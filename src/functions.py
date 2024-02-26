import sqlite3 as sl
import json
import os
# import shutil
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

import requests


def createDataFolder():
    data = '/app/data/'
    if not os.path.exists(data):
        os.makedirs(data)
    return True

def uri_validator(x):
    try:
        result = requests.head(x)
        return result.status_code
    except:
        return 0

def createDataStoriesDB():
    data = '/app/data'
    # if not os.path.exists(data):
    #     os.makedirs(data)

    con = sl.connect(data + '/datastories.db')
    cur = con.cursor()   
    cur.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                status TEXT DEFAULT 'draft',
                owner TEXT,
                filename TEXT,
                created TEXT,
                modified TEXT,
                store TEXT,
                title TEXT
            );
        """) 
    con.commit()
    cur.close()
    con.close()    


def getDataStoriesDB():
    data = '/app/data'
    con = sl.connect(data + '/datastories.db')
    cur = con.cursor()   
    sql = "SELECT uuid, title, status, created, modified, owner, groep FROM stories"
    cur.execute(sql)
    names = list(map(lambda x: x[0], cur.description)) # ergens opgezocht
    # print('names', names)
    result = cur.fetchall()

    cur.close()
    con.close()

    print('result', result)
    struct = []
    for x in result:
        # print('x', x[1])
        # id = x[1]
        # structure.append({'uuid': id})
        row = {}
        # namen in het resultaat plakken y is een rangnummer in de namenlijst
        for y in range(0, len(names)):
            key = names[y]
            value = x[y]
            row[key] = value
            # s.append({key: value})
            
        struct.append(row)
    print('struct', struct)
    return struct


def getListUUIDs():
    data = '/app/data'
    con = sl.connect(data + '/datastories.db')
    cur = con.cursor()   
    sql = "SELECT uuid FROM stories"
    cur.execute(sql)
    result = cur.fetchall() # list of tuples
    res = [ele[0] for ele in result] # list comprehension 
    print('result', res)
    
    cur.close()
    con.close()

    return list(res)



def tooManyStories(max):
    data = '/app/data/'
 
    count = len(os.listdir(data))
    print('aantal dirs', count)
    if(count > max):
        return True
    else:
        return False

def getNewId():
    # maakt gebruik van een sql lite database voor gegarandeerde oplopende unieke ids 
    datadir = '/app/data'
    unique_id = str(uuid.uuid4()) # kan misschien ook als database functie
    status = 'draft' # dubbelop?
    title = '[UNTITLED]'
    now = datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    created = now.strftime("%Y-%m-%d %H:%M:%S")    # creation timestamp
    print('datestring',created)
    # YYYY-MM-DD hh:mm:ss' 

    # datum = 
    # print('ideetje', ideetje)
    con = sl.connect(datadir + '/datastories.db')
    cur = con.cursor()   

    sql = "INSERT INTO stories (status, uuid, owner, title, groep, created, modified) values(?, ?, ?, ?, ?, datetime('now'), datetime('now'))"
    value = ('D', unique_id, 'Rob Zeeman', title, 'HuC')

    cur.execute(sql, value)
    con.commit()
    # id = con.lastrowid #werkt niet bij deze versie van sqllite
    res = cur.execute("SELECT last_insert_rowid()")
    con.commit()
    id = res.fetchone()
    unique_id = id[0]
    sql = 'SELECT id, uuid FROM stories WHERE id = ? '
    value = [unique_id]        
    cur.execute(sql, value)
    con.commit()
    result = res.fetchall()

    cur.close()
    con.close()

    # print('result', result)
    return result[0][1]

def createDataStoryFolder(id, template):
    # misschien ook een eens hiernaar kijken https://stackoverflow.com/questions/273192/how-do-i-create-a-directory-and-any-missing-parent-directories
    # os.path kan wel eens misgaan begrijp ik
    data = '/app/data/'
    createDataFolder()
    directory = data + str(id)
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.makedirs(directory + '/resources/images/')
        os.makedirs(directory + '/resources/audio/')
        os.makedirs(directory + '/resources/video/')
        saveDataStory(id, template)

    return True

def deleteDataStoryFolder(uuid):
    data = '/app/data/'
    directory = data + str(uuid)
    if os.path.exists(directory):
        # os.removedir
        shutil.rmtree(directory)
        return True
    else:
        return False    
    

def removeFromDB(uuid):
    con = sl.connect('data/datastories.db')
    cur = con.cursor()
    sql = 'DELETE FROM stories WHERE uuid = ? LIMIT 1 '
    cur.execute(sql, (uuid,))
    con.commit()

    cur.close()
    con.close()

    return True

def updateModifiedDate(unique_id, title):
    datadir = '/app/data'
    now = datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    modified = now.strftime("%Y-%m-%d %H:%M:%S")    # creation timestamp
    con = sl.connect(datadir + '/datastories.db')
    cur = con.cursor()   
    sql = 'UPDATE stories SET title = ?, modified = ? WHERE uuid = ? LIMIT 1 '
    value = (title, modified, unique_id)
    cur.execute(sql, value)
    con.commit()
    # best practice https://stackoverflow.com/questions/5504340/python-mysqldb-connection-close-vs-cursor-close
    cur.close()
    con.close()
  
    

def fs_tree_to_dict(path_):
    file_token = ''
    for root, dirs, files in os.walk(path_):
        tree = {d: fs_tree_to_dict(os.path.join(root, d)) for d in dirs}
        tree.update({f: file_token for f in files})
        return tree  # note we discontinue iteration trough os.walk

# https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
# Mikaelblomkvistsson's antwoord bijna onderaan, dit is de meest flexibele m.i. maar ik snap hem niet echt, nu geen tijd



def getDataStory(uuid):
    data = '/app/data/'
    directory = data + str(uuid) # misschien niet meer nodig
    filename = directory + '/datastory.json'
    datastory = {}
    if os.path.exists(filename):
        with open(filename) as json_file:
            datastory = json.load(json_file)
    return datastory

def saveDataStory(datastory_id, datastory):
    path = "/app/data/" + str(datastory_id) + "/datastory.json"

    with open(path, 'w') as f:
        json.dump(datastory, f)
