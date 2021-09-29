import os
import sys
from datetime import datetime
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from app.db_connector import db_connect, db_disconnect

def isnum(num):
    if isinstance(num, str):
        return num.replace('.','',1).isdigit()
    else:
        return False

def res_yageo():
    conn, cur = db_connect()
    cur.execute('''SELECT `Part Number`, `Manufacturer Part Number`
                        FROM Passives
                        WHERE `Table` LIKE \'%Resistors SMD%\'''')

    total = 0
    success = 0

    for item in cur.fetchall():
        pn = '--'
        if item[0] == item[1]:
            total += 1
            parm = item[0].split('_')

            if parm is not None:
                if len(parm) >= 5:
                    # R0805_1M24_1%_0.125W_200PPM
                    case  = parm[0][1:]
                    val   = parm[1]
                    power = parm[3]
                    drift = parm[4]

                    if parm[2] == '0.1%':
                        tol = 'F'
                        # tol = 'B' # Not present in Yageo products
                    elif parm[2] == '0.5%':
                        tol = 'F'
                        # tol = 'D' # Not present in Yageo products
                    elif parm[2] == '1%':
                        tol = 'F'
                    elif parm[2] == '5%':
                        tol = 'J'
                    else:
                        continue

                    pn = 'RC{}{}R-07{}L'.format(case, tol, val) # RC0805FR-074K99L
                    success += 1

                    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    upd_query = 'UPDATE Passives SET `Manufacturer1 Example` = ?, `Manufacturer1 Part Number` = ?, `LatestRevisionDate` = ? WHERE `Part Number` LIKE ?'
                    # print('YAGEO', pn, dt, item[0])
                    cur.execute(upd_query, ('YAGEO', pn, dt, item[0]))

        # print(item[0], ' : ', item[1], ' : ', pn)
    print('Total:', total, ', Success:', success)

    conn.commit()
    db_disconnect(conn, cur)
    return True

def cap_yageo():
    conn, cur = db_connect()
    cur.execute('''SELECT `Part Number`, `Manufacturer Part Number`
                        FROM Passives
                        WHERE `Table` LIKE \'%Capacitors SMD%\'''')

    total = 0
    success = 0
    case_lst = ['CC0201', 'CC0402', 'CC0603', 'CC0805', 'CC1206', 'CC1210', 'CC1812']

    for item in cur.fetchall():
        pn = '--'
        if item[0] == item[1] and item[0][:2] == 'CC':
            total += 1
            sgn = 0
            pack = 'R'
            parm = item[0].split('_')

            if parm is not None:
                if len(parm) >= 5:
                    # CC0805_1UF_25V_10%_X7R
                    
                    diel  = parm[4]                    
                    case  = parm[0]
                    if (   (diel == 'X7R' and case not in case_lst)
                        or (diel == 'X5R' and case not in case_lst[:-1])
                        or (diel not in ['X7R', 'X5R'])):
                        continue

                    # 0201 .. 1206
                    # if THICKNESS > 0.85 => blister (K)
                    # 0805 - EB
                    # 1206 - F1, FA, FC, FD
                    # 1210 .. 1812
                    # blister only (K)

                    if case in ['CC1210', 'CC1812']:
                        pack = 'K'
                    
                    origval   = parm[1][:-2]
                    if isnum(origval):
                        sgn = float(origval)
                        if parm[1][-2] == 'P':
                            if sgn >= 100.0:
                                val = str(int(sgn / 10)) + '1'
                            else:
                                continue
                        
                        elif parm[1][-2] == 'N':
                            if case == 'CC0805':
                                if (parm[2] == '50V' and origval == '220') or (sgn > 220.0):
                                    pack = 'K'
                            
                            if diel == 'X5R' and parm[3] == '20%' and sgn > 220.0:
                                continue                            

                            if sgn < 10.0:
                                val = str(int(sgn * 10)) + '2'
                            elif sgn < 100.0:
                                val = str(int(sgn)) + '3'
                            else:
                                val = str(int(sgn / 10)) + '4'
                        
                        elif parm[1][-2] == 'U' and parm[3] != '5%':
                            if case == 'CC0805':
                                pack = 'K'

                            if sgn < 10.0:
                                val = str(int(sgn * 10)) + '5'
                            elif sgn < 100.0:
                                val = str(int(sgn)) + '6'
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                    
                    if parm[2] == '6.3V':
                        vol = '5'
                    elif parm[2] == '10V':
                        vol = '6'
                    elif parm[2] == '16V':
                        if case == 'CC0201' and diel == 'X5R':
                            continue
                        else:
                            vol = '7'
                    elif parm[2] == '25V':
                        vol = '8'
                    elif parm[2] == '50V':
                        vol = '9'
                    else:
                        continue

                    if parm[3] == '5%':
                        tol = 'J'
                    elif parm[3] == '10%':
                        tol = 'K'
                    elif parm[3] == '20%':
                        tol = 'M'
                    else:
                        continue

                    pn = '{}{}{}{}{}BB{}'.format(case, tol, pack, diel, vol, val) # CC0805KRX7R9BB102
                    success += 1

                    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    upd_query = 'UPDATE Passives SET `Manufacturer1 Example` = ?, `Manufacturer1 Part Number` = ?, `LatestRevisionDate` = ? WHERE `Part Number` LIKE ?'
                    # print('YAGEO', pn, dt, item[0])
                    cur.execute(upd_query, ('YAGEO', pn, dt, item[0]))

    print('Total:', total, ', Success:', success)

    conn.commit()
    db_disconnect(conn, cur)
    return True

if __name__ == '__main__':
    # res_yageo()
    cap_yageo()
