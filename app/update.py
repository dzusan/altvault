from app.db_connector import db_connect, db_disconnect

def storage_update(table, part, cell, qty):
    conn, cur = db_connect()
    upd_query = 'UPDATE ' + table + ' SET `Storage Cell` = ?, `Storage Quantity` = ? WHERE `Part Number` LIKE ?'
    cur.execute(upd_query, (cell, str(qty), part))
    conn.commit()
    db_disconnect(conn, cur)
    return True