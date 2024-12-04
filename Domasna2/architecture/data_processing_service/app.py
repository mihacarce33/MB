from flask import Flask, jsonify
#
# from services.data_processing import get_ticker_data
#
app = Flask(__name__)
#
#
# @app.route('/ticker-data/<ticker>', methods=['GET'])
# def ticker_data(ticker):
#     # Fetch and return data for the given ticker from the database
#     data = get_ticker_data(ticker)  # Implement this function as needed
#     return jsonify({'data': data})
#
#
if __name__ == "__main__":
    app.run(debug=True, port=5002)
