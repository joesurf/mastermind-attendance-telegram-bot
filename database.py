import os
import logging
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv
import pymysql


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

host = os.environ.get("DB_HOST")
user = "admin"
password = os.environ.get("DB_PASS") 
database = "teleslack"

 
def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = pymysql.connect(
            host=host_name, user=user_name, password=user_password, database=db_name) 
        print("MySQL Database connection successful")
    except pymysql.Error as e:
        print(f"Error: '{e}'")
    return connection


def read_one_query(query):
    connection = create_db_connection(host, user, password, database)
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        return result
    except pymysql.Error as e:
        print(f"Error: '{e}'")
    finally:
        connection.close()


def read_all_query(query):
    connection = create_db_connection(host, user, password, database)
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except pymysql.Error as e:
        print(f"Error: '{e}'")
    finally:
        connection.close()


def execute_query(query):
    connection = create_db_connection(host, user, password, database)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except pymysql.Error as e:
        print(f"Error: '{e}'")
    finally:
        connection.close()
