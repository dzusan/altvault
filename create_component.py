import sqlite3
import sys
import colorama
import win32com.client as win

# User
import config
import octopart
import filler

def fillinput(prompt, default=""):
    win.Dispatch("WScript.Shell").SendKeys(default)
    return input(prompt)

def errprint(*args, **kwargs):
    print("\x1b[1;31;40mERROR: ", end="")
    print(*args, end="", **kwargs)
    print("\x1b[0m")

def search_dialog(keyword):
    result = octopart.search(keyword)
    print(result[0][0], result[0][1])

    for i in range(1, len(result)):
        
        if result[i][2] == None:
            info = 'No desctiption'
        elif len(result[i][2]) > 60:
            info = (result[i][2][:60] + '...')
        else:
            info = result[i][2]

        print('{} {:<20} {:<20} {}'.format(i, result[i][0], result[i][1], info))
    
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

def add_rec(conn, cursor, info):
    # Query for obtain field names
    cursor.execute('SELECT * FROM components WHERE `Part Number` LIKE \'ADS7852Y\'')

    # Create dict from coloumns
    field = {}
    for col in cursor.description:
        field[col[0].replace(' ', '_')] = None

    # Fill the fields
    filler.spec(field, info)
    filler.subclass(field, info)
    # It's preferable to call filler.subclass() before it to fill the 'Case'
    filler.footprint(field, conn, cursor)
    # Choose the datasheet (and preferable to call filler.subclass() before it to fill the 'Table')
    filler.datasheet(field, info)

    # Generated automatically from db_prepare.py
    insert_skeleton = 'INSERT INTO components (`Part Number`, `Library Ref`, `Library Path`, `Comment`, `Component Kind`, `Component Type`, `Footprint`, `Pin Count`, `Case`, `Footprint Path`, `Footprint Ref`, `PackageDescription`, `Device`, `Mounted`, `Socket`, `SMD`, `Status`, `Color`, `Part Description`, `Manufacturer`, `Manufacturer Part Number`, `ComponentHeight`, `Manufacturer1 Example`, `Manufacturer1 Part Number`, `Manufacturer1 ComponentHeight`, `HelpURL`, `ComponentLink1URL`, `ComponentLink1Description`, `ComponentLink2URL`, `ComponentLink2Description`, `Author`, `CreateDate`, `LatestRevisionDate`, `Table`, `Sim Model Name`, `Sim File`, `Sim SubKind`, `Sim Netlist`, `Sim Spice Prefix`, `Sim Port Map`, `Resistanse`, `Value`, `TC`, `Power`, `Tolerance`, `Voltage`) VALUES (:Part_Number, :Library_Ref, :Library_Path, :Comment, :Component_Kind, :Component_Type, :Footprint, :Pin_Count, :Case, :Footprint_Path, :Footprint_Ref, :PackageDescription, :Device, :Mounted, :Socket, :SMD, :Status, :Color, :Part_Description, :Manufacturer, :Manufacturer_Part_Number, :ComponentHeight, :Manufacturer1_Example, :Manufacturer1_Part_Number, :Manufacturer1_ComponentHeight, :HelpURL, :ComponentLink1URL, :ComponentLink1Description, :ComponentLink2URL, :ComponentLink2Description, :Author, :CreateDate, :LatestRevisionDate, :Table, :Sim_Model_Name, :Sim_File, :Sim_SubKind, :Sim_Netlist, :Sim_Spice_Prefix, :Sim_Port_Map, :Resistanse, :Value, :TC, :Power, :Tolerance, :Voltage)'

    field_keys = list(field)

    print('\n{:>32}'.format('== New Part =='))
    for i in range(len(field_keys)):
        print('{:3} {:<30} {}'.format(i, field_keys[i].replace('_', ' '), field[field_keys[i]]))

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
        print('\n{:>32}'.format('== Edited Part =='))
        for i in range(len(field_keys)):
            print('{:3} {:<30} {}'.format(i, field_keys[i].replace('_', ' '), field[field_keys[i]]))

    is_add = fillinput('Really add this component? (y,n): ', 'n')
    if is_add == 'y':
    # Make a record
        cursor.execute(insert_skeleton, field)
        conn.commit()
        print('Component added')
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
                        FROM components
                        WHERE `Part Number` LIKE ?''',
                        findkey)
        db_result = cursor.fetchall()
        if db_result:
            print('Found in DB Lib')
            for rec in db_result:

                if rec[1] == None:
                    info = 'No desctiption'
                elif len(rec[1]) > 30:
                    info = (rec[1][:30] + '... ')
                else:
                    info = rec[1]

                print('{:<20} {:<35} {:<15} {}'.format(rec[0], info, rec[2], rec[3]))
            return request
        else:
            print('Not found in DB Lib')

    ### Octopart ###
            print('Search in Octopart ...')
            octopart_result = search_dialog(request)
            if octopart_result[0]:
                part_info = octopart.part(octopart_result[1])

                print('\n{:>30} {}'.format('== Part', 'Specs =='))
                for key in part_info.keys():
                    if key != 'Categories' and key != 'Datasheets': # <-- Comment to print all
                        print('{:>30} {}'.format(key, part_info[key]))

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
    conn = sqlite3.connect(config.DB_path)
    cursor = conn.cursor()
    cursor.execute("SELECT `Part Number` FROM components")
except Exception:
    errprint("Wrong database")
    input("Type any key for exit")
    sys.exit(0)

cursor.execute("PRAGMA foreign_keys = ON")

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
