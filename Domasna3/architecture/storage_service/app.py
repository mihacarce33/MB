from flask import Flask, jsonify, request
from flask_migrate import Migrate
from services.storing_data import insert_data_into_table
from models import db
from dotenv import load_dotenv
import os

load_dotenv()
db_password = os.getenv("MYSQL_PASSWORD")
db_user = os.getenv("MYSQL_USER")
db_name = os.getenv("MYSQL_DB")
db_host = os.getenv("MYSQL_HOST")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Mihail123@localhost/MB_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/insert-data', methods=['POST'])
def insert_data():
    data = request.json.get('data')
    ticker = request.json.get('ticker')
    insert_data_into_table(ticker, data)
    return jsonify({'message': 'Data inserted successfully!'})


if __name__ == "__main__":
    app.run(debug=True, port=5003)
