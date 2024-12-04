import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import mysql.connector
from mysql.connector import Error


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="finki123",
        database="MB_db"
    )


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
                    datetime.strptime(tds[0].text.strip(), "%d.%m.%Y").strftime("%Y-%m-%d"),
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

    return dataDF


def get_last_date_for_ticker(ticker):
    conn = None
    try:
        conn = mysql.connector.connect(
            host='mysql-db',
            user='root',
            password='finki123',
            database='MB_db'
        )
        if conn.is_connected():
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT MAX(date) 
            FROM ticker_data
            JOIN Tickers ON ticker_data.ticker = Tickers.id
            WHERE Tickers.ticker = %s;
            """
            cursor.execute(query, (ticker,))
            result = cursor.fetchone()

            if result['MAX(date)'] is None:
                return None
            return result['MAX(date)']
    except Error as e:
        print(f"Error fetching last date for {ticker}: {e}, Or there is no data for ticker {ticker}", flush=True)
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def scrape_ticker(ticker, base_url, headers):
    last_date = get_last_date_for_ticker(ticker)
    start_date = (last_date + relativedelta(days=1)) if last_date else datetime.now() - relativedelta(years=10)
    dataTicker = fetch_and_store_ticker_data(start_date, ticker, base_url, headers)
    response = requests.post("http://storage-service:5003/insert-data", json={
        'ticker': ticker,
        'data': dataTicker
    })
    if response.status_code == 200:
        print(f"Data for {ticker} successfully sent to storage service.", flush=True)
    else:
        print(f"Failed to send data for {ticker}. Status code: {response.status_code}", flush=True)
