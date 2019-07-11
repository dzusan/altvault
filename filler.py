import os
import sqlite3
from datetime import datetime
import subprocess
import urllib
import re

# User
import config
import DBstructure
from markup import *
from app.db_connector import db_connect, db_disconnect

author = config.default_author

def fill_all(info, form_author=config.default_author):
    global author
    # Create dict from coloumns
    field = {}
    for col in DBstructure.colNames:
        field[col.replace(' ', '_')] = None

    # Fill the fields
    author = form_author
    spec(field, info)

    # Connect DB to search subclass
    conn, cur = db_connect()
    subclass(field, info, conn, cur)
    db_disconnect(conn, cur)

    # if not field['Component_Kind']:
    #     print('Mandatory field \'Component Kind\' not found')
    #     field['Component_Kind'] = selection(DBstructure.tables, 'Component Kind', mandatory = True)

    return field
    


def spec(mydb, octo):
    print('Filling specs ...')
    # Independed fields    
    mydb['Mounted'] = 'Yes'
    mydb['Part_Description'] = octo['Part Description']
    mydb['Manufacturer'] = octo['Manufacturer'].upper()
    mydb['Manufacturer_Part_Number'] = octo['Part Number']
    mydb['Author'] = author
    mydb['CreateDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mydb['LatestRevisionDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')     

    # Optional fields
    mydb['Pin_Count'] = octo['<Number of Pins>']    if '<Number of Pins>'   in octo.keys() else None
    mydb['Status']    = octo['<Lifecycle Status>']  if '<Lifecycle Status>' in octo.keys() else None
    if '<Mounting Style>' in octo.keys():
        if 'Surface Mount' in octo['<Mounting Style>']:
            mydb['SMD'] = 'Yes'
        else:
            mydb['SMD'] = 'No'
    else:
        mydb['SMD'] = None

    # Default fields (temporary prefer to overwrite onward)
    mydb['Part_Number'] = octo['Part Number']
    mydb['Library_Ref'] = octo['Part Number']
    mydb['Footprint_Ref'] = octo['Part Number']
    mydb['Footprint'] = octo['Part Number']
    mydb['Library_Path'] = author + '\\SchLib\\' + octo['Part Number'] + '.SchLib'
    mydb['Footprint_Path'] = author + '\\PcbLib\\' + octo['Part Number'] + '.PcbLib'
    
    # ??? fields
    # mydb['Component_Kind'] = 'Standard'
    mydb['Component_Type'] = 'Standard'

    

def subclass(mydb, octo, conn, cursor):
    print('Obtained subclasses: ', end='')
    for i, sc in enumerate(octo['Categories']):
        print(sc, end='')
        if i != len(octo['Categories']) - 1:
            print(', ', end='')

    print('\nFilling fields according this subclasses ...')
    
    ### LOWER LEVEL ###

    if ('Passive Components' in octo['Categories'] or
        'Fuses'              in octo['Categories'] or
        'Varistors'          in octo['Categories']):
        mydb['Comment'] = '=Value'
        # Cut Case/Package as [-4:] if it's like '3216, 1206'
        mydb['Case'] = octo['<Case/Package>'][-4:] if '<Case/Package>' in octo.keys() else None
        mydb['Voltage'] = octo['<Voltage Rating (DC)>'].replace(' ', '') + 'DC' if '<Voltage Rating (DC)>' in octo.keys() else None
        mydb['Component_Kind'] = 'Passives'

    if ('Integrated Circuits (ICs)' in octo['Categories'] or
        'Sensors' in octo['Categories'] or
        'Discrete Semiconductors' in octo['Categories']):
        mydb['Comment'] = '=Device'
        mydb['Device'] = octo['Part Number']
        if '<Case/Package>' in octo.keys():
            if '<Number of Pins>' in octo.keys():
                mydb['Case'] = octo['<Case/Package>'] + octo['<Number of Pins>']
            else:
                mydb['Case'] = octo['<Case/Package>']
        else:
            mydb['Case'] = None
        mydb['Component_Kind'] = 'Semiconductors'
        mydb['Library_Path'] = author + '\\SchLib\\SOC_GOST.SchLib' # Default
        mydb['Footprint_Path'] = author + '\\PcbLib\\ICs And Semiconductors SMD.PcbLib' # Default
    
    if ('Connectors' in octo['Categories'] or
        'Connectors ' in octo['Categories']): # Yeah, it's weird, but in Octopart 'Connectors ' can be with whitespase
        mydb['Part_Number'        ] = mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Footprint_Ref'      ] = mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Footprint'          ] = mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Component_Kind'     ] = 'Electromechanical'
        mydb['Table'              ] = mydb['Manufacturer']
        mydb['PackageDescription' ] = octo['Part Description']

        mydb['Comment'] = '=Value'
        if octo['Part Description']:
            if ' CONNECTOR' in octo['Part Description']:
                mydb['Value'] = octo['Part Description'].upper().split(' CONNECTOR')[0]
        else:
            mydb['Value'] = octo['Part Number']

        octo['<Number of Contacts>'] + '8Pin'
        mydb['Library_Path'] = author + '\\SchLib\\Connectors GOST.SchLib' # Default      
        if mydb['SMD'] == 'Yes':
            mydb['Footprint_Path'] = author + '\\PcbLib\\Connectors SMD.PcbLib' # Default
        else:
            mydb['Footprint_Path'] = author + '\\PcbLib\\Connectors THD.PcbLib' # Default  
        if '<Number of Contacts>' in octo.keys():
            mydb['Library_Ref'] = octo['<Number of Contacts>'] + 'Pin'
            mydb['Pin_Count'] = octo['<Number of Contacts>']
        if '<Number of Positions>' in octo.keys():
            mydb['Library_Ref'] = octo['<Number of Positions>'] + 'Pin'
            mydb['Pin_Count'] = octo['<Number of Positions>']
        if '<Color>' in octo.keys():
            mydb['Color'] = octo['<Color>']
        if '<Housing Color>' in octo.keys():
            mydb['Color'] = octo['<Housing Color>']

    if 'Electromechanical' in octo['Categories']:
        mydb['Component_Kind'] = 'Electromechanical'

    # Finally
    if not mydb['Case']: # Another way to find 'Case'
        print('\'Case\' field is not in subclass')
        findcase(mydb, conn, cursor)

    ### MIDDLE LEVEL ###

    if 'Capacitors' in octo['Categories']:
        mydb['Table'] = 'Capacitors'
        mydb['Sim_Model_Name'] = 'CAP'
        mydb['Sim_SubKind'] = 'Capacitor'
        mydb['Sim_Spice_Prefix'] = 'C'        
        mydb['Sim_Netlist'] = '@DESIGNATOR %1 %2 @VALUE'
        if '<Capacitance>' in octo.keys():
            value = octo['<Capacitance>']
            value = value.replace(' ', '')
            value = value.replace('F', '')
            value = value.replace('µ', 'u')
            mydb['Value'] = value
        else:
            mydb['Value'] = None
        mydb['Tolerance'] = octo['<Capacitance Tolerance>']  if '<Capacitance Tolerance>' in octo.keys() else None
        mydb['Library_Path'] = 'CERN\\SchLib\\Capacitors.SchLib'
        mydb['Footprint_Path'] = author + '\\PcbLib\\Capacitors THD.PcbLib' # Default
        # TODO: Or SMD too
        mydb['Pin_Count'] = '2' if not mydb['Pin_Count'] else mydb['Pin_Count']  
    
    if 'Resistors' in octo['Categories'] or 'Resistor Arrays' in octo['Categories']:
        if 'Resistor Arrays' in octo['Categories']:
            mydb['Table'] = 'Resistor Networks SMD'
            mydb['Footprint_Path'] = 'CERN\\PcbLib\\Networks SMD.PcbLib'
            mydb['Case'] = octo['Part Number'].split('-')[0].split(' ')[0]
            mydb['Part_Number'] = 'RN'
            if '<Number of Contacts>' in octo.keys():
                if '8' in octo['<Number of Contacts>']:
                    mydb['Library_Ref'] = 'RN DIL8_4xR_Isolated_5%'
                elif '16' in octo['<Number of Contacts>']:
                    mydb['Library_Ref'] = 'RN DIL16_8xR_Isolated_5%'
                else:
                    mydb['Library_Ref'] = None
        else:
            mydb['Table'] = 'Resistors'
            mydb['Footprint_Path'] = 'CERN\\PcbLib\\Resistors SMD.PcbLib'
            mydb['Part_Number'] = 'R'
            if '<Resistance Tolerance>' in octo.keys():
                if octo['<Resistance Tolerance>'] == '±0.1%':
                    mydb['Library_Ref'] = 'Resistor - 0.1%'
                elif octo['<Resistance Tolerance>'] == '±1%':
                    mydb['Library_Ref'] = 'Resistor - 1%'
                elif octo['<Resistance Tolerance>'] == '±5%':
                    mydb['Library_Ref'] = 'Resistor - 5%'
                else:
                    mydb['Library_Ref'] = None
            if mydb['Case']:
                mydb['Part_Number'] += mydb['Case']

        if '<Resistance>' in octo.keys():
            resSplitted = octo['<Resistance>'].split(' ')
            if len(resSplitted[1]) == 1:
                expMod = 'R'
            elif resSplitted[1][0] == 'm': # Milli-ohms not Mega
                expMod = 'milli'
            else:
                expMod = resSplitted[1][0].upper()

            if expMod == 'milli':
                resVal = float(resSplitted[0]) * 10**(-3)
                resStr = str(resVal)
                resMant = resStr.split('.')
                res = '0R' + resMant[1]
            else:
                res = resSplitted[0].replace('.', expMod)
            
            mydb['Part_Number'] += '_' + res

            value = octo['<Resistance>']
            value = value.replace(' ', '')
            value = value.replace('Ω', '')
            mydb['Value'] = value
        else:
            mydb['Value'] = None        
        
        if '<Resistance Tolerance>' in octo.keys():
            mydb['Part_Number'] += '_' + octo['<Resistance Tolerance>'][1:]
            mydb['Tolerance'] = octo['<Resistance Tolerance>']
            
        if '<Power Rating>' in octo.keys():
            mydb['Power'] = octo['<Power Rating>']
            if 'm' not in octo['<Power Rating>']: # Not add milli-watts
                powSplit = octo['<Power Rating>'].split(' ')
                power = powSplit[0].strip('0').strip('.') + 'W'
                mydb['Part_Number'] += '_' + power

        mydb['Part_Number'] += '_' + octo['Part Number']

        mydb['Sim_Model_Name'] = 'RES'
        mydb['Sim_SubKind'] = 'Resistor'        
        mydb['Sim_Spice_Prefix'] = 'R'
        mydb['Sim_Netlist'] = '@DESIGNATOR %1 %2 @VALUE'
        mydb['Library_Path'] = 'CERN\\SchLib\\Resistors.SchLib'
        mydb['Pin_Count'] = '2' if not mydb['Pin_Count'] else mydb['Pin_Count']

    if 'Inductors' in octo['Categories']:
        mydb['Part_Number'] = 'IND'

        if mydb['Case']:
            mydb['Part_Number'] += mydb['Case']

        if '<Inductance>' in octo.keys():
            ind = octo['<Inductance>']
            if '.0 ' in ind:
                ind = ind.replace('.0 ', '')
            ind = ind.replace(' ', '')
            ind = ind.replace('µ', 'u')         
            mydb['Value'] = ind   
            ind = ind.upper()
            mydb['Part_Number'] += '_' + ind
        else:
            mydb['Value'] = None        
        
        if '<Inductance Tolerance>' in octo.keys():
            mydb['Part_Number'] += '_' + octo['<Inductance Tolerance>'][1:]

        mydb['Part_Number'] += '_' + octo['Manufacturer'].upper() + '_' + octo['Part Number']

        if mydb['SMD'] =='Yes':
            mydb['Table'] = 'Inductors SMD'
        else:
            mydb['Table'] = 'Inductors'

        mydb['Library_Path'] = 'CERN\\SchLib\\Inductors & Transformers.SchLib'
        mydb['Library_Ref'] = 'Inductor'
        mydb['Footprint_Path'] = 'CERN\\PcbLib\\Inductors SMD.PcbLib' # Default 
        mydb['Footprint_Ref'] = 'IND_' + octo['Manufacturer'].upper() + '_' + octo['Part Number']
        mydb['Footprint'] = 'IND_' + octo['Manufacturer'].upper() + '_' + octo['Part Number']
        mydb['Pin_Count'] = '2' if not mydb['Pin_Count'] else mydb['Pin_Count']

    if 'Varistors' in octo['Categories']:
        mydb['Part_Number'] = 'VAR_' + mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Table'] = 'Thermistors And Varistors'
        mydb['Value']   = octo['<Voltage Rating (DC)>'].replace(' ', '') + 'DC' if '<Voltage Rating (DC)>' in octo.keys() else None
        mydb['Library_Path'] = 'CERN\\SchLib\\Resistors.SchLib'
        mydb['Library_Ref'] = 'Varistor'
        mydb['Footprint_Path'] = 'CERN\\PcbLib\\Thermistors And Varistors.PcbLib' # Default
        mydb['Pin_Count'] = '2' if not mydb['Pin_Count'] else mydb['Pin_Count']

    if 'Fuses' in octo['Categories']:
        if re.search('[a-zA-Z]', mydb['Case']):
            mydb['Part_Number'] = 'FUSR' + '_'
        else:
            mydb['Part_Number'] = 'FUS' + mydb['Case'] + '_'
        mydb['Part_Number'] += mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Table'] = 'Fuses'
        mydb['Value']   = octo['<Current Rating>'].replace(' ', '') if '<Current Rating>' in octo.keys() else None
        mydb['Library_Path'] = 'CERN\\SchLib\\Fuses.SchLib'
        mydb['Library_Ref'] = 'Fuse'
        mydb['Footprint_Path'] = 'CERN\\PcbLib\\Fuses.PcbLib' # Default
        mydb['Pin_Count'] = '2' if not mydb['Pin_Count'] else mydb['Pin_Count']

    if 'Transistors' in octo['Categories']:
        mydb['Table'] = 'Transistors'
        mydb['Library_Path'] = author + '\\SchLib\\Transistors.SchLib'
        mydb['Pin_Count'] = '3' if not mydb['Pin_Count'] else mydb['Pin_Count']

    if 'Switches' in octo['Categories'] or 'Encoders' in octo['Categories']:
        mydb['Part_Number'] = 'SW_' + mydb['Manufacturer'].replace(' ', '_') + '_' + octo['Part Number']
        mydb['Table'] = 'Switches'
        mydb['Library_Path'] = 'CERN\\SchLib\\Switches.SchLib'
        mydb['Library_Ref'] = 'SW 1x SPST DIP Switch' # Default
        mydb['Footprint_Path'] = author + '\\PcbLib\\Switches.PcbLib' # Default
        mydb['Footprint_Ref'] = mydb['Part_Number']
        mydb['Footprint'] = mydb['Part_Number']

    # TODO: Add diodes
        

    ### UPPER LEVEL ###

    if 'Ceramic Capacitors' in octo['Categories']:
        mydb['Library_Ref'] = 'Capacitor - non polarized'
        mydb['TC'] = octo['<Dielectric Characteristic>'] if '<Dielectric Characteristic>' in octo.keys() else None
        mydb['Part_Number'] = 'CC'

        if mydb['Case']:
            mydb['Part_Number'] += mydb['Case']

        if '<Capacitance>' in octo.keys():
            cap = octo['<Capacitance>']
            if '.0 ' in cap:
                cap = cap.replace('.0 ', '')
            cap = cap.replace(' ', '')
            cap = cap.replace('µ', 'u')         
            mydb['Value'] = cap   
            cap = cap.upper()
            mydb['Part_Number'] += '_' + cap
        else:
            mydb['Value'] = None    

        if '<Voltage Rating (DC)>' in octo.keys():
            vol = octo['<Voltage Rating (DC)>']
            if '.0 ' in vol:
                vol = vol.replace('.0 ', '')
            vol = vol.replace(' ', '')  
            mydb['Voltage'] = vol
            vol = vol.upper()
            mydb['Part_Number'] += '_' + vol
        else:
            mydb['Value'] = None    

        if mydb['Tolerance']:
            mydb['Part_Number'] += '_' + mydb['Tolerance'].replace('±', '')

        if mydb['TC']:
            mydb['Part_Number'] += '_' + mydb['TC']

    if 'Aluminum Electrolytic Capacitors' in octo['Categories']:
        mydb['Library_Ref'] = 'Capacitor - polarized'

    if 'Amplifiers - Op Amps, Buffer, Instrumentation' in octo['Categories']:
        mydb['Library_Path'] = 'SchLib\\Operational Amplifiers.SchLib'
        mydb['Table'] = 'Operational Amplifiers'
        if '<Number of Channels>' in octo.keys():
            if octo['<Number of Channels>'] == '1':
                mydb['Library_Ref'] = 'Operational Amplifier Type1'
            elif octo['<Number of Channels>'] == '2':
                mydb['Library_Ref'] = 'Operational Amplifier x2 Type1'
            elif octo['<Number of Channels>'] == '4':
                mydb['Library_Ref'] = 'Operational Amplifier x4 Type1'
        else:
            mydb['Library_Ref'] = None


def findcase(mydb, conn, cursor):
    print('Searching \'Case\' in Part Description ...')
    cursor.execute('''(SELECT Case FROM Semiconductors GROUP BY Case)
                     UNION
                      (SELECT Case FROM Passives GROUP BY Case)
                     UNION
                      (SELECT Case FROM Electromechanical GROUP BY Case)''')
    results = cursor.fetchall()

    # Stage 1 (optimistic): Search raw like 'SOT23-3'
    for row in results:
        try:
            if len(row[0]) > 2: # <-- can rise exception
                fullCaseName = ' ' + row[0] + ' ' # Whitespaces for ignore partial matches
                for key in mydb:
                    if mydb[key]:
                        if mydb[key].upper().find(fullCaseName) != -1:
                            print('Found (optimistic):', fullCaseName)
                            mydb['Case'] = fullCaseName[1:-1] # Erase whitespaces back
                            return
        except:
            pass

    # Stage 2 (hopeless): Search only first letters set like 'SOT'
    found_hopeless = []
    for row in results:
        try:
            caseAcronym = re.split('(\d+)', row[0])[0]  # <-- can rise exception
            if len(caseAcronym) > 2:
                for key in mydb:
                    if mydb[key]:
                        if mydb[key].upper().find(caseAcronym) != -1:
                            found_hopeless.append(caseAcronym)
        except:
            pass     

    if found_hopeless:
        longestMatch = max(found_hopeless, key=len)        
        print('Found (hopeless):', longestMatch)
        mydb['Case'] = longestMatch
    else:
        print('Not found available packages in Part Description')



def footprint(mydb, conn, cursor):
    print('Matching \'Case\' field with footprint ...')

    # TODO: Search mydb['Case'] not only in 'Case' field in DB.
    # For example FUSC_BOURNS_SF-1206S in CERN\PcbLib\Fuses.PcbLib
    # but not contains any reflection in 'Case' coloumn
    # CHECK: FUS1206_BOURNS_SF-1206S500-2

    query = '''(SELECT `Footprint Ref`, MAX(`Footprint Path`), MAX(`PackageDescription`)
                FROM Semiconductors
                WHERE `Case` LIKE ?
                GROUP BY `Footprint Ref`)
              UNION
               (SELECT `Footprint Ref`, MAX(`Footprint Path`), MAX(`PackageDescription`)
                FROM Passives
                WHERE `Case` LIKE ?
                GROUP BY `Footprint Ref`)
              UNION
               (SELECT `Footprint Ref`, MAX(`Footprint Path`), MAX(`PackageDescription`)
                FROM Electromechanical
                WHERE `Case` LIKE ?
                GROUP BY `Footprint Ref`)'''               
    # MAX() functions use only as workaround for MS Access query restrictions.
    # With SQLite this is no effect.
    
    if mydb['Case']:
        findkey = ('%' + mydb['Case'] + '%', '%' + mydb['Case'] + '%', '%' + mydb['Case'] + '%')
        cursor.execute(query, findkey)
        options = cursor.fetchall()
        if options:
            if options[0][0]: # Workaround when MS Access give [(None, None, None)] if keyword not found
                choice_item = selection(options, 'Package options', cutColoumn=2)
                if choice_item:
                    mydb['Footprint'] = choice_item[0]
                    mydb['Footprint_Path'] = choice_item[1]
                    mydb['Footprint_Ref'] = choice_item[0]
                    mydb['PackageDescription'] = choice_item[2]
                else:
                    return
            else:
               print('Not found such package in DB Lib') 
        else:
            print('Not found such package in DB Lib')
    else:
        print('\'Case\' field is empty')


def datasheet(mydb, octo):
    print()
    options = octo['Datasheets']

    # TODO: Fix mess with the cossing (y,n)...

    if options:
        tableprint(options, 1, tableName='Datasheet', itemize=0)
        is_fit = 'n'
        while is_fit != 'y':
            choice_word = input('Your decision (number): ')
            try:
                choice_index = int(choice_word)
                subprocess.Popen([config.pdf_viewer, options[choice_index][1]])
            except:
                print('No such option')

            is_fit = input('Is it datasheet fit? (y,n): ')

        path = 'C:\\Datasheets\\' + mydb['Component_Kind'] + '\\'
        if mydb['Table']:
            path += mydb['Table']
        else:
            path += 'Unsorted'

        if not os.path.exists(path):
            os.makedirs(path)
        
        filename = mydb['Part_Number']
        illegals = ('\\', '/', ':', '*', '?', '\'', '\"', '<', '>', '|', '.', ',')
        for sym in illegals:
            filename = filename.replace(sym, ' ')

        path += '\\' + filename + '.pdf'

        # Fix 'HTTP Error 403' from https://stackoverflow.com/a/36663971
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        print('Downloading...')
        try:
            urllib.request.urlretrieve(options[choice_index][1], path)
        except Exception as e:
            print('Download failed.', e)
        else:
            print('Download successful')
            mydb['HelpURL'] = path
    else:
        print('Datasheets not found')
    

