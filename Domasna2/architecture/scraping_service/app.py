from flask import Flask, jsonify, request
from services.ticker_scraping import fetch_and_filter_tickers
from services.data_scraping import fetch_and_store_ticker_data, scrape_ticker
import requests

app = Flask(__name__)

STORAGE_SERVICE_URL = 'http://storage_service:5003/insert-data'

@app.route('/scrape-tickers', methods=['GET'])
def scrape_tickers():
    tickers = fetch_and_filter_tickers("https://www.mse.mk/en/stats/current-schedule")
    return jsonify({'tickers': tickers})

@app.route('/scrape-data', methods=['POST'])
def scrape_data():
    tickers = request.json.get('tickers')

    for ticker in tickers:
        base_url = "https://www.mse.mk/mk/stats/symbolhistory/ALK"
        headers = {"Content-Type": "application/json"}
        data = scrape_ticker(ticker, base_url, headers)
        data = fetch_and_store_ticker_data(data.start_date, ticker, base_url, headers)
        response = requests.post(STORAGE_SERVICE_URL, json={
            'ticker': ticker,
            'data': data
        })
        if response.status_code == 200:
            print(f"Data for {ticker} successfully sent to storage service.")
        else:
            print(f"Failed to send data for {ticker}. Status code: {response.status_code}")

        return jsonify({'message': 'Scraping complete!'})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
