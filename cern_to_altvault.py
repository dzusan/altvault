import os
import re
import pyodbc
from datetime import datetime

# User
import DBstructure
import config

# TODO: generate query with .format()

### Create log file ###
nowTimeStamp = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
logFileName = os.path.dirname(config.DB_path) + '\\Transfer ' + nowTimeStamp + '.log'

try:
    logFile = open(logFileName, "w")
except Exception as e:
    print("ERROR opening log file: {}".format(e))
else:
    print("{} log file opened successfully".format(logFile.name))

msg = 'Date/Time: {}\nTarget DB: {}\nDonor CERN DBs: {}\n\n'.format(nowTimeStamp, config.DB_path, config.CERNdir)
logFile.write(msg)

print('Processing...')

# Connect to target single table Database
targetCon = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+config.DB_path)
targetCur = targetCon.cursor()
targetSearch = 'SELECT `Part Number` FROM components WHERE `Part Number` LIKE ?'

# Obtain full paths for donor Databases
DBs = []
for fileName in os.listdir(config.CERNdir):
    if re.search(r'.mdb', fileName):
        DBs.append(config.CERNdir + '\\' + fileName)

# Statistics counters
totalDBs = 0
totalTables = 0
totalRecords = 0

# Perfor operation for each donor Database
for DB_path in DBs:
    # Statistics
    totalDBs += 1

    logFile.write('====== Database =======\n{}\n\n'.format(DB_path))
    donorCon = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+DB_path)
    donorCur = donorCon.cursor()

    # Obtain necessary tables in DB
    needTables = []
    for col in donorCur.columns():
        if col.column_name == 'Part Number':
            needTables.append(col.table_name)


    for table in needTables:
        # Statistics
        tableRecords = 0
        totalTables += 1

        logFile.write('-------- Table {} ---------\n\n'.format(table))

        query = 'SELECT * FROM `'
        query += table    
        query += '`'

        donorCur.execute(query)
        parts = donorCur.fetchall()

        for part in parts:
            targetCur.execute(targetSearch, part[0])
            targetResult = targetCur.fetchall()
            if not targetResult:
                logFile.write('Transfer part:\n{}\n\n'.format(part))

                # Obtain match columns and assembly INSERT query
                colSkeleton = ''
                colCount = 0
                libPathIdx = 0
                footPathIdx = 0

                for col in donorCur.columns(table=table):
                    if col.column_name in DBstructure.colNames:
                        colSkeleton += '`' + col.column_name + '`, '
                        libPathIdx = colCount if col.column_name == 'Library Path' else libPathIdx
                        footPathIdx = colCount if col.column_name == 'Footprint Path' else footPathIdx
                        colCount += 1

                donorSelect = 'SELECT '
                donorSelect += colSkeleton[:-2]
                donorSelect += ' FROM `'
                donorSelect += table
                donorSelect += '` WHERE `Part Number` LIKE ?'
                logFile.write('Assembled SELECT query for donor Database:\n{}\n\n'.format(donorSelect))

                targetInsert = 'INSERT INTO components ('
                targetInsert += colSkeleton
                targetInsert += '`Table`) VALUES ('
                targetInsert += '?,'*colCount
                targetInsert += '?)'
                logFile.write('Assembled INSERT query for target Database:\n{}\n\n'.format(targetInsert))

                logFile.write('-----------------------------\n\n')
                
                donorCur.execute(donorSelect, part[0])
                donorResult = donorCur.fetchall()
                insertData = list(donorResult[0])

                # Change Library and Footprint Path (move to 'CERN\' directory)
                if libPathIdx != 0:
                    insertData[libPathIdx] = 'CERN\\' + insertData[libPathIdx]                    
                if footPathIdx != 0:
                    insertData[footPathIdx] = 'CERN\\' + insertData[footPathIdx]

                # Add Table information
                insertData.append(table)
                
                targetCur.execute(targetInsert, insertData)
                targetCur.commit()

                # Statistics
                tableRecords += 1
                totalRecords += 1
        
        logFile.write('*************************************\n')
        logFile.write('Transfered records in this table: {}\n'.format(tableRecords))
        logFile.write('*************************************\n\n\n')

    donorCon.close()

# Statistics
logFile.write('\n\n\n*******Total Statistics*******\n')
logFile.write('Total donor DBs: {}\n'.format(totalDBs))
logFile.write('Total read tables: {}\n'.format(totalTables))
logFile.write('Total transfered records: {}\n'.format(totalRecords))
logFile.write('******************************\n')

print('Transfer successful')
print('See log in {}'.format(logFileName))

targetCon.close()
logFile.close()
