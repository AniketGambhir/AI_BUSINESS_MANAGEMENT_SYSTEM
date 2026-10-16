import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Aniket$2007",
    "database": "ai_business_management_system",
    "autocommit": False
}


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

        return None

    except Error as e:
        print("MySQL connection error:", e)
        return None


def test_connection():
    connection = get_connection()

    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()

            print("====================================")
            print("MySQL connected successfully")
            print("Database:", database[0] if database else "Unknown")
            print("====================================")

            cursor.close()
            connection.close()
            return True

        except Error as e:
            print("Database test error:", e)
            return False

    return False