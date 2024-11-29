from flask import Flask, request, send_file, render_template, url_for
import os
from GameReport import GameReport  # Import the chart generation function

app = Flask(__name__)

# File path for the generated chart

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    username = request.form['username']
    global STATIC_DIR
    global CHART_FILENAME
    global CHART_FILEPATH
    STATIC_DIR = os.path.join(app.root_path, 'static')
    CHART_FILENAME = username+'.png'
    CHART_FILEPATH = os.path.join(STATIC_DIR, CHART_FILENAME)
    # Ensure the static directory exists
    os.makedirs(STATIC_DIR, exist_ok=True)

    # Generate the chart and save it to the static folder
    chart = GameReport(username)
    chart.getGameReport(CHART_FILEPATH)

    # Pass the graph URL to the template
    graph_url = url_for('static', filename=CHART_FILENAME)
    return render_template('index.html', graph_url=graph_url)

@app.route('/download')
def download():
    return send_file(CHART_FILEPATH, mimetype='image/png', as_attachment=True, download_name='chart.png')

if __name__ == '__main__':
    app.run(debug=True)
