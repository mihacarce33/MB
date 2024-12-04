from flask import Flask, render_template, jsonify
import requests
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scrape', methods=['POST'])
def scrape():
    requests.post('http://scraping-service:5001/scrape-data')
    return jsonify({'message': 'Scraping complete!'})


@app.route('/ticker/<ticker>')
def get_ticker_data(ticker):
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

            ticker_query = """
            SELECT * FROM Tickers WHERE ticker = %s;
            """
            cursor.execute(ticker_query, (ticker,))
            ticker_obj = cursor.fetchone()

            if not ticker_obj:
                return jsonify({'error': 'Ticker not found'}), 404

            data_query = """
            SELECT date, last_transaction_price, max_price, min_price, average_price, 
                   percent_change, quantity, best_turnover, total_turnover
            FROM ticker_data WHERE ticker = %s;
            """
            cursor.execute(data_query, (ticker,))
            data = cursor.fetchall()

            return render_template('ticker.html', ticker=ticker, data=data)

    except Error as e:
        return jsonify({'error': f"Error fetching data for ticker {ticker}: {e}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
