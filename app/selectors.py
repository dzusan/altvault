import os
import config

def author():
    illegals = ('Datasheets', 'History')
    glob_path = os.path.dirname(config.DB_path)
    authors = [(name, name) for name in os.listdir(glob_path) 
               if os.path.isdir(glob_path + '\\' + name)
               and name not in illegals]
    
    return authors
