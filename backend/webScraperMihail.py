import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import time
import os

start_time = time.time()

def fetch_and_filter_tickers(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    AllTickers = soup.select("#Code option")
    tickers = [option['value'] for option in AllTickers if not re.search(r'\d', option.text)]
    return tickers


def fetch_data_and_store_csv(tickers):
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'  # Replace with the actual URL
    headers = {"Content-Type": "application/json"}  # Adjust headers as needed

    for ticker in tickers:
        # Check if a CSV file for the ticker already exists
        file_path = f"{ticker}.csv"
        if os.path.exists(file_path):
            # Read the existing CSV file to get the latest date
            df_existing = pd.read_csv(file_path)
            most_recent_date = df_existing["Датум"].max()
            start_date = datetime.strptime(most_recent_date, "%d.%m.%Y") + relativedelta(days=1)
        else:
            # If no CSV file exists, fetch data for the last 10 years
            start_date = datetime.now() - relativedelta(years=10)

        today = datetime.now()
        dataDF = []

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

            # Send the POST request
            response = requests.post(base_url, headers=headers, json=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            resultsTableRows = soup.select("#resultsTable tr")

            for row in resultsTableRows:
                tds = row.find_all("td")
                if tds:
                    # # Skip rows with any `null` values
                    # if any(td.text.strip() == '' for td in tds):
                    #     continue

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

                    # Check for '0' or 'null' values and skip the row if any are found
                    if any(value == '0' or value is None for value in row_data.values()):
                        continue  # Skip this row if it contains 0 or None

                    dataDF.append(row_data)

            # Move the start date forward by one year
            start_date += relativedelta(years=1)

        print(ticker + ' is scraped.')
        # Convert the collected data to a DataFrame and append to the existing CSV file
        df_new_data = pd.DataFrame(dataDF)
        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path)
            df_combined = pd.concat([df_existing, df_new_data]).drop_duplicates(subset=["Датум"])
            df_combined.to_csv(file_path, index=False)
        else:
            df_new_data.to_csv(file_path, index=False)

url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
tickers = fetch_and_filter_tickers(url)
fetch_data_and_store_csv(tickers)

end_time = time.time()
elapsed_time = end_time - start_time #6min 50sec (6:50)
print(f"Script finished in {elapsed_time:.2f} seconds.")
# print(data)
