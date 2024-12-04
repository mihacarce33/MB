from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    # Call scraping service to trigger scraping
    requests.post('http://scraping-service:5001/scrape-data')
    return jsonify({'message': 'Scraping complete!'})

@app.route('/ticker/<ticker>')
def get_ticker_data(ticker):
    # Call the storage service to get data for the specific ticker
    response = requests.get(f'127.0.0.1:5003/ticker-data/{ticker}')
    data = response.json().get('data')
    return render_template('ticker.html', ticker=ticker, data=data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
