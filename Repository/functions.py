import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from textsum.summarize import Summarizer
import time
import os

#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#--------------------------------------File Manipulation: dataframe later csv------------------------------------------#
#---------------------------------Related to: Title, Text, Scoop, URL, Brand, Country----------------------------------#
#----------------------------------Still to go: Key Items, Image Links-------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
path_to_csv_data = 'CSV/data.csv'
path_to_csv_lookup = 'CSV/lookup.csv'
#TODO Gather img src and Key Items in the text, correct Year/Month format
#Deletes everything for a new session usage
def flush_data():
    """
    Deletes the data from all files
    Returns whether the data was flushed or not 
    """
    try:
        open(path_to_csv_data, 'w', encoding='utf-8').close()
        return "Data flushed successfully!"
    except Exception as e:
        return f"Error flushing data: {e}"

def save_to_dataframe(dataframe, item_name, items):
    """
    Save desired items to the dataframe to be added in the repository
    
    Parameters:
        - dataframe: pandas DataFrame to append data
        - item_name: type of the object added, e.g.: URL, Title, Text, Scoop, etc.
        - items: object to be added 'str'
    """
    temp_df = pd.DataFrame({f'{item_name}': items})
    return pd.concat([dataframe, temp_df], ignore_index=True)

def aglutinate_text_to_title(data):
    """
    Aglutinates a list of texts under theirs respective titles!
    
    Parameters:
        - DataFrame data
    """
    aglutinated_text = []
    current_title = None
    aglutinated_text_aux = ""

    # Ensure all values are strings
    data = data.fillna("").astype(str)

    for _, item in data.iterrows():
        if "Titles" in item and item["Titles"]:
            if current_title is not None:
                aglutinated_text.append({"Titles": current_title, "Text": aglutinated_text_aux.strip()})
                aglutinated_text_aux = ""
            current_title = clean_text(item["Titles"])
        elif "Text" in item and item["Text"]:
            aglutinated_text_aux += clean_text(item["Text"]) + "\n"

    if current_title is not None:
        aglutinated_text.append({"Titles": current_title, "Text": aglutinated_text_aux.strip()})

    return pd.DataFrame(aglutinated_text)

def clean_text(text):
    """
    Cleans the text (special chars etc.)! 
    
    Parameters:
        - str text
    """
    return re.sub(r'[^\x00-\x7F]+', '', text)

def add_year_month(dataframe):
    """
    It is considered that every news that we are scraping are new, so we get current month and year
    Repo is in sheets and month was being added manually with the structure of mm/dd/yy with day always 01,
    I am just adding the day of scraping because it is irrelevant to change and add codelines here
    
    Parameters:
        - dataframe: pd.DataFrame
    """
    try:
        today = time.localtime()
        year = today.tm_year
        month = time.strftime('%m/%d/%Y', today)
        
        dataframe['Year'] = year
        dataframe['Month'] = month
    except:
        dataframe['Year'] = ''
        dataframe['Month'] = ''
    finally:
        return dataframe

def sum_text(text):
        """
        This sum up the texts!

        Parameters:
            - text: str
        """
        try:
            sum = Summarizer()
            return sum.summarize_string(text)
        except:
            return ""
def add_scoop(dataframe):
    '''
    Adds a Scoop in the text. I'm using a downloaded Learned Machine from the Textsum library.
    It is not ideal, it is massive, slow, etc. But it is easy to implement and time/storage is not a problem in my case.
    '''
        
    dataframe['Scoop'] = dataframe['Text'].apply(lambda x: sum_text(x) if pd.notnull(x) else "")
    return dataframe

def add_urls(dataframe, urls):
    """
    Adds the urls to the dataframe
    
    Parameters:
        - dataframe: pandas DataFrame to add URLs
        - list urls: list of URLs
    """
    if len(urls) > len(dataframe): print("\n\n-------An error has occurred scrapping one or more of the links given,"+
                                         " check the 'Links' field for mistakes before adding to the repository!----------\n\n")
    dataframe['Link'] = urls[:len(dataframe)]
    return dataframe

def try_find_country_brand(dataframe, lookup_csv=path_to_csv_lookup):
    """
    Looks if any word in the title or text matches a country or brand in the lookup table.
    Adds the country or brand to the dataframe if found.
    
    Parameters:
        - dataframe: pandas DataFrame containing the text data.
        - lookup_csv: path to the CSV file containing the lookup data.
    """
    #tries to find the lookup file
    if not os.path.exists(lookup_csv):
        print(f"Lookup file {lookup_csv} not found.")
        return dataframe
    
    #tries to read the lookup, if it is empty → nothing to see, break; if it doesn't have the columns needed → insuficient data to work, break
    try:
        df_lookup = pd.read_csv(lookup_csv)
        if df_lookup.empty:
            print(f"Lookup file {lookup_csv} is empty.")
            return dataframe
        # Check if necessary columns are present
        if 'Country' not in df_lookup.columns or 'Brand' not in df_lookup.columns:
            print(f"Lookup file {lookup_csv} does not contain 'Country' or 'Brand' columns.")
            return dataframe

        def find_country(text):
            '''
            Find a country in the text:\n
                \t - if there is no text: break\n
                \t - for each word in the text: try to see if word is str\n
                \t - if the word is in country: return country, else return None\n
            Parameters:
                - text: str
            '''
            if pd.isna(text):
                return ""
            words = text.split()
            for word in words:
                if isinstance(word, str):
                    for country in df_lookup['Country']:
                        if isinstance(country, str) and word.lower() == country.lower():
                            return country
            return ""
        
        def find_brand(text):
            '''
            Find a brand in the text:\n
                \t - if there is no text: break\n
                \t - for each word in the text: try to see if word is str\n
                \t - if the word is in brand: return brand, else return None\n
            Parameters:
                - text: str
            '''
            if pd.isna(text):
                return ""
            words = text.split()
            for word in words:
                if isinstance(word, str):
                    for brand in df_lookup['Brand']:
                        if word.lower() == brand.lower():
                            return brand
            return ""
        #Here it will apply the methods to find Country and Brand, first it will try to look in the title, then in the text
        try:
            dataframe['Country'] = dataframe['Titles'].apply(lambda x: find_country(x) if pd.notnull(x) else "")
            dataframe['Country'] = dataframe.apply(lambda row: find_country(row['Text']) if row['Country'] == "" else row['Country'], axis=1)
        except Exception as e:
            print("Not able to add Country, error: ", e)

        try:
            dataframe['Brand'] = dataframe['Titles'].apply(lambda x: find_brand(x) if pd.notnull(x) else "")
            dataframe['Brand'] = dataframe.apply(lambda row: find_brand(row['Text']) if row['Brand'] == "" else row['Brand'], axis=1)
        except Exception as e:
            print("Not able to add Brand, error: ", e)
        
        return dataframe
    except pd.errors.EmptyDataError as e:
        print("No columns to parse from file: ",e)
        return dataframe
    except Exception as e:
        print(f"An error occurred: {e}")
        return dataframe

def wait_until_page_loads(driver, timeout=30):
    """
    Awaits page to load dynamically

    Parameters:
        - driver: Selenium's driver object
        - int timeout: in seconds, if none is given =  30
    """
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout or driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(3)

def go_into_website(urls):
    """
    Uses Selenium to get into each webpage in the list of URLs provided by the user
    Gather the title (h1), the texts (p), and image links from each webpage and close the navigator

    Parameters:
        list urls: list of URLs of the news websites
    """
    driver = webdriver.Chrome()
    dataframe = pd.DataFrame()
    # image_links = []

    try:
        for url in urls:
            try:
                if not url.startswith("http://") and not url.startswith("https://"):
                    raise ValueError(f"Invalid URL: {url}")

                driver.get(url)
                wait_until_page_loads(driver)
                
                try:
                    titles = [clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'h1')]
                    if titles == None:
                        h1_elements = driver.find_elements(By.TAG_NAME, 'h1')
                        for h1 in h1_elements:
                            span_elements = h1.find_elements(By.TAG_NAME, 'span')
                            for span in span_elements:
                                titles.append(clean_text(span.text))
                except:
                    try:
                        titles = [clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'h2')]
                    except:
                        if titles == "":
                            h2_elements = driver.find_elements(By.TAG_NAME, 'h2')
                            for h2 in h2_elements:
                                span_elements = h2.find_elements(By.TAG_NAME, 'span')
                                for span in span_elements:
                                    titles.append(clean_text(span.text))

                
                try:
                    try: texts = [clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'p')]
                    except: pass
                    try: texts.append([clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'h3')])
                    except: pass
                    try: texts.append([clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'h4')])
                    except: pass                     
                    try: texts.append([clean_text(every.text) for every in driver.find_elements(By.TAG_NAME, 'li')])
                    except: pass
                except:
                    try: texts = [clean_text(every.text) for every in (driver.find_elements(By.TAG_NAME, 'span'))]
                    except Exception as e: print("\n\n No text found :( : ", e) 
                
                # images = driver.find_elements(By.TAG_NAME, 'img')
                # title_keywords = set(re.findall(r'\w+', ' '.join(titles).lower()))
                # image_link = next((img.get_attribute('src') for img in images if any(keyword in img.get_attribute('src').lower() for keyword in title_keywords)), "")
                # image_links.append(image_link if image_link else "")

                dataframe = save_to_dataframe(dataframe, "Titles", titles)
                dataframe = save_to_dataframe(dataframe, "Text", texts)
                
                print(f"\n-----------------------------------\nWebsite info for {url} got copied!\n-------------------------------------------")
            except Exception as e:
                print(f"ERROR!: {e}")
    finally:
        driver.quit()

    try:
        dataframe = aglutinate_text_to_title(dataframe)
        dataframe = add_scoop(dataframe)
        dataframe = add_urls(dataframe, urls)
        # dataframe['ImageLink'] = image_links
        dataframe = try_find_country_brand(dataframe)
        dataframe = add_year_month(dataframe)
    except Exception as e:
        print("Something went wrong: ", e)

    return dataframe

def dataframe_to_csv(dataframe):
    """
    Convert DataFrame data to CSV format with a specific separator (';').
    """
    try:
        csv_file = path_to_csv_data
    except Exception as e: print("Unable to find the file, error: ", e)
    header = ["Year", "Month", "Corporate", "Brand", "Att 1", "Att 2", "Product", "Region", "Country", 
              "Link", "Titles", "Scoop", "Article photo", "Text", "Type of News"]
    # Add missing columns with empty values
    for col in header:
        if col not in dataframe.columns:
            dataframe[col] = ""
    try:
        dataframe.to_csv(csv_file, sep=';', index=False, columns=header)
        print(f"CSV file '{csv_file}' has been created.")
    except Exception as e: print("Could not create the CSV file, error: ", e)
