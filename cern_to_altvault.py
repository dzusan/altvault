import os
import re
import pyodbc

# User
import DBstructure
import config

# TODO: (!) Insert 'Table' column
# TODO: generate query with .format()
# TODO: write log

# Connect to target single table Database
targetCon = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+config.DB_path)
targetCur = targetCon.cursor()
targetSearch = 'SELECT `Part Number` FROM components WHERE `Part Number` LIKE ?'

# Obtain full paths for donor Databases
DBs = []
for fileName in os.listdir(config.CERNdir):
    if re.search(r'.mdb', fileName):
        DBs.append(config.CERNdir + '\\' + fileName)

# Perfor operation for each donor Database
for DB_path in DBs:
    print('====== Database =======\n{}\n'.format(DB_path))
    donorCon = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+DB_path)
    donorCur = donorCon.cursor()

    # Obtain necessary tables in DB
    needTables = []
    for col in donorCur.columns():
        if col.column_name == 'Part Number':
            needTables.append(col.table_name)


    for table in needTables:
        print('-------- Table {} ---------\n'.format(table))

        query = 'SELECT * FROM `'
        query += table    
        query += '`'

        donorCur.execute(query)
        parts = donorCur.fetchall()

        for part in parts:
            targetCur.execute(targetSearch, part[0])
            targetResult = targetCur.fetchall()
            if not targetResult:
                print('Transfer part:\n{}\n'.format(part))

                # Obtain match columns and assembly INSERT query
                colSkeleton = ''
                colCount = 0

                for col in donorCur.columns(table=table):
                    if col.column_name in DBstructure.colNames:
                        colSkeleton += '`' + col.column_name + '`, '
                        colCount += 1

                donorSelect = 'SELECT '
                donorSelect += colSkeleton[:-2]
                donorSelect += ' FROM `'
                donorSelect += table
                donorSelect += '` WHERE `Part Number` LIKE ?'
                print('Assembled SELECT query for donor Database:\n{}\n'.format(donorSelect))

                targetInsert = 'INSERT INTO components ('
                targetInsert += colSkeleton[:-2]
                targetInsert += ') VALUES ('
                targetInsert += ('?,'*colCount)[:-1]
                targetInsert += ')'
                print('Assembled INSERT query for target Database:\n{}\n'.format(targetInsert))

                print('-----------------------------\n')
                
                donorCur.execute(donorSelect, part[0])
                donorResult = donorCur.fetchall()
                targetCur.execute(targetInsert, donorResult[0])
                targetCur.commit()

    donorCon.close()

targetCon.close()

