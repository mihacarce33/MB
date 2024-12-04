from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ticker(db.Model):
    __tablename__ = 'Tickers'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(255), unique=True, nullable=False)


class TickerData(db.Model):
    __tablename__ = 'ticker_data'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.VARCHAR(255), db.ForeignKey('Tickers.ticker'), nullable=False)
    date = db.Column(db.Date, nullable=False, unique=True)
    last_transaction_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    min_price = db.Column(db.Float)
    average_price = db.Column(db.Float)
    percent_change = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    best_turnover = db.Column(db.Float)
    total_turnover = db.Column(db.Float)
