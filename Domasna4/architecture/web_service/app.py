from flask import Flask, render_template, jsonify, request, send_file
import requests
from mysql.connector import Error
from services.webService import get_db_connection, get_stock_data, calculate_indicators, generate_signals, \
    analyze_trends, load_data, create_lags, train_and_validate, predict, retrieve_and_analyze_sentiment
import matplotlib.pyplot as plt
import io
from sklearn.metrics import r2_score

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/a1')
def a1():
    return render_template('technical_analysis.html')

@app.route('/a2')
def a2():
    return render_template('fundamental_analysis.html')

@app.route('/a3')
def a3():
    return render_template('LSTM_predictions.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    requests.post('http://scraping-service:5001/scrape-data')
    return jsonify({'message': 'Scraping complete!'})


@app.route('/ticker/<ticker>')
def get_ticker_data(ticker):
    conn = None
    try:
        conn = get_db_connection()
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

@app.route('/stock_data', methods=['GET'])
def stock_data():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    df = get_stock_data(ticker)

    if df.empty:
        return jsonify({"error": f"No data found for ticker: {ticker}"}), 404

    stock_data = df[['close', 'high', 'low', 'total_turnover']].to_dict(orient='records')
    return jsonify(stock_data), 200


@app.route('/indicators', methods=['GET'])
def indicators():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    df = get_stock_data(ticker)
    if df.empty:
        return jsonify({"error": f"No data found for ticker: {ticker}"}), 404

    df = calculate_indicators(df)

    indicators = df[['RSI', 'SMA_50', 'EMA_20', 'WMA_50', 'BB_upper', 'BB_lower', 'MACD', 'CCI', 'WilliamsR']].tail(
        1).to_dict(orient='records')
    return jsonify(indicators), 200


@app.route('/signals', methods=['GET'])
def signals():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    df = get_stock_data(ticker)
    df.reset_index(inplace=True)
    if df.empty:
        return jsonify({"error": f"No data found for ticker: {ticker}"}), 404

    df = calculate_indicators(df)
    df = generate_signals(df)

    signals = df[['date', 'Signal', 'Crossover']].tail(1).to_dict(orient='records')
    df.set_index('date', inplace=True)
    return jsonify(signals), 200


@app.route('/trend_analysis', methods=['GET'])
def trend_analysis():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    df = get_stock_data(ticker)
    if df.empty:
        return jsonify({"error": f"No data found for ticker: {ticker}"}), 404

    df = calculate_indicators(df)
    df = generate_signals(df)

    analysis = analyze_trends(df)
    return jsonify(analysis), 200


@app.route('/lstm_prediction', methods=['GET'])
def lstm_prediction():
    ticker = request.args.get('ticker')

    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    df = load_data(ticker)

    if df.empty:
        return jsonify({"error": f"No data found for ticker: {ticker}"}), 404

    df_lagged = create_lags(df)

    model, train_X, test_X, train_y, test_y = train_and_validate(df_lagged)

    pred_y, actual_y = predict(model, train_X, test_X, train_y, test_y)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(test_y.index, test_y, label="Actual Values", color='blue')
    ax.plot(test_y.index, pred_y, label="Predicted Values", color='red', linestyle='--')
    ax.set_xlabel('Time')
    ax.set_ylabel('Close Price')
    ax.set_title('Actual vs Predicted Close Prices for ' + ticker)
    ax.legend()

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    r2 = r2_score(test_y, pred_y)

    return render_template('LSTM_predictions.html', plot_url=f'/lstm_prediction/plot?ticker={ticker}', r2_score=r2)


@app.route('/lstm_prediction/plot', methods=['GET'])
def plot_image():

    fig, ax = plt.subplots(figsize=(10, 6))
    ticker = request.args.get('ticker')
    df = load_data(ticker)
    df_lagged = create_lags(df)
    model, train_X, test_X, train_y, test_y = train_and_validate(df_lagged)
    pred_y, actual_y = predict(model, train_X, test_X, train_y, test_y)

    ax.plot(test_y.index, test_y, label="Actual Values", color='blue')
    ax.plot(test_y.index, pred_y, label="Predicted Values", color='red', linestyle='--')
    ax.set_xlabel('Time')
    ax.set_ylabel('Close Price')
    ax.set_title('Actual vs Predicted Close Prices for ' + ticker)
    ax.legend()

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')

@app.route('/fundamental-analysis', methods=['GET', 'POST'])
def fundamental_analysis():
    ticker = request.args.get('ticker')
    if ticker:
        analysis_results = retrieve_and_analyze_sentiment(ticker)
    else:
        analysis_results = []

    return render_template('fundamental_analysis.html', results=analysis_results)



if __name__ == "__main__":
    app.run(debug=True, port=5000)
