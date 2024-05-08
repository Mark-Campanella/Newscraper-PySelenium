import json
import csv
import os

def json_to_csv():
    """
    Convert JSON data to CSV format with a specific separator.
    """
    json_file = 'Repository/file_cleaned.json'
    csv_file = 'Repository/CSV/data.csv'

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
        writer.writerow(['Titles', 'Text', 'Scoop'])

        # Write rows
        for row in json_data:
            writer.writerow([row.get('Titles', '').replace(';', ','), row.get('Text', '').replace(';', ','), row.get('Scoop', '').replace(';', ',')])

    print(f"CSV file '{csv_file}' has been created.")

if __name__ == '__main__':
    json_to_csv()