import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from urllib3 import Retry


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

    return dataDF
