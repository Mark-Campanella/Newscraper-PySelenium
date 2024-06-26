import csv
import json
import os
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from textsum.summarize import Summarizer
import time



#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------File Manipulation: json later csv--------------------------------------------#
#---------------------------------Related to: Title, Text, Scoop, URL, Brand, Country----------------------------------#
#----------------------------------Still to go: Key Items, Image Links, Month, Year------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#

#TODO Gather img src and Key Items in the text, gather Year/Month from datetime
#Deletes everything for a new session usage
def flush_data():
    '''
    Deletes the data from all files
    Returns whether the data was flushed or not 
    '''
    try:
        with open('JSON/file_cleaned.json', 'w', encoding='utf-8') as json_file:
            json_file.write('')
            
        with open('JSON/pre_file.json', 'w', encoding='utf-8') as json_file:
            json_file.write('')
        
        with open('CSV/data.csv', 'w', encoding='utf-8') as csv_file:
            csv_file.write('')
        return "Data flushed successfully!"
    except Exception as e:
        return f"Error flushing data: {e}"
#Saves each item in the pre-file to be organized later
def save(item_name, items):
    '''
        Save desired items in a csv to be added in the repository
        
        Parameters:
            -item_name: type of the object added, e.g.: URL, Title, Text, Scoop, etc.
            -itens: object to be added 'str'
    '''
    df = pd.DataFrame({f'{item_name}': items})
    df.to_json('JSON/pre_file.json', orient='records', lines=True, mode='a', index=False)
#Takes the raw pre-file and transforms it in a useful and organized file    
def rework_json_file():
    '''
    Rework the pre_file so it is closer to being correct, saves another file, it does not overwrite pre_file, but overwrite itself!
    '''
    with open('JSON/pre_file.json', 'r', encoding='utf-8') as file:
        # loads each JSON individually
        data = [json.loads(line.strip()) for line in file if line.strip()]

    # Aglutinates text under their title
    aglutinated_text = aglutinate_text_to_title(data)
            
    # Where I keep the aglutinated text
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'JSON/file_cleaned.json')

    # Save the result where I want
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(aglutinated_text, output_file, ensure_ascii=False, indent=4)
    # Not relevant for final user
    print("Archive saved in:", output_file_path)
#Removes unvalid chars and things like that
def clean_text(text):
    '''
    Cleans the text (special chars etc.)! 
    
    Parameters:
        - str text
    '''
    return re.sub(r'[^\x00-\x7F]+', '', text)
#This is what gather multiple titles and text togheter in one dict structure, or json object structure which are both compatibles
#I prefer to work with json and separated files, notwithstanding, I understand it might be smarter to just hold in a dict and only later put it in a file
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
#Adds year and month of the article, considering that they are new!
def add_year_month():
    '''
    It is considered that every news that we are scraping are new, so we get current month and year
    '''
    today = time.asctime(time.localtime())#gets current time tuple and convert to a string format date
    year = today[len(today)-4:len(today)]#gets the year 
    month = today[4:7]#gets the month
    json_file = 'JSON/file_cleaned.json'
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    
    # Iterate through each item in JSON data
    for item in json_data:
        try:
            item["Year"] = year #Add year
            item["Month"] = month #Add month
        except: continue
        
    # Write updated JSON data back to file
    with open(json_file, 'w') as outfile:
        json.dump(json_data, outfile, indent=4)
    
    print("Year and Month added.")        
#This function uses a library (textsum) to summarize the texts, it is avaible in GitHub, really useful and easy to use library! 
def sum_text(text:str):
    '''
    This sum up the texts!
    
    Parameters:
    
        - str Text
    '''
    sum = Summarizer()
    scoop = sum.summarize_string(text)
    return scoop
#Adds the summarized text to the json file for each object
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
#Function was a basic solution for adding URL to the file without having to change it or do something more elaborate, not ideal perhaps, but works
def add_urls(urls:list):
    '''
    Adds the urls to the json objects, after everything is already there in the object
    
    Parameters:
        -list urls
    '''
    with open('JSON/file_cleaned.json', 'r') as arquivo:
        dados_json = json.load(arquivo)
    
    # If there is the same amout of itens and urls
    if len(urls) <= len(dados_json):
        for i, item in enumerate(urls):
            dados_json[i]["Link"] = item
    
        with open('JSON/file_cleaned.json', 'w') as arquivo:
            json.dump(dados_json, arquivo, indent=4)
        print("urls adicionadas.")
    else:
        print("There are more itens than urls, check your files to understand it better")
#Function tries to add a country and a brand in the csv      
def try_find_country_brand():
    '''
    Looks if the country, region, or continent is mentioned (checked if it is in a lookup table)
    Looks if a company is mentioned
    If they are mentioned (anyone) it is added to the json
    '''
    
    lookup_csv = 'CSV/lookup.csv'
    json_file = 'JSON/file_cleaned.json'

    try:
        # Load lookup table
        df = pd.read_csv(lookup_csv)
        
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        # Iterate through each item in JSON data
        for item in json_data:
            title = str(item.get("Titles", ""))  # Get the title from JSON item
            text = str(item.get("Text", ""))    # Get the text from JSON item
            try:
                # Look for country mentions
                country_found = False
                for country in df["Country"]:
                    if country in text:
                        item["Country"] = country
                        country_found = True
                        break  # Stop searching for country once found
                if not country_found: item["Country"] = ""
            except: continue
            try:
                # Look for brand mentions in title
                for brand in df["Brand"]:
                    if brand in title:
                        item["Brand"] = brand
                        break  # Stop searching for brand once found 
                    
                # If brand is not found in title, look in text
                if not item.get("Brand"):
                    for brand in df["Brand"]:
                        if brand in text:
                            item["Brand"] = brand
                            break  # Stop searching for brand once found
                    if not item.get("Brand"): item["Brand"] = ""     
            except: continue
                
        # Write updated JSON data back to file
        with open(json_file, 'w') as outfile:
            json.dump(json_data, outfile, indent=4)
        
        print("Brand and/or country added.")
        
    except Exception as e:
        print("An error occurred:", e)
#Dynamic loading of webpages
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
#Function that calls other functions, first one and last one to execute
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
            
            #Problem with image: Multiple unrelated images from different pages, how to identify which I want?
            #Idea 1: What if I searched the brand's name in the img src link? if contains, it gets, if not, it skips
                #Problem: at first it doesn't have the brand name, to reaccess the websites would be required (not scalable nor efficient)
            # elem = driver.find_element(By.TAG_NAME,"img")
            # img = elem.get_attribute('src')
            
            
            print(f"\n-----------------------------------\nWebsite info for {url} got copied!\n-------------------------------------------")
        except Exception as e:
            print(f"ERROR!: {e}")
        finally:
            try:
                driver.quit()
                rework_json_file()  # Calling rework_json_file() to clean and save a better version of the pre-file
            except Exception as e:
                print(f"Data was not cleaned for {url}: {e}")
    try:
        json_data = json.load(open('JSON/file_cleaned.json', 'r', encoding='utf-8'))  #Loads the new file cleaned up
        json_data_with_scoop = add_scoop(json_data)  # Adds the summary
        with open('JSON/file_cleaned.json', 'w', encoding='utf-8') as output_file:
            json.dump(json_data_with_scoop, output_file, ensure_ascii=False, indent=4)  # Saves the summary          
        add_urls(urls)  # Adding URLs to each object after everything is done to the files
        try_find_country_brand()
        add_year_month()
    except FileNotFoundError:
        print("File not found.")
    except json.JSONDecodeError:
        print("Invalid JSON format.")
    except Exception as e:
        print(f"An error occurred: {e}")
#Last thing called, as I am currently sustaining a Sheets with the infos I want, this one helps to import things there (sep = ";")
def json_to_csv():
    """
    Convert JSON data to CSV format with a specific separator.
    """
    json_file = 'JSON/file_cleaned.json'
    csv_file = 'CSV/data.csv'

    # Check if the JSON file exists
    if not os.path.exists(json_file):
        print("JSON file does not exist.")
        return

    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Write JSON data to CSV file with a specific separator
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Write header
        writer.writerow(['Year','Month','Brand','Country','Link','Titles','Scoop','Text'])

        # Write rows
        for row in json_data:
            writer.writerow([row.get('Year', '').replace(';', ','),row.get('Month', '').replace(';', ','),row.get('Brand', '').replace(';', ','), row.get('Country', '').replace(';', ','), row.get('Link', '').replace(';', ','), row.get('Titles', '').replace(';', ','), row.get('Scoop', '').replace(';', ','), row.get('Text', '').replace(';', ',')])

    print(f"CSV file '{csv_file}' has been created.")                    
