import csv
import json
import os
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from textsum.summarize import Summarizer
import time

def flush_data():
    '''
    Deletes the data from all files
    Returns whether the data was flushed or not 
    '''
    try:
        with open('JSON/data.json', 'w', encoding='utf-8') as json_file:
            json_file.write('')
        
        with open('CSV/data.csv', 'w', encoding='utf-8') as csv_file:
            csv_file.write('')
        return "Data flushed successfully!"
    except Exception as e:
        return f"Error flushing data: {e}"

def save_to_pre_file(pre_file, item_name, items):
    '''
    Save desired items to the pre_file dictionary
        
    Parameters:
        - pre_file: dictionary to store data temporarily
        - item_name: type of the object added, e.g.: URL, Title, Text, Scoop, etc.
        - items: list of objects to be added
    '''
    if item_name not in pre_file:
        pre_file[item_name] = []
    pre_file[item_name].extend(items)

def rework_data(pre_file):
    '''
    Rework the pre_file data so it is organized into a list of dictionaries
    '''
    data = []
    titles = pre_file.get("Titles", [])
    texts = pre_file.get("Text", [])
    
    for title, text in zip(titles, texts):
        data.append({"Titles": clean_text(title), "Text": clean_text(text)})

    return data

def clean_text(text):
    '''
    Cleans the text (special chars etc.)! 
    
    Parameters:
        - str text
    '''
    return re.sub(r'[^\x00-\x7F]+', '', text)

def add_year_month(data):
    '''
    It is considered that every news that we are scraping are new, so we get current month and year
    '''
    today = time.asctime(time.localtime())
    year = today[-4:]
    month = today[4:7]
    
    for item in data:
        item["Year"] = year
        item["Month"] = month
    
    print("Year and Month added.")        
    return data

def sum_text(text):
    '''
    This sum up the texts!
    
    Parameters:
    
        - str Text
    '''
    sum = Summarizer()
    scoop = sum.summarize_string(text)
    return scoop

def add_scoop(data):
    for item in data:
        if "Text" in item and "Scoop" not in item:
            original_text = item["Text"]
            summarized_text = sum_text(original_text)
            item["Scoop"] = summarized_text
    return data

def add_urls(data, urls):
    '''
    Adds the urls to the json objects, after everything is already there in the object
    
    Parameters:
        - list data: list of data dictionaries
        - list urls: list of URLs
    '''
    for i, item in enumerate(data):
        if i < len(urls):
            item["Link"] = urls[i]
    
    print("URLs added.")
    return data

def try_find_country_brand(data):
    '''
    Looks if the country, region, or continent is mentioned (checked if it is in a lookup table)
    Looks if a company is mentioned
    If they are mentioned (anyone) it is added to the json
    '''
    lookup_csv = 'CSV/lookup.csv'

    try:
        df = pd.read_csv(lookup_csv)
        
        for item in data:
            title = item.get("Titles", "")
            text = item.get("Text", "")
            try:
                country_found = False
                for country in df["Country"]:
                    if country in text:
                        item["Country"] = country
                        country_found = True
                        break
                if not country_found: item["Country"] = ""
            except: continue
            try:
                for brand in df["Brand"]:
                    if brand in title or brand in text:
                        item["Brand"] = brand
                        break
                if not item.get("Brand"): item["Brand"] = ""
            except: continue
                
        print("Brand and/or country added.")
    except Exception as e:
        print("An error occurred:", e)
    return data

def wait_until_page_loads(driver, timeout=30):
    """
    Awaits page to load dynamically

    Parameters:
        - driver: Selenium's driver object
        - int timeout: in seconds, if none is given =  30
    """
    start_time = time.time()
    while True:
        end_time = time.time()
        if (end_time - start_time) > timeout or driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(3)

def go_into_website(urls):
    '''
    Uses Selenium to get into each webpage in the list of URLs provided by the user
    Gather the title (h1) and the texts (p) from each webpage and close the navigator
    It calls rework_data() to clean up the pre_file and save the final data
    
    Parameters:
    list urls: list of URLs of the news websites
    '''
    pre_file = {}
    for url in urls:
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError(f"Invalid URL: {url}")
        driver = webdriver.Chrome()
        titles = []
        text = []
        try:
            driver.get(url)
            wait_until_page_loads(driver)
            
            elems = driver.find_elements(By.TAG_NAME, 'h1')
            titles = [elem.text for elem in elems]
            save_to_pre_file(pre_file, "Titles", titles)
            
            elems = driver.find_elements(By.TAG_NAME, 'p')
            text = [elem.text for elem in elems]      
            save_to_pre_file(pre_file, "Text", text)
            
            print(f"\n-----------------------------------\nWebsite info for {url} got copied!\n-------------------------------------------")
        except Exception as e:
            print(f"ERROR!: {e}")
        finally:
            driver.quit()
    
    try:
        data = rework_data(pre_file)
        data = add_scoop(data)
        data = add_urls(data, urls)
        data = try_find_country_brand(data)
        data = add_year_month(data)
        
        with open('JSON/data.json', 'w', encoding='utf-8') as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"An error occurred: {e}")

def json_to_csv():
    """
    Convert JSON data to CSV format with a specific separator.
    """
    json_file = 'JSON/data.json'
    csv_file = 'CSV/data.csv'

    if not os.path.exists(json_file):
        print("JSON file does not exist.")
        return

    with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        header = ["Year", "Month", "Brand", "Country", 
                  "Link", "Titles", "Scoop", "Text"]
        writer.writerow(header)

        for row in json_data:
            writer.writerow([row.get(col, '').replace(';', ',') for col in header])

    print(f"CSV file '{csv_file}' has been created.")
