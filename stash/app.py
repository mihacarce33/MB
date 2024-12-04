from flask import Flask, render_template, jsonify
from flask_migrate import Migrate

from stash.models import TickerData, db, Ticker
from stash.services.main import main

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:finki123@localhost/MB_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scrape', methods=['POST'])
def scrape():
    main()
    return jsonify({'message': 'Scraping complete!'})


@app.route('/ticker/<ticker>')
def get_ticker_data(ticker):
    ticker_obj = db.session.query(Ticker).filter_by(ticker=ticker).first()

    if not ticker_obj:
        return jsonify({'error': 'Ticker not found'}), 404

    data = TickerData.query.filter_by(ticker=ticker).all()

    return render_template('ticker.html', ticker=ticker, data=data)


if __name__ == "__main__":
    app.run(debug=True)
