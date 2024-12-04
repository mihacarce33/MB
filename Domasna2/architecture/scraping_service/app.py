from os import cpu_count

from flask import Flask, jsonify, request
from joblib import Parallel, delayed

from services.ticker_scraping import fetch_and_filter_tickers
from services.data_scraping import fetch_and_store_ticker_data, scrape_ticker
import requests

app = Flask(__name__)

STORAGE_SERVICE_URL = 'http://storage_service:5003/insert-data'


@app.route('/scrape-data', methods=['POST'])
def scrape_data():
    tickers = fetch_and_filter_tickers("https://www.mse.mk/en/stats/current-schedule")

    base_url = "https://www.mse.mk/mk/stats/symbolhistory/ALK"
    headers = {"Content-Type": "application/json"}

    Parallel(n_jobs=cpu_count())(delayed(scrape_ticker)(ticker, base_url, headers) for ticker in tickers)
    return jsonify({'message': 'Scraping complete!'})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
