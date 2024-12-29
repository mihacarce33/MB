from textwrap import wrap
from mysql.connector import Error
import mysql.connector
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.trend import MACD, CCIIndicator
from ta.volatility import BollingerBands
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from keras.api.models import Sequential
from keras.api.layers import Input, LSTM, Dense
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from transformers import pipeline, AutoTokenizer
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='mysql-db',
            user='root',
            password='Mihail123',
            database='MB_db'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_stock_data(ticker):
    try:
        conn = get_db_connection()
        query = f"SELECT date, last_transaction_price, max_price, min_price, total_turnover FROM ticker_data WHERE ticker = '{ticker}' ORDER BY date ASC;"
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'last_transaction_price': 'close'}, inplace=True)
        df.rename(columns={'max_price': 'high'}, inplace=True)
        df.rename(columns={'min_price': 'low'}, inplace=True)
        return df
    except Error as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def calculate_indicators(df):
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['WMA_50'] = df['close'].rolling(window=50).apply(lambda x: np.dot(x, range(1, 51)) / sum(range(1, 51)), raw=True)
    bollinger = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_upper'] = bollinger.bollinger_hband()
    df['BB_lower'] = bollinger.bollinger_lband()

    df['RSI'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['Stochastic'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14).stoch()
    macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['CCI'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close'], window=20).cci()
    df['WilliamsR'] = WilliamsRIndicator(high=df['high'], low=df['low'], close=df['close'], lbp=14).williams_r()

    return df

def generate_signals(df):
    df['Signal'] = 'Hold'
    df.loc[df['RSI'] < 30, 'Signal'] = 'Buy'
    df.loc[df['RSI'] > 70, 'Signal'] = 'Sell'
    df.loc[(df['close'] < df['BB_lower']), 'Signal'] = 'Buy'
    df.loc[(df['close'] > df['BB_upper']), 'Signal'] = 'Sell'
    df['Crossover'] = np.where(df['SMA_50'] > df['EMA_20'], 'Buy', 'Sell')
    return df

def analyze_trends(df):
    timeframes = {'1D': 1, '1W': 5, '1M': 20}
    analysis_results = {}
    for name, period in timeframes.items():
        df_period = df.tail(period)
        analysis_results[name] = {
            'Mean RSI': float(df_period['RSI'].mean()),
            'Mean Stochastic': float(df_period['Stochastic'].mean()),
            'Mean CCI': float(df_period['CCI'].mean()),
            'Buy Signals': int((df_period['Signal'] == 'Buy').sum()),
            'Sell Signals': int((df_period['Signal'] == 'Sell').sum()),
        }
    return analysis_results

def load_data(ticker):
    try:
        conn = get_db_connection()
        query = f"SELECT date, last_transaction_price FROM ticker_data WHERE ticker = '{ticker}' ORDER BY date ASC;"
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'last_transaction_price': 'close'}, inplace=True)
        df.sort_index(inplace=True)
        return df

    except Error as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def create_lags(df):
    lag = 3
    periods = range(lag, 0, -1)
    df.shift(periods=periods)
    df = pd.concat([df, df.shift(periods=periods)], axis=1)
    df.dropna(axis=0, inplace=True)
    return df

def train_and_validate(df):
    X, y = df.drop(columns=["close"]), df["close"]
    train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=0.3, shuffle=False)
    scaler = MinMaxScaler()
    train_X = scaler.fit_transform(train_X)
    test_X = scaler.transform(test_X)
    lag = 3
    train_X = train_X.reshape(train_X.shape[0], lag, (train_X.shape[1] // lag))
    test_X = test_X.reshape(test_X.shape[0], lag, (test_X.shape[1] // lag))
    model = Sequential([
        Input((train_X.shape[1], train_X.shape[2],)),
        LSTM(64, activation="relu", return_sequences=True),
        LSTM(32, activation="relu"),
        Dense(1, activation="linear")
    ])
    return model, train_X, test_X, train_y, test_y

def predict(model, train_X, test_X, train_y, test_y):
    model.compile(
        loss="mean_squared_error",
        optimizer="adam",
        metrics=["mean_squared_error"],
    )
    model.fit(train_X, train_y, validation_split=0.2, epochs=64, batch_size=8)
    pred_y = model.predict(test_X)
    return pred_y, test_y

def retrieve_and_analyze_sentiment(ticker):
    url = f"https://mse.mk/en/symbol/{ticker}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('.nav-link')
    link = [link['href'] for link in links if link.has_attr('href') and 'https' in link['href']]
    if len(link) == 1:
        link = link[0]
    parts = link.split('/')
    issuerId = int(parts[-1])

    today = datetime.now()
    one_year_ago = today - relativedelta(years=1)
    today = today.strftime('%Y-%m-%dT%H:%M:%S')
    last_year = one_year_ago.strftime('%Y-%m-%dT%H:%M:%S')
    news = []


    for i in range(1, 100):
        json = {
            "issuerId": issuerId,
            "languageId": 2,
            "channelId": 1,
            "dateFrom": last_year,
            "dateTo": today,
            "page": i,
            "isPushRequest": 0
        }
        headers = {
            "Content-Type": "application/json"
        }

        url = 'https://api.seinet.com.mk/public/documents'
        response = requests.post(url, headers=headers, json=json)
        resJSON = response.json()
        data = resJSON['data']
        if not data:
            break
        for i in range(0, len(data)):
            text = data[i]['content']
            if not text:
                if 'attachments' in data[i] and len(data[i]['attachments']) > 0 and 'fileName' in data[i]['attachments'][0]:
                    text = data[i]['attachments'][0]['fileName'].split('.')[0]
            if "automaticaly generated" in text or "automatically generated" in text:
                continue

            soup = BeautifulSoup(text, 'html.parser')
            plain_text = soup.get_text().strip()
            news.append(plain_text)


    classifier = pipeline(
        "sentiment-analysis",
        model="yiyanghkust/finbert-tone",
        truncation=True,
    )

    def analyze_sentiment(news_text):
        max_token_length = 512
        chunks = wrap(news_text, max_token_length * 2)
        sentiment_results = []
        for chunk in chunks:
            sentiment_result = classifier(chunk[:max_token_length])[0]
            sentiment = sentiment_result['label']
            confidence = sentiment_result['score']

            sentiment_results.append({
                "sentiment": sentiment,
                "confidence": confidence
            })


        positive = sum(1 for result in sentiment_results if result['sentiment'] == 'Positive')
        negative = sum(1 for result in sentiment_results if result['sentiment'] == 'NEGATIVE')

        if positive > negative:
            action = "Buy stocks"
            final_sentiment = "Positive"
        elif negative > positive:
            action = "Sell stocks"
            final_sentiment = "Negative"
        else:
            action = "Hold stocks"
            final_sentiment = "Neutral"

        return {
            "news": news_text[:200] + ("..." if len(news_text) > 200 else ""),
            "sentiment": final_sentiment,
            "confidence": max(result['confidence'] for result in sentiment_results),
            "recommendation": action
        }


    with ThreadPoolExecutor(max_workers=4) as executor:
        analysis_results = list(executor.map(analyze_sentiment, news))

    return analysis_results