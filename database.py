import os
import mysql.connector


def get_connection():

    return mysql.connector.connect(
        host=os.environ.get("mysql.railway.internal"),
        port=int(os.environ.get("3306", 3306)),
        user=os.environ.get("root"),
        password=os.environ.get("uzBXmuZQHSkamZkJmsNcguFtlYSTpool"),
        database=os.environ.get("railway")
    )
