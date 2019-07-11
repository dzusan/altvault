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
    # Firstly convert dict to sorted tuple for universal INSERT syntax
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
        return 'No table like Component Kind in DB'

    #  And then make a record
    conn, cur = db_connect()
    cur.execute(skillet, insTuple)
    conn.commit()
    db_disconnect(conn, cur)

    return 'Component added'