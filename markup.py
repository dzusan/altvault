import sys
import win32com.client as win
from terminaltables import AsciiTable

def fillinput(prompt, default=""):
    win.Dispatch("WScript.Shell").SendKeys(default)
    return input(prompt)

def errprint(*args, **kwargs):
    print("\x1b[1;31;40mERROR: ", end="")
    print(*args, end="", **kwargs)
    print("\x1b[0m")

def progressMarker(flag):
    if flag[0] == True:
        sys.stdout.write("\b|")
        flag[0] = False
    else:
        sys.stdout.write("\b-")
        flag[0] = True
    sys.stdout.flush()

def tableprint(noModifydata, cutColoumn, tableName = '', itemize=-1, initCol=0, lastCol = 10):
    MAX_TABLE_WIDTH = 80
    minCol = int(MAX_TABLE_WIDTH / 5)

    data = []
    # Copy all input data to local list
    # Convert to mutable type - list
    # And cut coloumns if needed
    for i, row in enumerate(noModifydata):
        data.append(list(row[initCol:(lastCol+1)]))

    # If selection table
    if itemize >= 0:
        tableName = 'Select ' + tableName[:MAX_TABLE_WIDTH - 10]
        # Add item number if needed
        cutColoumn += 1
        for row in data:
            row.insert(0, itemize)
            itemize += 1
    else:
        tableName = tableName[:MAX_TABLE_WIDTH - 3]

    table = AsciiTable(data, title = tableName)
    width = table.table_width

    if width > MAX_TABLE_WIDTH:
        maxCol = table.column_widths[cutColoumn] - (width - MAX_TABLE_WIDTH)
        maxCol = minCol if maxCol < minCol else maxCol
        for i, row in enumerate(data):
            row = list(row)
            # Cutting row if needed
            if row[cutColoumn] == None:
                row[cutColoumn] = '------'
            elif len(row[cutColoumn]) > maxCol:
                row[cutColoumn] = row[cutColoumn][:maxCol-4] + '... '
            else:
                pass            
            data[i] = row
        table = AsciiTable(data, title = tableName)

    table.inner_heading_row_border = False
    print(table.table)


def selection(options, selectionName, cutColoumn = 1):
    noModifydata = []
    if len(options[0][0]) == 1:
        for item in options:
            noModifydata.append((item,))
    else:
        noModifydata = options

    print()
    tableprint(noModifydata, cutColoumn, tableName=selectionName, itemize=1)
    
    choice_index = 0
    while True:
        choice_word = fillinput('Your decision (number): ', '1')        
        try:
            choice_index = int(choice_word)
            if choice_index > 0:
                # This solution in 'try' also able to ignore fractional numbers
                choise_item = noModifydata[choice_index - 1] 
        except:
            print('No such option')
        else:
            print('Your choice:')
            for col in noModifydata[choice_index - 1]:
                print(col)
            print()
            return options[choice_index - 1]
            