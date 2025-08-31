import sqlite3

def conection_db():
    try:
        conn = sqlite3.connect("spam.db")
        return conn
    except:
        return 'an error ocurred.'

def consulta_db(query):
    if conection_db() != 'an error ocurred.':
        try:
            cursor = conection_db().cursor()
            resp = cursor.execute(query)
            return resp.fetchone()
        except:
            return 'an error ocurred to consult into.'
    else:
        return 'an error ocurred to connect in db.'


def insert_into(query):
    if conection_db() != 'an error ocurred.':
        try:
            conn = conection_db()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
        except:
            return 'an error ocurred to insert into.'
    else:
        return 'an error ocurred to connect in db.'

def update_into(query):
    if conection_db() != 'an error ocurred.':
        try:
            conn = conection_db()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
        except:
            return 'an error ocurred to update into.'
    else:
        return 'an error ocurred to connect in db.'