from app.db_connector import db_connect, db_disconnect

def local(keyword):
    conn, cur = db_connect()

    db_result = []
    if keyword:
        print('Search in DB Lib ...')
        idx = 0
        findkey = '%'+keyword+'%'

        cur.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                           FROM Semiconductors
                           WHERE `Part Number` LIKE ?)''', findkey)

        for item in cur.fetchall():
            db_result.append(['Semiconductors'])
            for col in item:
                db_result[idx].append(col)
            idx += 1

        cur.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                           FROM Passives
                           WHERE `Part Number` LIKE ?)''', findkey)

        for item in cur.fetchall():
            db_result.append(['Passives'])
            for col in item:
                db_result[idx].append(col)
            idx += 1    

        cur.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                           FROM Electromechanical
                           WHERE `Part Number` LIKE ?)''', findkey)

        for item in cur.fetchall():
            db_result.append(['Electromechanical'])
            for col in item:
                db_result[idx].append(col)
            idx += 1

    db_disconnect(conn, cur)
    return db_result

