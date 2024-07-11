from flask import Flask, render_template, request, send_file, send_from_directory
import os
from functions import go_into_website, flush_data, dataframe_to_csv

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
            dataframe = go_into_website(urls)
        except:
            return render_template('index.html', user_input="Website was not found!")
        finally:
            try:
                dataframe_to_csv(dataframe)  # Convert dataframe to CSV
                return send_file('CSV/data.csv', as_attachment=True)
            except:
                return render_template('index.html', user_input="CSV not found!")

    return render_template('index.html', user_input="")
@newscrapper.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(newscrapper.root_path),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    newscrapper.run(debug=True)