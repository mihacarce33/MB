import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta


def fetch_and_filter_tickers(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    AllTickers = soup.select("#Code option")
    tickers = [option['value'] for option in AllTickers if not re.search(r'\d', option.text)]
    return tickers


def fetch_data_past_10_years(code):
    base_url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'  # Replace with the actual URL
    headers = {"Content-Type": "application/json"}  # Adjust headers as needed
    today = datetime.now()

    # Loop to make requests for the past 10 years
    # for ticker in tickers:
    dataDF = []
    for i in range(10):
        # Calculate the date range for the current year interval
        to_date = today - relativedelta(years=i)
        from_date = to_date + relativedelta(days=1) - relativedelta(years=1)

        # Format the dates to match the request format, e.g., "dd.mm.yyyy"
        to_date_str = to_date.strftime("%d.%m.%Y")
        from_date_str = from_date.strftime("%d.%m.%Y")

        # Define the request body
        data = {
            "FromDate": from_date_str,
            "ToDate": to_date_str,
            "Code": code
        }

        # Send the POST request
        response = requests.post(base_url, headers=headers, json=data)
        soup = BeautifulSoup(response.text, 'html.parser')
        resultsTableRows = soup.select("#resultsTable tr")
        for row in resultsTableRows:
            tds = row.find_all("td")
            if tds:
                row_data = {
                    "Датум": tds[0].text.strip() if tds[0] else None,
                    "Цена на последна трансакција": tds[1].text.strip() if tds[1] else None,
                    "Мак.": tds[2].text.strip() if tds[2] else None,
                    "Мин.": tds[3].text.strip() if tds[3] else None,
                    "Просечна цена": tds[4].text.strip() if tds[4] else None,
                    "%пром.": tds[5].text.strip() if tds[5] else None,
                    "Количина": tds[6].text.strip() if tds[6] else None,
                    "Промет во БЕСТ во денари": tds[7].text.strip() if tds[7] else None,
                    "Вкупен промет во денари": tds[8].text.strip() if tds[8] else None,
                }
                dataDF.append(row_data)
        df = pd.DataFrame(dataDF)
        df.to_csv(code + '.csv', index=False)
    # Check if the response is JSON
    # try:
    #     result_data = response.json()  # Attempt to parse JSON
    #     results.append(result_data)
    #     print(f"Data fetched for range {from_date_str} - {to_date_str}")
    # except requests.exceptions.JSONDecodeError:
    #     print(f"Non-JSON response for range {from_date_str} - {to_date_str}")
    #     # print("Response content:", response.text)  # Print the raw response for debugging

    return df

url = 'https://www.mse.mk/mk/stats/symbolhistory/ALK'
tickers = fetch_and_filter_tickers(url)
data = fetch_data_past_10_years("ALK")
# print(data)

