import mysql.connector
from mysql.connector import Error

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-db",
        user="root",
        password="Mihail123",
        database="MB_db"
    )

def insert_data_into_table(ticker, data):
    conn = None
    try:
        conn = mysql.connector.connect(
            host='mysql-db',
            user='root',
            password='Mihail123',
            database='MB_db'
        )
        if conn.is_connected():
            cursor = conn.cursor(dictionary=True)

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

            # Insert data with ticker name directly
            data_with_ticker = [(ticker, *row) for row in data]  # Use ticker name, not ticker_id

            cursor.executemany(insert_data_query, data_with_ticker)
            conn.commit()
    except Error as e:
        print(f"Error inserting data into tables for ticker {ticker}: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()




