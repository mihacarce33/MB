import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
import csv

# Setup for caching requests to avoid redundant HTTP calls during repeated scrapes
requests_cache.install_cache('my_cache')

# Setup retry mechanism for failed requests
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

start_time = time.time()


def fetch_and_filter_tickers(url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')  # Use lxml parser for faster parsing
    AllTickers = soup.select("#Code option")
    tickers = [option['value'] for option in AllTickers if not re.search(r'\d', option.text)]
    return tickers


def fetch_and_store_ticker_data(ticker, base_url, headers):
    # Check if a CSV file for the ticker already exists
    file_path = f"{ticker}.csv"
    dataDF = []

    if os.path.exists(file_path):
        # Read the existing CSV file to get the latest date
        df_existing = pd.read_csv(file_path)
        most_recent_date = df_existing["Датум"].max()
        start_date = datetime.strptime(most_recent_date, "%d.%m.%Y") + relativedelta(days=1)
    else:
        # If no CSV file exists, fetch data for the last 10 years
        start_date = datetime.now() - relativedelta(years=10)

    today = datetime.now()

    while start_date < today:
        to_date = start_date + relativedelta(years=1) - relativedelta(days=1)
        if to_date > today:
            to_date = today

        # Format the dates for the request
        from_date_str = start_date.strftime("%d.%m.%Y")
        to_date_str = to_date.strftime("%d.%m.%Y")

        data = {
            "FromDate": from_date_str,
            "ToDate": to_date_str,
            "Code": ticker
        }

        response = session.post(base_url, headers=headers, json=data)
        soup = BeautifulSoup(response.text, 'lxml')  # Use lxml parser for faster parsing
        resultsTableRows = soup.select("#resultsTable tr")

        # Process the rows from the response
        for row in resultsTableRows:
            tds = row.find_all("td")
            if tds and all(tds[i].text.strip() != "" for i in range(len(tds))):  # Ensure non-empty cells
                row_data = {
                    "Датум": tds[0].text.strip(),
                    "Цена на последна трансакција": tds[1].text.strip(),
                    "Мак.": tds[2].text.strip(),
                    "Мин.": tds[3].text.strip(),
                    "Просечна цена": tds[4].text.strip(),
                    "%пром.": tds[5].text.strip(),
                    "Количина": tds[6].text.strip(),
                    "Промет во БЕСТ во денари": tds[7].text.strip(),
                    "Вкупен промет во денари": tds[8].text.strip(),
                }
                dataDF.append(row_data)

        # Move the start date forward by one year
        start_date += relativedelta(years=1)

    # Write the scraped data to CSV
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path)
        df_combined = pd.concat([df_existing, pd.DataFrame(dataDF)]).drop_duplicates(subset=["Датум"])
        df_combined.to_csv(file_path, index=False)
    else:
        pd.DataFrame(dataDF).to_csv(file_path, index=False)

    print(f"{ticker} is scraped.")


def main():
    url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'  # Update with actual URL
    headers = {"Content-Type": "application/json"}  # Adjust headers as needed

    # Fetch the tickers
    tickers = fetch_and_filter_tickers(url)

    # Use ThreadPoolExecutor to fetch data for multiple tickers concurrently
    with ThreadPoolExecutor() as executor:
        executor.map(lambda ticker: fetch_and_store_ticker_data(ticker, base_url, headers), tickers)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Script finished in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    main()
