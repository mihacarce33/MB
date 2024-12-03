from flask import jsonify, render_template

from stash.models import db, Ticker, TickerData

def get_ticker_data(ticker):
    ticker_obj = db.session.query(Ticker).filter_by(ticker=ticker).first()

    if not ticker_obj:
        return jsonify({'error': 'Ticker not found'}), 404

    # Fetch data for the specific ticker using its ID
    data = TickerData.query.filter_by(ticker=ticker).all()

    return render_template('ticker.html', ticker=ticker, data=data)