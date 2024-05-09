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
def save(item_name, items):
    '''
        Save desired items in a csv to be added in the repository
        
        Parameters:
            -item_name: type of the object added, e.g.: Title, Text, Scoop, etc.
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
    algutinated_text = aglutinate_text_to_title(data)

    # Where I keep the aglutinated text
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_cleaned.json')

    # Save the result where I want
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(algutinated_text, output_file, ensure_ascii=False, indent=4)
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
    algutinated_text = []
    current_title = None
    algutinated_text_aux = ""

    for item in data:
        if "Titles" in item:
            # If there is a new title we add the other title to it and add the text aglutinated
            if current_title is not None:
                algutinated_text.append({"Titles": current_title, "Text": algutinated_text_aux.strip()})
                algutinated_text_aux = ""

            # Add the other title
            current_title = clean_text(item["Titles"])
        elif "Text" in item:
            # Add the text
            algutinated_text_aux += clean_text(item["Text"]) + "\n"

    # We add the result to a list of aglutinated texts
    if current_title is not None:
        algutinated_text.append({"Titles": current_title, "Text": algutinated_text_aux.strip()})

    return algutinated_text
            
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
        if "Text" in item:
            original_text = item["Text"]
            summarized_text = sum_text(original_text)
            # Add the scoop (sum) to the JSON in the new topic "Scoop"
            item["Scoop"] = summarized_text
        json_updated.append(item)
    return json_updated

def wait_until_page_loads(driver:webdriver, timeout=30):
    """
    Awaits page to load dynamically

    Parâmetros:
        - driver: Selenium's driver object
        - timeout: in seconds, if none is given =  30
    """
    start_time = time.time()  # When it Begins
    while True:
        end_time = time.time()  # When it ends
        # If timeout happens or the object html loads, it gets out of the loop
        if (end_time - start_time) > timeout or driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(3)  # Before trying again it waits

def go_into_website(url: str):
    '''
    Uses Selenium to get into the webpage the user typed in the input (url)
    Gather the title (h1) and the texts (p) from the webpage and closes the navigator
    It calls rework_json_file() to clean up the 'pre-file' to the 'file_cleaned'

    Parameters:
    str url = text of the link of the news website
    '''
    # Validating the URL
    if not url.startswith("http://") and not url.startswith("https://"):
        raise Exception("Unvalid url")

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
        
        return "Website info got copied!"
    except Exception as e:
        return f"ERROR!: {e}"
    finally:
        try:
            driver.quit()
            rework_json_file()  # Chamando a função rework_json_file() para limpar e salvar o arquivo JSON
            json_data = json.load(open('Repository/file_cleaned.json', 'r', encoding='utf-8'))  # Carregando o arquivo limpo
            json_data_with_scoop = add_scoop(json_data)  # Adicionando resumos
            with open('Repository/file_cleaned.json', 'w', encoding='utf-8') as output_file:
                json.dump(json_data_with_scoop, output_file, ensure_ascii=False, indent=4)  # Salvando o arquivo com os resumos
        except:
            driver.quit()
            return "Data was not cleaned!"