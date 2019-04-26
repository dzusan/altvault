import sqlite3
import pyodbc

# User
import config

def db_connect():
    try:
        if config.DB_path[-4:] == '.mdb' or config.DB_path[-6:] == '.accdb':
            conn = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+config.DB_path)
        elif config.DB_path[-3:] == '.db':
            conn = sqlite3.connect(config.DB_path)
        else:
            raise Exception

        cursor = conn.cursor()
        cursor.execute("SELECT `Part Number` FROM Semiconductors") # Test query
    except Exception:
        print('Wrong database')
        return None

    return conn, cursor

def db_disconnect(conn, cursor):
    conn.close()