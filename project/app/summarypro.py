import torch
import transformers
from transformers import PegasusForConditionalGeneration, PegasusTokenizer, PegasusConfig
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config
from transformers import BartTokenizer, BartForConditionalGeneration, BartConfig
import nltk
import bs4 as bs  # beautifulsource4
import urllib.request
import re
import logging

log = logging.getLogger(__name__)
torch_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class SummarizerProcessor:
    def __init__(self, model: str = None):
        log.info(model)
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

    def nest_sentences(self, document):
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

    def preprocess(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0'}
        opener = urllib.request.URLopener()
        opener.addheader('User-Agent', 'Mozilla/5.0')

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        scraped_data = urllib.request.urlopen(req, timeout=20)

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

    def generate_summary(self, nested_sentences):
        # logger.info("Inside inference before generate summary")
        # logger.info(self.model.get_input_embeddings())
        summaries = []
        for nested in nested_sentences:
            input_tokenized = self.tokenizer.encode(' '.join(nested), truncation=True, return_tensors='pt')
            input_tokenized = input_tokenized.to(self.device)
            summary_ids = self.model.to(self.device).generate(input_tokenized,
                                                              length_penalty=3.0)
            output = [self.tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in
                      summary_ids]
            summaries.append(output)

        # logger.info("Inside inference after generate summary")

        summaries = [sentence for sublist in summaries for sentence in sublist]
        return summaries

    def inference(self, input_url: str):
        """
        Method to perform the inference
        :param input_url: Input url for the inference

        :return: correct category and confidence for that category
        """
        log.info(input_url)
        self.text = self.preprocess(input_url)
        if self.modelName == "google/pegasus-newsroom":
            batch = self.tokenizer(self.text, truncation=True, padding='longest', return_tensors="pt").to(torch_device)
            translated = self.model.generate(**batch)
            tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
            log.info(tgt_text)
        elif self.modelName == "facebook/bart-large-cnn":
            nested = self.nest_sentences(self.text)
            summarized_text = self.generate_summary(nested)
            nested_summ = self.nest_sentences(' '.join(summarized_text))
            tgt_text = self.generate_summary(nested_summ)
        return tgt_text
