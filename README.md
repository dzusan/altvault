## AltVault - An Alternative Altium Vault

Python scripts to servise large DBLib. DataBase based on CERN library and
contains about 7500 components.

Can operate with:
* Microsoft Access 2000-2003 (*.mdb, 32-bit)
* Microsoft Access 2007-2016 (*.mdb, *.accdb, 32-bit, 64-bit)
* SQLite3

**Microsoft Access 64-bit (.accdb)** is preferable because it works properly
with Altium Designer 18.

**Copy `config.py.example` to `config.py` for proper operation! And only then
change settings in file or replace them by command line.**

### A little demo

![A little demo](demo.gif?raw=true "demo.gif")

### Launch without keys (completed config.py)

```
path\to\create_component.py
^
script
```

### Launch with keys (replace config.py)

```
path\to\create_component.py path\to\altvault.db 12345678 stm32f100c
^                           ^                   ^        ^
script                      data base           apikey   prefill search
```

### DB must contain
* Table `components`
* At least one row
* Following columns with data type varchar255:
    * Part Number [Primary Key]
    * Library Ref
    * Library Path
    * Comment
    * Component Kind
    * Component Type
    * Footprint
    * Pin Count
    * Case
    * Footprint Path
    * Footprint Ref
    * PackageDescription
    * Device
    * Mounted
    * Socket
    * SMD
    * Status
    * Color
    * Part Description
    * Manufacturer
    * Manufacturer Part Number
    * ComponentHeight
    * Manufacturer1 Example
    * Manufacturer1 Part Number
    * Manufacturer1 ComponentHeight
    * HelpURL
    * ComponentLink1URL
    * ComponentLink1Description
    * ComponentLink2URL
    * ComponentLink2Description
    * Author
    * CreateDate
    * LatestRevisionDate
    * Table
    * Sim Model Name
    * Sim File
    * Sim SubKind
    * Sim Netlist
    * Sim Spice Prefix
    * Sim Port Map
    * Resistanse
    * Value
    * TC
    * Power
    * Tolerance
    * Voltage

