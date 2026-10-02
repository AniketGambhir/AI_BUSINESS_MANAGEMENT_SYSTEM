import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="PASTE_RAILWAY_HOST_HERE",
        port=PASTE_RAILWAY_PORT_HERE,
        user="root",
        password="Aniket$2007",
        database="railway"
    )
