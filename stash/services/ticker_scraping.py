import re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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
