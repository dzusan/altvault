import os
import sqlite3
from datetime import datetime
import subprocess
import urllib

# User
import config
from markup import *

def spec(mydb, octo):
    # Independed fields
    mydb['Part_Number'] = octo['Part Number']
    mydb['Mounted'] = 'Yes'
    mydb['Part_Description'] = octo['Part Description']
    mydb['Manufacturer'] = octo['Manufacturer'].upper()
    mydb['Manufacturer_Part_Number'] = octo['Part Number']
    mydb['Author'] = config.author
    mydb['CreateDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mydb['LatestRevisionDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')     

    # Optional fields
    mydb['Pin_Count'] = octo['<Number of Pins>']    if '<Number of Pins>'   in octo.keys() else None
    mydb['Status']    = octo['<Lifecycle Status>']  if '<Lifecycle Status>' in octo.keys() else None
    if '<Mounting Style>' in octo.keys():
        if octo['<Mounting Style>'] == 'Surface Mount':
            mydb['SMD'] = 'Yes'
        else:
            mydb['SMD'] = 'No'
    else:
        mydb['SMD'] = None
    
    # ??? fields
    mydb['Component_Kind'] = 'Standard'
    mydb['Component_Type'] = 'Standard'

    

def subclass(mydb, octo):
    if 'Passive Components' in octo['Categories']:
        mydb['Comment'] = '=Value'
        mydb['Case'] = octo['<Case/Package>'] if '<Case/Package>' in octo.keys() else None
        mydb['Sim_Netlist'] = '@DESIGNATOR %1 %2 @VALUE'
        mydb['Voltage'] = octo['<Voltage Rating (DC)>'] if '<Voltage Rating (DC)>' in octo.keys() else None

    if 'Integrated Circuits (ICs)' in octo['Categories']:
        mydb['Comment'] = '=Device'
        mydb['Device'] = octo['Part Number']
        if '<Case/Package>' in octo.keys():
            if '<Number of Pins>' in octo.keys():
                mydb['Case'] = octo['<Case/Package>'] + octo['<Number of Pins>']
            else:
                mydb['Case'] = octo['<Case/Package>']
        else:
            mydb['Case'] = None

    if 'Capacitors' in octo['Categories']:
        mydb['Library_Path'] = 'SchLib\\Capacitors.SchLib'
        mydb['Table'] = 'Capacitors'
        mydb['Sim_Model_Name'] = 'CAP'
        mydb['Sim_SubKind'] = 'Capacitor'
        mydb['Sim_Spice_Prefix'] = 'C'
        if '<Capacitance>' in octo.keys():
            value = octo['<Capacitance>']
            value = value.replace(' ', '')
            value = value.replace('F', '')
            value = value.replace('µ', 'u')
            mydb['Value'] = value
        else:
            mydb['Value'] = None
        mydb['Tolerance'] = octo['<Capacitance Tolerance>']  if '<Capacitance Tolerance>' in octo.keys() else None
    
    if 'Resistors' in octo['Categories']:
        mydb['Library_Path'] = 'SchLib\\Resistors.SchLib'
        mydb['Table'] = 'Resistors'
        mydb['Sim_Model_Name'] = 'RES'
        mydb['Sim_SubKind'] = 'Resistor'        
        mydb['Sim_Spice_Prefix'] = 'R'
        if '<Resistance>' in octo.keys():
            value = octo['<Resistance>']
            value = value.upper()
            value = value.replace(' ', '')
            value = value.replace('Ω', '')
            value = value.replace('M', 'Meg')
            mydb['Value'] = value
        else:
            mydb['Value'] = None
        mydb['Tolerance'] = octo['<Resistance Tolerance>'] if '<Resistance Tolerance>' in octo.keys() else None
        if '<Resistance Tolerance>' in octo.keys():
            if octo['<Resistance Tolerance>'] == '±0.1%':
                mydb['Library_Ref'] = 'Resistor - 0.1%'
            elif octo['<Resistance Tolerance>'] == '±1%':
                mydb['Library_Ref'] = 'Resistor - 1%'
            elif octo['<Resistance Tolerance>'] == '±5%':
                mydb['Library_Ref'] = 'Resistor - 5%'
        else:
            mydb['Library_Ref'] = None

    if 'Ceramic Capacitors' in octo['Categories']:
        mydb['Library_Ref'] = 'Capacitor - non polarized'
        mydb['TC'] = octo['<Dielectric Characteristic>'] if '<Dielectric Characteristic>' in octo.keys() else None

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



def footprint(mydb, conn, cursor):
    query = '''SELECT `Footprint Ref`, MAX(`Footprint Path`), MAX(`PackageDescription`)
               FROM components
               WHERE `Case` LIKE ?
               GROUP BY `Footprint Ref`'''
    # MAX() functions use only as workaround for MS Access query restrictions.
    # With SQLite this is no effect.
    
    if mydb['Case']:
        findkey = ('%' + mydb['Case'] + '%',)
        cursor.execute(query, findkey)
        options = cursor.fetchall()
        if options:
            if options[0][0]: # Workaround when MS Access give [(None, None, None)] if keyword not found
                tableprint(options, 2, tableName='Package options', itemize=0)
                choice_word = input('Your decision (number): ')
                try:
                    choice_index = int(choice_word)
                    print('You choose {} ({})'.format(options[choice_index][0], options[choice_index][2]))
                    mydb['Footprint'] = options[choice_index][0]
                    mydb['Footprint_Path'] = options[choice_index][1]
                    mydb['Footprint_Ref'] = options[choice_index][0]
                    mydb['PackageDescription'] = options[choice_index][2]
                except:
                    print('No such option')
            else:
               print('Not found such package in DB Lib') 
        else:
            print('Not found such package in DB Lib')
    else:
        print('No \'Case\' field')


def datasheet(mydb, octo):
    options = octo['Datasheets']

    if options:
        tableprint(options, 1, tableName='Datasheet options', itemize=0)
        is_fit = 'n'
        while is_fit != 'y':
            choice_word = input('Your decision (number): ')
            try:
                choice_index = int(choice_word)
                subprocess.Popen([config.pdf_viewer, options[choice_index][1]])
            except:
                print('No such option')

            is_fit = input('Is it datasheet fit? (y,n): ')

        path = 'C:\\Datasheets\\'
        if mydb['Table']:
            path += mydb['Table']
        else:
            path += 'Unsorted'

        if not os.path.exists(path):
            os.makedirs(path)
        
        filename = mydb['Part_Number']
        illegals = ('\\', '/', ':', '*', '?', '\'', '\"', '<', '>', '|', '_', '.', ',')
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
    

