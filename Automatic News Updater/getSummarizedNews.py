from flask import Flask, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests
import json
import torch
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
import time


DRIVER_PATH = # path to the selenium chrome driver
MODEL_PATH = # path to the Phi-3-mini-4k-instruct model
USERNAME = # username
PASSWORD = # password
URL = # url where the front end server is started

app = Flask(__name__)

def get_headline_id():
    url = "https://www.bbc.com/news"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    div_element = soup.find('div', {'data-testid': 'illinois-grid-10'})
    links = div_element.find_all('a', {'data-testid': 'internal-link'})
    href_list = [link.get('href') for link in links]
    return href_list

def get_news(link):
    webdriver_service = Service(DRIVER_PATH)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    url = f"https://www.bbc.com{link}"
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(url)

    try:
        image_block = driver.find_element(By.CSS_SELECTOR, 'section[data-component="image-block"]')
        hero_image = image_block.find_element(By.CSS_SELECTOR, 'div[data-testid="hero-image"] img')
        image_src = hero_image.get_attribute("src")
    except NoSuchElementException:
        print("Hero image not found")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        meta_image = soup.find('meta', property='og:image')
        image_src = meta_image['content'] if meta_image else None

    headline_elements = driver.find_elements(By.CSS_SELECTOR, '[data-component="headline-block"]')
    headline_texts = [headline.text for headline in headline_elements]
    headline_text = ' '.join(headline_texts)
    
    paragraphs = driver.find_elements(By.CSS_SELECTOR, '[data-component="text-block"]')
    paragraph_texts = []
    for paragraph in paragraphs:
        paragraph_texts.append(paragraph.text)
    full_paragraph = ' '.join(paragraph_texts)
    driver.quit()
    print("\nLink scraped successfully.\n")
    return {"image": image_src, "headline": headline_text, "paragraph": full_paragraph,"url": url }

def get_final_news(href_list):
    news = []
    for link in href_list:
        result = get_news(link)
        news.append(result)
    return news

def get_all_news():
    href_list = get_headline_id()
    return get_final_news(href_list)

config = BitsAndBytesConfig(
   load_in_4bit=True,
   bnb_4bit_quant_type="nf4",
   bnb_4bit_use_double_quant=True,
   bnb_4bit_compute_dtype=torch.bfloat16
)

torch.random.manual_seed(0)
model_path = MODEL_PATH
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    device_map="cuda", 
    torch_dtype="auto", 
    trust_remote_code=True, 
    quantization_config = config
)

tokenizer = AutoTokenizer.from_pretrained(model_path)

def summarize_input(prompt, model, tokenizer):
    messages = [
        {"role": "user", "content": f"""
        [INST]<>
          You are a summarizer tasked with creating concise, accurate summaries of user input. Your summaries should retain the original meaning and avoid including any false information. Ensure that you rely solely on the provided input, without using external knowledge. The final output should be a summarized text of less than 80 words.
        <>
        {prompt}
        [/INST]
      """},
    ]
    model_inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to("cuda")
    
    output = model.generate(model_inputs, max_new_tokens=500, do_sample=True)
    
    decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)
    
    end_index = decoded_output[0].find("[/INST]")
    summarized_text = decoded_output[0][end_index + len("[/INST]"):].strip()
    print("\nSummarized an article successfully.\n")
    return summarized_text

@app.route('/')
def update_news():
    start_time = time.time()
    summarized_news = []

    data = get_all_news()

    for item in data:
        prompt = item["paragraph"]
        url = item["url"]
        headline = item["headline"]
        summary = summarize_input(prompt, model, tokenizer)
        image = item["image"]
        news_item = {
            "url": url,
            "headline": headline,
            "summary": summary,
            "image": image
        }
        summarized_news.append(news_item)
    
    summarized_news_json = json.dumps(summarized_news)

    headers = {'Content-Type': 'application/json', 'username': USERNAME, 'password': PASSWORD}
    response = requests.post(f'{URL}/update_news', headers=headers, data=summarized_news_json)
    print(response)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    return jsonify({'message': 'News updated successfully'}), 200

if __name__ == "__main__":
    app.run(debug=False)