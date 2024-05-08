import pandas as pd
import json

def json_to_csv():
    # Carregar o arquivo JSON
    with open('Repository/file_cleaned.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Criar um DataFrame vazio
    df = pd.DataFrame()

    # Iterar sobre os itens do JSON
    for item in json_data:
        # Adicionar cada item ao DataFrame
        df = df._append(item, ignore_index=True)

    # Salvar o DataFrame como CSV
    #TODO sep='' create a sep for csv and add it in the end of each part (text, title, summary, etc.)
    df.to_csv('Repository/CSV/file_cleaned.csv', index=False, )

    print("Arquivo CSV criado com sucesso!")
