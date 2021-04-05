import torch
import transformers
from transformers import PegasusForConditionalGeneration, PegasusTokenizer, PegasusConfig
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config
from transformers import BartTokenizer, BartForConditionalGeneration, BartConfig
import json
import bs4 as bs  # beautifulsource4
import urllib.request
import re
import logging

log = logging.getLogger(__name__)
torch_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class SummarizerProcessor:
    def __init__(self, model: str = None, service: str = "summ"):
        if model is None:
            model = "t5"

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
        if model == "google/pegasus-newsroom":
            self.config = PegasusConfig.from_json_file(self.config_path)
            # self.model = PegasusForConditionalGeneration(self.config)
            # self.tokenizer = PegasusTokenizer.from_pretrained(self.path)
            self.model = PegasusForConditionalGeneration.from_pretrained(model).to(torch_device)
            self.tokenizer = PegasusTokenizer.from_pretrained(model)
        if model == "facebook/bart-large-cnn":
            self.config = BartConfig.from_json_file(self.config_path)
            # self.model = PegasusForConditionalGeneration(self.config)
            # self.tokenizer = PegasusTokenizer.from_pretrained(self.path)
            self.model = BartForConditionalGeneration.from_pretrained(model).to(torch_device)
            self.tokenizer = BartTokenizer.from_pretrained(model)
        else:
            raise Exception("This model is not supported")

        self.text = str()

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
        return self.text

    def inference(self, input_url: str):
        """
        Method to perform the inference
        :param input_url: Input url for the inference

        :return: correct category and confidence for that category
        """
        log.info(input_url)
        self.text = self.preprocess(input_url)
        log.info(self.text)
        batch = self.tokenizer(self.text, truncation=True, padding='longest', return_tensors="pt").to(torch_device)
        translated = self.model.generate(**batch)
        tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)

        return tgt_text
