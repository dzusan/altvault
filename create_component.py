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
    filler.subclass(field, info)
    if not field['Component_Kind']:
        print('Mandatory field \'Component Kind\' not found')
        field['Component_Kind'] = selection(DBstructure.tables, 'Component Kind', mandatory = True)

    if not field['Case']: # Another way to find 'Case'
        print('\'Case\' field is not in subclass')
        filler.findcase(field, conn, cursor)
        
    # It's preferable to call filler.subclass() before it to fill the 'Case'
    filler.footprint(field, conn, cursor)
    # Choose the datasheet (and preferable to call filler.subclass() before it to fill the 'Table')
    filler.datasheet(field, info)

    field_keys = list(field)
    displayArray = []
    for i in range(len(field_keys)):
        displayArray.append([i, field_keys[i].replace('_', ' '), field[field_keys[i]]])
    tableprint(displayArray, 2, tableName='New part')

    edit_flag = False
    is_edit = None
    while is_edit != 'n':        
        field_edit = None
        is_edit = fillinput('Do you want to edit any field? (index,n): ', 'n')
        if is_edit == 'n':
            break
        else:
            try:
                field_edit = field_keys[int(is_edit)] # <-- Can generate exception

                if field[field_edit] == None:
                    value_edit = input('Type value: ')
                else:
                    value_edit = fillinput('Type value: ', field[field_edit])
                field[field_edit] = value_edit
                print('Field successfully changed')
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
        findkey = ('%'+request+'%',)
        cursor.execute('''SELECT `Part Number`, `Part Description`, Author, CreateDate
                        FROM Semiconductors
                        WHERE `Part Number` LIKE ?''',
                        findkey)
        db_result = cursor.fetchall()
        if db_result:
            tableprint(db_result, 1, tableName='Found in DB Lib')
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
    cursor.execute("SELECT `Part Number` FROM Semiconductors")
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
