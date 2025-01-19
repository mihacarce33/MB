import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
db_password = os.getenv("MYSQL_PASSWORD")
db_user = os.getenv("MYSQL_USER")
db_name = os.getenv("MYSQL_DB")
db_host = os.getenv("MYSQL_HOST")

def get_db_connection():
    return mysql.connector.connect(
        host='mysql-db',
        user=db_user,
        password=db_password,
        database=db_name
    )