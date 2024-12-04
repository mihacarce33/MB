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
import mysql.connector
from mysql.connector import Error

start_time = time.time()


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="finki123",
        database="MB_db"
    )


def get_last_date_for_ticker(ticker):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT MAX(date) 
        FROM ticker_data
        JOIN Tickers ON ticker_data.ticker = Tickers.id
        WHERE Tickers.ticker = %s;
        """
        cursor.execute(query, (ticker,))
        result = cursor.fetchone()

        return result[0]
    except Error as e:
        print(f"Error fetching last date for {ticker}: {e}, Or there is no data for ticker {ticker}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def insert_data_into_table(ticker, data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_ticker_query = """
        INSERT INTO Tickers (ticker)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE ticker = VALUES(ticker);
        """
        cursor.execute(insert_ticker_query, (ticker,))
        conn.commit()

        insert_data_query = """
                INSERT INTO ticker_data (ticker, date, last_transaction_price, max_price, min_price,
                                         average_price, percent_change, quantity, best_turnover, total_turnover)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                last_transaction_price = VALUES(last_transaction_price),
                max_price = VALUES(max_price),
                min_price = VALUES(min_price),
                average_price = VALUES(average_price),
                percent_change = VALUES(percent_change),
                quantity = VALUES(quantity),
                best_turnover = VALUES(best_turnover),
                total_turnover = VALUES(total_turnover);
                """

        data_with_ticker = [(ticker, *row) for row in data]

        cursor.executemany(insert_data_query, data_with_ticker)
        conn.commit()

    except Error as e:
        print(f"Error inserting data into tables for ticker {ticker}: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def fetch_and_filter_tickers(url):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    continuousTable = soup.select_one('#continuousTradingMode-table tbody')
    auctionTable = soup.select_one('#fixingWith20PercentLimit-table tbody')
    auctionWithoutPriceLimitTable = soup.select_one('#fixingWithoutLimit-table tbody')
    symbol_texts1 = [a.text for a in continuousTable.select('a')]
    symbol_texts2 = [a.text for a in auctionTable.select('a')]
    symbol_texts3 = [a.text for a in auctionWithoutPriceLimitTable.select('a')]
    symbol_texts = symbol_texts1 + symbol_texts2 + symbol_texts3
    tickers = [s for s in symbol_texts if not re.search(r'\d', s)]
    return tickers


def fetch_and_store_ticker_data(start_date, ticker, base_url, headers):
    dataDF = []
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    today = datetime.now()

    while start_date < today:
        to_date = today if start_date.year == today.year else start_date + relativedelta(years=1) - relativedelta(
            days=1)
        from_date_str = start_date.strftime("%d.%m.%Y")
        to_date_str = to_date.strftime("%d.%m.%Y")

        data = {"FromDate": from_date_str, "ToDate": to_date_str, "Code": ticker}
        try:
            response = session.post(base_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {ticker}: {e}")
            break

        soup = BeautifulSoup(response.text, 'lxml')
        resultsTableRows = soup.select("#resultsTable tr")

        for row in resultsTableRows:
            tds = row.find_all("td")
            if tds and all(tds[i].text.strip() != "" for i in range(len(tds))):
                dataDF.append((
                    datetime.strptime(tds[0].text.strip(), "%d.%m.%Y"),
                    float(tds[1].text.strip().replace('.', '').replace(',', '.')),
                    float(tds[2].text.strip().replace('.', '').replace(',', '.')),
                    float(tds[3].text.strip().replace('.', '').replace(',', '.')),
                    float(tds[4].text.strip().replace('.', '').replace(',', '.')),
                    float(tds[5].text.strip().replace('.', '').replace(',', '.')),
                    int(tds[6].text.strip().replace('.', '')),
                    float(tds[7].text.strip().replace('.', '').replace(',', '.')),
                    float(tds[8].text.strip().replace('.', '').replace(',', '.'))
                ))

        start_date += relativedelta(years=1)

    insert_data_into_table(ticker, dataDF)
    print(f"{ticker} data stored successfully.")


def scrape_ticker(ticker, base_url, headers):
    last_date = get_last_date_for_ticker(ticker)
    start_date = (last_date + relativedelta(days=1)) if last_date else datetime.now() - relativedelta(years=10)
    fetch_and_store_ticker_data(start_date, ticker, base_url, headers)


def main():
    url = 'https://www.mse.mk/en/stats/current-schedule'
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
    headers = {"Content-Type": "application/json"}

    tickers = fetch_and_filter_tickers(url)
    Parallel(n_jobs=cpu_count())(delayed(scrape_ticker)(ticker, base_url, headers) for ticker in tickers)


if __name__ == "__main__":
    main()
