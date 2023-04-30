import pymysql

 
def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = pymysql.connect(
            host=host_name, user=user_name, password=user_password, database=db_name) 
        print("MySQL Database connection successful")
    except pymysql.Error as e:
        print(f"Error: '{e}'")
    return connection


def read_query1(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        return result
    except pymysql.Error as e:
        print(f"Error: '{e}'")


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except pymysql.Error as e:
        print(f"Error: '{e}'")
