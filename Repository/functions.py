import json
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time
from textsum.summarize import Summarizer


#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------File Manipulation: json later csv--------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#

def flush_data():
    '''
    Resets Data
    returns if the data was or not flushed
    '''
    try:
        with open('Repository/file_cleaned.json', 'w', encoding='utf-8') as json_file:
            json_file.write('')
            
        with open('Repository/pre_file.json', 'w', encoding='utf-8') as json_file:
            json_file.write('')
        
        with open('Repository/CSV/data.csv', 'w', encoding='utf-8') as csv_file:
            csv_file.write('')
        return "Data flushed successfully!"
    except Exception as e:
        return f"Error flushing data: {e}"

def save(item_name, items):
    '''
        Save desired items in a csv to be added in the repository
        
        Parameters:
            -item_name: type of the object added, e.g.: URL, Title, Text, Scoop, etc.
            -itens: object to be added 'str'
    '''
    df = pd.DataFrame({f'{item_name}': items})
    df.to_json('Repository/pre_file.json', orient='records', lines=True, mode='a', index=False)
    
def rework_json_file():
    '''
    Rework the pre_file so it is closer to being correct, saves another file, it does not overwrite pre_file, but overwrite itself!
    '''
    with open('Repository/pre_file.json', 'r', encoding='utf-8') as file:
        # loads each JSON individually
        data = [json.loads(line.strip()) for line in file if line.strip()]

    # Aglutinates text under their title
    aglutinated_text = aglutinate_text_to_title(data)
            
    # Where I keep the aglutinated text
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_cleaned.json')

    # Save the result where I want
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(aglutinated_text, output_file, ensure_ascii=False, indent=4)
    # Not relevant for final user
    print("Archive saved in:", output_file_path)

def clean_text(text):
    '''
    Cleans the text (special chars etc.)! 
    
    Parameters:
        - str text
    '''
    return re.sub(r'[^\x00-\x7F]+', '', text)

def aglutinate_text_to_title(data:list):
    '''
    Aglutinates a list of texts under theirs respective titles!
    
    Parameters:
        - List data
    '''
    aglutinated_text = []
    current_title = None
    aglutinated_text_aux = ""

    for item in data:
        if "Titles" in item:
            if current_title is not None:
                aglutinated_text.append({"Titles": current_title, "Text": aglutinated_text_aux.strip()})
                aglutinated_text_aux = ""
            current_title = clean_text(item["Titles"])
        elif "Text" in item:
            aglutinated_text_aux += clean_text(item["Text"]) + "\n"

    if current_title is not None:
        aglutinated_text.append({"Titles": current_title, "Text": aglutinated_text_aux.strip()})

    return aglutinated_text

def sum_text(text:str):
    '''
    This sum up the texts!
    
    Parameters:
    
        - str Text
    '''
    sum = Summarizer()
    scoop = sum.summarize_string(text)
    return scoop
    
def add_scoop(json_data):
    json_updated = []
    for item in json_data:
        if "Text" in item and "Scoop" not in item:
            original_text = item["Text"]
            summarized_text = sum_text(original_text)
            # Add the scoop (sum) to the JSON in the new topic "Scoop"
            item["Scoop"] = summarized_text
        json_updated.append(item)
    return json_updated

def add_urls(urls:list):
    '''
    Adds the urls to the json objects, after everything is already there in the object
    
    Parameters:
        -list urls
    '''
    with open('Repository/file_cleaned.json', 'r') as arquivo:
        dados_json = json.load(arquivo)
    
    # Verifica se o comprimento da lista é menor ou igual ao número de objetos no arquivo JSON
    if len(urls) <= len(dados_json):
        for i, item in enumerate(urls):
            dados_json[i]["Link"] = item
    
        with open('Repository/file_cleaned.json', 'w') as arquivo:
            json.dump(dados_json, arquivo, indent=4)
        print("urls adicionadas.")
    else:
        print("A lista é maior do que o número de objetos no arquivo JSON.")

def wait_until_page_loads(driver:webdriver, timeout=30):
    """
    Awaits page to load dynamically

    Parâmetros:
        - driver: Selenium's driver object
        - int timeout: in seconds, if none is given =  30
    """
    start_time = time.time()  # When it Begins
    while True:
        end_time = time.time()  # When it ends
        # If timeout happens or the object html loads, it gets out of the loop
        if (end_time - start_time) > timeout or driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(3)  # Before trying again it waits

def go_into_website(urls: list):
    '''
    Uses Selenium to get into each webpage in the list of URLs provided by the user
    Gather the title (h1) and the texts (p) from each webpage and close the navigator
    It calls rework_json_file() to clean up the 'pre-file' to the 'file_cleaned'

    Parameters:
    list urls: list of URLs of the news websites
    '''
    for url in urls:
        # Validating the URL
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError(f"Invalid URL: {url}")
        driver = webdriver.Chrome()
        titles = []
        text = []
        try:
            driver.get(url)
            wait_until_page_loads(driver)
            
            elem = driver.find_elements(By.TAG_NAME, 'h1')
            [titles.append(every.text) for every in elem]
            save("Titles", titles)
            
            elem = driver.find_elements(By.TAG_NAME, 'p')
            [text.append(every.text) for every in elem]      
            save("Text", text)
            
            print(f"\n-----------------------------------\nWebsite info for {url} got copied!\n-------------------------------------------")
        except Exception as e:
            print(f"ERROR!: {e}")
        finally:
            try:
                driver.quit()
                rework_json_file()  # Calling rework_json_file() to clean and save a better version of the pre-file
                json_data = json.load(open('Repository/file_cleaned.json', 'r', encoding='utf-8'))  #Loads the new file cleaned up
                json_data_with_scoop = add_scoop(json_data)  # Adds the summary
                with open('Repository/file_cleaned.json', 'w', encoding='utf-8') as output_file:
                    json.dump(json_data_with_scoop, output_file, ensure_ascii=False, indent=4)  # Saves the summary
            except Exception as e:
                print(f"Data was not cleaned for {url}: {e}")
    try:           
        add_urls(urls)  # Adding URLs to each object after everything is done to the files
    except FileNotFoundError:
        print("File not found.")
    except json.JSONDecodeError:
        print("Invalid JSON format.")
    except Exception as e:
        print(f"An error occurred: {e}")
                    