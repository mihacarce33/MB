import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from joblib import Parallel, delayed
from multiprocessing import cpu_count

start_time = time.time()

def fetch_and_filter_tickers(url):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    AllTickers = soup.select("#Code option")
    tickers = [option['value'] for option in AllTickers if not re.search(r'\d', option.text)]
    return tickers


def check_if_data_exists(ticker, base_url, headers):
    file_path = f"{ticker}.csv"

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            df_existing = pd.read_csv(file_path)
            if df_existing.empty:
                start_date = datetime.now() - relativedelta(years=10)
                fetch_and_store_ticker_data(start_date, ticker, base_url, headers, file_path)
            df_existing["Датум"] = pd.to_datetime(df_existing["Датум"], format="%d.%m.%Y")
            today = datetime.now()
            nearest_date = df_existing.loc[(df_existing["Датум"] - today).abs().idxmin(), "Датум"]
            start_date = datetime.strptime(nearest_date.strftime("%d.%m.%Y"), "%d.%m.%Y") + relativedelta(days=1)
            fetch_and_store_ticker_data(start_date, ticker, base_url, headers, file_path)
        except (pd.errors.EmptyDataError, KeyError) as e:
            start_date = datetime.now() - relativedelta(years=10)
            fetch_and_store_ticker_data(start_date, ticker, base_url, headers, file_path)
    else:
        start_date = datetime.now() - relativedelta(years=10)
        fetch_and_store_ticker_data(start_date, ticker, base_url, headers, file_path)


def fetch_and_store_ticker_data(start_date, ticker, base_url, headers, file_path):
    dataDF = []

    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    today = datetime.now()

    while start_date < today:
        if start_date.year == today.year:
            to_date = today
        else:
            to_date = start_date + relativedelta(years=1) - relativedelta(days=1)

        from_date_str = start_date.strftime("%d.%m.%Y")
        to_date_str = to_date.strftime("%d.%m.%Y")

        data = {
            "FromDate": from_date_str,
            "ToDate": to_date_str,
            "Code": ticker
        }

        try:
            response = session.post(base_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed for ticker {ticker}: {e}")
            time.sleep(1)
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        resultsTableRows = soup.select("#resultsTable tr")

        for row in resultsTableRows:
            tds = row.find_all("td")
            if tds and all(tds[i].text.strip() != "" for i in range(len(tds))):
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

        start_date += relativedelta(years=1)

    if dataDF:
        new_df = pd.DataFrame(dataDF)

        if os.path.exists(file_path):
            try:
                df_existing = pd.read_csv(file_path)
                if not df_existing.empty:
                    df_combined = pd.concat([df_existing, new_df]).drop_duplicates(subset=["Датум"])
                    df_combined.to_csv(file_path, index=False)
                else:
                    new_df.to_csv(file_path, index=False)
            except pd.errors.EmptyDataError:
                new_df.to_csv(file_path, index=False)
        else:
            new_df.to_csv(file_path, index=False)

    print(f"{ticker} is scraped.")


def main():
    url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
    headers = {"Content-Type": "application/json"}

    tickers = fetch_and_filter_tickers(url)
    Parallel(n_jobs=cpu_count())(delayed(check_if_data_exists)(ticker, base_url, headers) for ticker in tickers)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Script finished in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    main()
