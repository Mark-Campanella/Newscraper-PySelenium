from templates.json_to_csv import json_to_csv
from flask import Flask, render_template, request, send_file
from functions import go_into_website


#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#-------------------------------------------Backend for the user input-------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#

newscrapper = Flask(__name__)

@newscrapper.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        try:
            user_input = go_into_website(user_input)
            json_to_csv()  # Convert JSON to CSV
            return send_file('CSV/data.csv', as_attachment=True)
        except:
            return render_template('index.html', user_input ="Website was not found!")
    return render_template('index.html', user_input=None)
    

if __name__ == '__main__':
    newscrapper.run(debug=True)