from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    # Call scraping service to trigger scraping
    requests.post('http://scraping_service:5001/scrape-data', json={'tickers': ['ticker1', 'ticker2']})
    return jsonify({'message': 'Scraping complete!'})

@app.route('/ticker/<ticker>')
def get_ticker_data(ticker):
    # Call the storage service to get data for the specific ticker
    response = requests.get(f'http://storage_service:5003/ticker-data/{ticker}')
    data = response.json().get('data')
    return render_template('ticker.html', ticker=ticker, data=data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
