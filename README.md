## AltVault - An Alternative Altium Vault

Python scripts to servise large DBLib. DataBase based on CERN library converted to SQLite3 and contains about 7500 components.

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
