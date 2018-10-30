import sqlite3
import pyodbc
import sys
import colorama
import os

# User
import config
import octopart
import filler
import DBstructure
from markup import *


def search_dialog(keyword):
    # TODO: Fix breaking program if not valid choice
    result = octopart.search(keyword)
    print(result[0][0], result[0][1])
    if result[0][1] == 0:
        return (False, keyword)
    else:
        tableprint(result[1:], 2, tableName='Part', itemize=1, lastCol=2)
        choice_word = input('Your decision (number or new keyword): ')
        if choice_word.isdecimal():
            choice_index = int(choice_word)
            if choice_index >= 1 and choice_index <= 9:
                print('You choose {} (UID {})'.format(result[choice_index][0], result[choice_index][3]))
                return (True, result[choice_index][3])
            else:
                print('No such variant')
                return(False, '')
        else:        
            return (False, choice_word)

def select_author():
    illegals = ('Datasheets', 'History')
    glob_path = os.path.dirname(config.DB_path)
    possible_authors = [name for name in os.listdir(glob_path) 
                        if os.path.isdir(glob_path + '\\' + name)
                        and name not in illegals]
    
    return selection(possible_authors, 'Author', mandatory = True)


def add_rec(conn, cursor, info):
    # Create dict from coloumns
    field = {}
    for col in DBstructure.colNames:
        field[col.replace(' ', '_')] = None

    # Select Author
    filler.author = select_author()

    # Fill the fields
    filler.spec(field, info)
    filler.subclass(field, info, conn, cursor)
    if not field['Component_Kind']:
        print('Mandatory field \'Component Kind\' not found')
        field['Component_Kind'] = selection(DBstructure.tables, 'Component Kind', mandatory = True)

    # TODO: Fill the fields based on 'Component_Kind' like Comment =Device or =Value

    # Choose the datasheet
    # It's preferable to call filler.subclass() before it 
    # to fill the 'Component_Kind' and 'Table'
    filler.datasheet(field, info)
    # It's preferable to call filler.subclass() before it to fill the 'Case'
    filler.footprint(field, conn, cursor)


    field_keys = list(field)
    displayArray = []
    for i in range(len(field_keys)):
        displayArray.append([i, field_keys[i].replace('_', ' '), field[field_keys[i]]])
    tableprint(displayArray, 2, tableName='New part')

    edit_flag = False
    is_edit = None
    while is_edit != 'q':        
        field_edit = None
        is_edit = input('Field number to edit (number, \'q\' to quit): ')
        if is_edit == 'q':
            break
        else:
            try:
                field_edit = field_keys[int(is_edit)] # <-- Can generate exception

                if field[field_edit] == None:
                    value_edit = input('Type value: ')
                else:
                    value_edit = fillinput('Type value: ', field[field_edit])
                field[field_edit] = value_edit
                tableprint(((is_edit, field_edit, value_edit),), 2)
                edit_flag = True
            except:
                print('No such field')

    if edit_flag:
        displayArray = []
        for i in range(len(field_keys)):
            displayArray.append([i, field_keys[i].replace('_', ' '), field[field_keys[i]]])
        tableprint(displayArray, 2, tableName='Edited part')

    is_add = fillinput('Really add this component? (y,n): ', 'n')
    if is_add == 'y':
        # Firstly convert dict to sorted tuple for universal INSERT syntax
        insList = []
        for col in DBstructure.colNames:
            insList.append(field[col.replace(' ', '_')])
        insTuple = tuple(insList)

        # Then choose table and make a record
        if field['Component_Kind'] == 'Semiconductors':
            cursor.execute(DBstructure.tupleInsSemiconductors, insTuple)
            conn.commit()
            print('Component added')
        elif field['Component_Kind'] == 'Passives':
            cursor.execute(DBstructure.tupleInsPassives, insTuple)
            conn.commit()
            print('Component added')
        elif field['Component_Kind'] == 'Electromechanical':
            cursor.execute(DBstructure.tupleInsElectromechanical, insTuple)
            conn.commit()
            print('Component added')
        else:
            print('No table like Component Kind in DB')        
    else:
        print('You cancel')



def dialog(conn, cursor, prefill=''):
    ### Request ###
    request = fillinput('Search part: ', prefill)
    
    if request:
    ### DB Lib ###
        print('Search in DB Lib ...')
        db_result = []
        idx = 0
        findkey = '%'+request+'%'

        cursor.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                           FROM Semiconductors
                           WHERE `Part Number` LIKE ?)''', findkey)

        for item in cursor.fetchall():
            db_result.append(['Semiconductors'])
            for col in item:
                db_result[idx].append(col)
            idx += 1

        cursor.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                            FROM Passives
                            WHERE `Part Number` LIKE ?)''', findkey)

        for item in cursor.fetchall():
            db_result.append(['Passives'])
            for col in item:
                db_result[idx].append(col)
            idx += 1    

        cursor.execute('''(SELECT `Part Number`, `Part Description`, Author, CreateDate, `Storage Cell`, `Storage Quantity`
                            FROM Electromechanical
                            WHERE `Part Number` LIKE ?)''', findkey)

        for item in cursor.fetchall():
            db_result.append(['Electromechanical'])
            for col in item:
                db_result[idx].append(col)
            idx += 1

        if idx:     
            DBchoice = selection(db_result, 'part in DB Lib', cutColoumn = 2)
            if DBchoice:
                changeQuery = 'UPDATE ' + DBchoice[0] + ' SET `Storage Cell` = ?, `Storage Quantity` = ? WHERE `Part Number` LIKE ?'
                cellChoice = fillinput('Cell: ', DBchoice[5] if DBchoice[5] else '')
                quantityChoice = fillinput('Quantity: ', DBchoice[6] if DBchoice[6] else '')
                cursor.execute(changeQuery, (cellChoice, quantityChoice, DBchoice[1]))
                conn.commit()
                print('Record changed successfully')

            # TODO: Make possible continue to search in octopart even if 
            #       part found in db. For patrial names like 
            #       '84952-4' part of '2-84952-4'
            return request
        else:
            print('Not found in DB Lib')

    ### Octopart ###
            print('Search in Octopart ...')
            octopart_result = search_dialog(request)
            if octopart_result[0]:
                part_info = octopart.part(octopart_result[1])

                displayArray = []
                for key in part_info.keys():
                    if key != 'Categories' and key != 'Datasheets': # <-- Comment to print all
                        displayArray.append([key, part_info[key]])
                tableprint(displayArray, 1, tableName='Part specs')

                is_add = fillinput('Add component to DB Lib? (y,n): ', 'y')
                if is_add == 'y':
                    add_rec(conn, cursor, part_info)
                else:
                    return request
            else:
                print('Initialize new search with this keyword')
                return octopart_result[1]
    else:
        print('Empty keyword')

    return prefill


#################################
colorama.init()

# Prefer the command line argument
if len(sys.argv) > 1:
    config.DB_path = sys.argv[1]
if len(sys.argv) > 2:
    config.apikey = sys.argv[2]
if len(sys.argv) > 3:
    config.prefill_key = sys.argv[3]

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
    errprint("Wrong database")
    input("Type any key for exit")
    sys.exit(0)

try:
    while(True):
        print("")
        config.prefill_key = dialog(conn, cursor, config.prefill_key)
except KeyboardInterrupt:
    print("")
    errprint("You break the program")
except EOFError:
    print("")
    errprint("You break the program")
except Exception as e: # Unexpected break
    print(e)
finally:
    conn.close()
    print("--- break ---") # For debug
    input('Press ENTER')
