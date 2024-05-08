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
        # Carregar cada objeto JSON individualmente
        data = [json.loads(line.strip()) for line in file if line.strip()]

    # Aglutinar os textos sob cada título
    aglutinado = aglutinar_textos(data)

    # Caminho do arquivo de saída
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_cleaned.json')

    # Salvar o resultado no mesmo diretório do arquivo original
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(aglutinado, output_file, ensure_ascii=False, indent=4)

    print("Resultado salvo em:", output_file_path)

# Função para limpar caracteres especiais
def limpar_texto(texto):
    '''
    Cleans the text! 
    
    Parameters:
        - str text
    '''
    return re.sub(r'[^\x00-\x7F]+', '', texto)

# Função para aglutinar textos sob cada título
def aglutinar_textos(data:list):
    '''
    Aglutinates a list of texts under theirs respective titles!
    
    Parameters:
        - List data
    '''
    aglutinado = []
    titulo_atual = None
    texto_aglutinado = ""

    for item in data:
        if "Titles" in item:
            # Se encontrarmos um novo título, adicionamos o título anterior e seu texto aglutinado à lista
            if titulo_atual is not None:
                aglutinado.append({"Titles": titulo_atual, "Text": texto_aglutinado.strip()})
                texto_aglutinado = ""

            # Atualizamos o título atual
            titulo_atual = limpar_texto(item["Titles"])
        elif "Text" in item:
            # Aglutinamos o texto sob o título atual
            texto_aglutinado += limpar_texto(item["Text"]) + "\n"

    # Adicionamos o último título e texto aglutinado à lista
    if titulo_atual is not None:
        aglutinado.append({"Titles": titulo_atual, "Text": texto_aglutinado.strip()})

    return aglutinado
            
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
    json_atualizado = []
    for item in json_data:
        if "Text" in item:
            texto_original = item["Text"]
            resumo = sum_text(texto_original)
            # Adicionando o resumo ao item do JSON sob o novo tópico "Scoop"
            item["Scoop"] = resumo
        json_atualizado.append(item)
    return json_atualizado

def wait_until_page_loads(driver:webdriver, timeout=30):
    """
    Awaits page to load dynamically

    Parâmetros:
        - driver: Selenium's driver object
        - timeout: in seconds, if none is given =  30
    """
    start_time = time.time()  # Tempo de início da execução
    while True:
        end_time = time.time()  # Tempo de fim da execução
        # Condição para sair do loop: quando o tempo de espera excede o tempo limite ou todos os elementos são carregados
        if (end_time - start_time) > timeout or driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(1)  # Espera 1 segundo antes de verificar novamente

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


            


