import urllib
import DBstructure
from app.db_connector import db_connect, db_disconnect


def storage_update(table, part, cell, qty):
    conn, cur = db_connect()
    upd_query = 'UPDATE ' + table + ' SET `Storage Cell` = ?, `Storage Quantity` = ? WHERE `Part Number` LIKE ?'
    cur.execute(upd_query, (cell, str(qty), part))
    conn.commit()
    db_disconnect(conn, cur)
    return True

def add_part(field):
    # Firstly download datasheet
    # Fix 'HTTP Error 403' from https://stackoverflow.com/a/36663971
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)

    print('Downloading datasheet ...')
    try:
        urllib.request.urlretrieve(field['datasheet_url'], field['HelpURL'])
    except Exception as e:
        print('Download failed', e)
        return 'Downloading datasheet failed: ' + str(e)
    else:
        print('Download successful')

        # Add to database
        # Convert dict to sorted tuple for universal INSERT syntax
        insList = []
        for col in DBstructure.colNames:
            insList.append(field[col.replace(' ', '_')])
        insTuple = tuple(insList)
        
        # Then choose a table
        if field['Component_Kind'] == 'Semiconductors':
            skillet = DBstructure.tupleInsSemiconductors
        elif field['Component_Kind'] == 'Passives':
            skillet = DBstructure.tupleInsPassives
        elif field['Component_Kind'] == 'Electromechanical':
            skillet = DBstructure.tupleInsElectromechanical
        else:
            return 'No table like \'Component Kind\' in DB'

        #  And then make a record
        try:
            conn, cur = db_connect()
            cur.execute(skillet, insTuple)
            conn.commit()
            db_disconnect(conn, cur)
        except Exception as e:
            return 'Database error'

    return 'Component added'