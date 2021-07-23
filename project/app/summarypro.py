import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer, PegasusConfig
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config
from transformers import BartTokenizer, BartForConditionalGeneration, BartConfig
import nltk
import sys

import bs4 as bs  # beautifulsource4
from urllib.request import Request, urlopen
import re
import logging

nltk.download('punkt')
log = logging.getLogger(__name__)

PERCENTAGE = {"short": 10,
              "medium": 20,
              "long": 30
              }


def percentage(percent, whole):
    return (percent * whole) / 100.0


def number_of_words(article_text):
    # log.info(article_text)
    word_count = len(article_text.split(" "))
    return word_count


def summary_length(number, count):
    return round(percentage(number, count))


def nest_sentences(document):
    nested = []
    sent = []
    length = 0
    for sentence in nltk.sent_tokenize(document):
        length += len(sentence)
        if length < 1024:
            sent.append(sentence)
        else:
            nested.append(sent)
            sent = [sentence]
            length = len(sentence)

    if sent:
        nested.append(sent)

    return nested


def preprocess(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    scraped_data = urlopen(req, timeout=200)

    article = scraped_data.read()

    parsed_article = bs.BeautifulSoup(article, 'lxml')
    parsed_article = bs.BeautifulSoup(article, 'lxml')

    paragraphs = parsed_article.find_all('p')

    article_text = ""

    for p in paragraphs:
        article_text += ' ' + p.text
    formatted_article_text = re.sub(r'\n|\r', ' ', article_text)
    formatted_article_text = re.sub(r' +', ' ', formatted_article_text)
    formatted_article_text = formatted_article_text.strip()

    return formatted_article_text


class SummarizerProcessor:
    def __init__(self, model: str = None):
        log.info(model)
        torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        log.info(torch_device)
        if model is None:
            model = "t5"
        self.modelName = model
        # path to all the files that will be used for inference
        self.path = f"./app/api/{model}/"
        self.model_path = self.path + "pytorch_model.bin"
        self.config_path = self.path + "config.json"

        # Selecting the correct model based on the passed madel input. Default t5
        if model == "t5":
            self.config = T5Config.from_json_file(self.config_path)
            self.model = T5ForConditionalGeneration(self.config)
            self.tokenizer = T5Tokenizer.from_pretrained(self.path)
            self.model.eval()
            self.model.load_state_dict(torch.load(self.model_path, map_location=torch_device))
        elif model == "google/pegasus-newsroom":
            self.config = PegasusConfig.from_json_file(self.config_path)
            # self.model = PegasusForConditionalGeneration(self.config)
            # self.tokenizer = PegasusTokenizer.from_pretrained(self.path)
            self.model = PegasusForConditionalGeneration.from_pretrained(model).to(torch_device)
            self.tokenizer = PegasusTokenizer.from_pretrained(model)
        elif model == "facebook/bart-large-cnn":
            self.config = BartConfig.from_json_file(self.config_path)
            # self.model = PegasusForConditionalGeneration(self.config)
            # self.tokenizer = PegasusTokenizer.from_pretrained(self.path)
            self.model = BartForConditionalGeneration.from_pretrained(model).to(torch_device)
            self.tokenizer = BartTokenizer.from_pretrained(model)
        else:
            raise Exception("This model is not supported")

        self.text = str()

    def generate_summary(self, nested_sentences, max_length):
        # logger.info("Inside inference before generate summary")
        # logger.info(self.model.get_input_embeddings())
        summaries = []
        for nested in nested_sentences:
            input_tokenized = self.tokenizer.encode(' '.join(nested), truncation=True, return_tensors='pt')
            input_tokenized = input_tokenized.to(torch_device)
            summary_ids = self.model.to(torch_device).generate(input_tokenized,
                                                               length_penalty=3.0,
                                                               max_length=max_length)
            output = [self.tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in
                      summary_ids]
            summaries.append(output)

        # logger.info("Inside inference after generate summary")

        summaries = [sentence for sublist in summaries for sentence in sublist]
        return summaries

    def generate_simple_summary(self, text):
        # logger.info("Inside inference before generate summary")
        # logger.info(self.model.get_input_embeddings())
        inputs = self.tokenizer([text], max_length=1024, return_tensors='pt')

        # Generate Summary
        summary_ids = self.model.generate(inputs['input_ids'], num_beams=4, max_length=5, early_stopping=True)
        # print([tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in summary_ids])
        # input_tokenized = self.tokenizer.encode(text, truncation=True, return_tensors='pt')
        # input_tokenized = input_tokenized.to(torch_device)
        # summary_ids = self.model.to(torch_device).generate(input_tokenized)
        output = [self.tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in
                  summary_ids]

        return output

    async def inference(self, input_url: str, length: str):
        """
        Method to perform the inference
        :param length:
        :param input_url: Input url for the inference

        :return: correct category and confidence for that category
        """
        # log.info(input_url)

        self.text = preprocess(input_url)
        # log.info(self.text)
        # word_count = number_of_words(self.text)
        length_of_summary = PERCENTAGE[length]
        # min_length = summary_length(word_count, min_length_percentage)
        max_length = 1000
        if self.modelName == "google/pegasus-newsroom":
            batch = self.tokenizer(self.text, truncation=True, padding='longest', return_tensors="pt").to(torch_device)
            translated = self.model.generate(**batch)
            tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
            # log.info(tgt_text)
        elif self.modelName == "facebook/bart-large-cnn":
            nested = nest_sentences(self.text)
            summarized_text = self.generate_summary(nested, max_length)
            list_length = len(summarized_text)
            number_items = summary_length(list_length, length_of_summary)

            # nested_summ = nest_sentences(' '.join(summarized_text))
            # tgt_text_list = self.generate_summary(nested_summ,  max_length)
            index = 0
            tgt_text = ""
            while index < number_items:
                tgt_text += summarized_text[index]
                index += 1
            # tgt_text = self.generate_simple_summary(self.text)
        return tgt_text
