from ticker_scraping import fetch_and_filter_tickers
from data_scraping import fetch_and_store_ticker_data
from storing_data import get_last_date_for_ticker, insert_data_into_table
from joblib import Parallel, delayed
from multiprocessing import cpu_count
from datetime import datetime
from dateutil.relativedelta import relativedelta

def scrape_ticker(ticker, base_url, headers):
    last_date = get_last_date_for_ticker(ticker)
    start_date = (last_date + relativedelta(days=1)) if last_date else datetime.now() - relativedelta(years=10)
    data = fetch_and_store_ticker_data(start_date, ticker, base_url, headers)
    insert_data_into_table(ticker, data)
    print(f"{ticker} data stored successfully.")

def main():
    url = 'https://www.mse.mk/en/stats/current-schedule'
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
    headers = {"Content-Type": "application/json"}

    tickers = fetch_and_filter_tickers(url)
    Parallel(n_jobs=cpu_count())(delayed(scrape_ticker)(ticker, base_url, headers) for ticker in tickers)

if __name__ == "__main__":
    main()
