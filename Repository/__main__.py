from templates.json_to_csv import json_to_csv
from flask import Flask, render_template, request, send_file
from functions import go_into_website, flush_data
import os



#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#-------------------------------------------Backend for the user input-------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#

newscrapper = Flask(__name__)

@newscrapper.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('flush_data_button'): 
            result = flush_data() #Delete data from csv and jsons
            return render_template('index.html', user_input=result)

        user_input = request.form['user_input']
        # Converts to a list of urls
        urls = user_input.split(',')  # URLs should be separated by commas!!
        try:
            go_into_website(urls)
            json_to_csv()  # Convert JSON to CSV
            return send_file('CSV/data.csv', as_attachment=True)
        except:
            return render_template('index.html', user_input="Website was not found!")
    return render_template('index.html', user_input=None)

if __name__ == '__main__':
    newscrapper.run(debug=True)