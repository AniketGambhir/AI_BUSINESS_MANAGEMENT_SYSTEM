import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Aniket$2007",
    "database": "ai_business_management_system"
}


def get_connection():
    """
    Create and return a MySQL database connection.
    """

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as e:
        print("MySQL connection error:", e)

    return None


def test_connection():
    """
    Test MySQL connection.
    """

    connection = get_connection()

    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()

            cursor.close()
            connection.close()

            return {
                "success": True,
                "database": database[0] if database else None
            }

        except Exception as e:
            try:
                connection.close()
            except Exception:
                pass

            return {
                "success": False,
                "error": str(e)
            }

    return {
        "success": False,
        "error": "Unable to connect to MySQL"
    }