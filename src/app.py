from flask import Flask, request, jsonify, send_file, jsonify, abort
import json
import requests
import random
import sqlite3 as sl
import os
from os.path import isfile, join, exists
from werkzeug.utils import secure_filename
from ds_template import template


from functions import (
    getNewId, createDataStoryFolder, removeFromDB, 
    deleteDataStoryFolder,getDataStory, fs_tree_to_dict,
    tooManyStories, createDataFolder, createDataStoriesDB, getDataStoriesDB,
    getListUUIDs, updateModifiedDate, saveDataStory, uri_validator
)
# https://peps.python.org/pep-0328/#rationale-for-parentheses


app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = '/data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



# wordt maar 1 keer gedaan na het opstarten
@app.before_first_request
def before_first_request():
    # datafolder aanmaken
    print('initialisatie')
    createDataFolder()
    createDataStoriesDB()
    # app.logger.info("before_first_request")



@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.route("/")
def hello_world():
    retStruc = {"app": "Data Stories Slurf=", "version": "0.1"}
    # jsonHeaders(response)
    return jsonify(retStruc)

@app.route("/check_url", methods=['POST'])
def check_url():
    data = request.json
    url = data.get("url")
    result = uri_validator(url)
    return jsonify({"status": result})


@app.route("/create_new")
def create_new():
    status = 'OK'
    max = 100 # maximaal 100 datastories
    if tooManyStories(max):
        response = {"status": 'ff aan de rem getrokken'}
        return jsonify(response)        

    id = getNewId()
    status = createDataStoryFolder(id, template)
    if status == True:
        # stringie = 'I created something new! De unieke id is: ' + str(id)
        response = {"datastory_id": id}
        return jsonify(response)

@app.route("/delete" , methods=['GET'])
def delete():
    status = 'OK'
    id = request.args.get("ds")
    if deleteDataStoryFolder(id):
        status = 'OK' 
    else: 
        status = 'DATASTORY NOT FOUND'  

    removeFromDB(id) # nog even goed naar kijken of dit nu klopt 
    response = {"status": status}
    return jsonify(response)

# datastory is de inhoud van de json file, ik hoef geen structuur te parsen
@app.route("/get_item", methods=['GET'] )
def get_item():
    status = ''
    datastory = {}
    uuid = request.args.get("ds")
    #print('uuid', uuid)
    if not uuid:
        status = 'INVALID REQUEST, NO UUID'
        
    else:    
        datastory = getDataStory(uuid) # kan empty zijn
        status = 'OK'

    #print('ds', datastory)
    response = {"status": status, "datastory": datastory}
    return jsonify(datastory)


# hier moet de sqllite database bevraagd worden, om de lijstpagina te genereren
@app.route("/get_data_stories")
def getDataStories():
    structure = {'message': 'nothing yet'}
    # data = 'data/'
    status = 'OK'
    # structure = fs_tree_to_dict(data)
    # print(structure)
    structure = getDataStoriesDB()

    response = {"status": status, "structure": structure}
    return jsonify(response)


@app.route("/update_datastory", methods=['POST'])
def updateDataStory():
    data = request.json

    datastory_id = data.get('datastory_id')
    datastory_title = data.get('datastory_title')
    datastory = data.get('datastory')

    # save the content to file
    #path = "data/" + str(datastory_id) + "/datastory.json"

    #with open(path, 'w') as f:
    #    json.dump(datastory, f)
    saveDataStory(datastory_id, datastory)


    updateModifiedDate(datastory_id, datastory_title)

    return jsonify({"status": "OK"});

# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# def allowed_file(filename):
# 	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods = ['POST', 'OPTIONS']) 
def upload(): #uploaded file from js / react
    # print('request', request)
    # print('request.files: ', request.files)
    # print('request.headers: ', request.headers)
    # print('request.args: ', request.args)
    # print('request.form: ', request.form)
    # print('request.endpoint: ', request.endpoint)
    # print('request.method: ', request.method)
    # print('request.remote_addr: ', request.remote_addr)
    # uuid = '6a4a58a2-8777-4cbe-896c-85049a928768' #test
    if not request.files:
        print("No file")
        return jsonify('No file')
    
    if not 'file' in request.files:
        print('No filename <file> in request')
        return jsonify('No filename <file> in request')    

    if not request.form.get('uuid'):
        print('No uuid')
        return jsonify('No uuid')
    


    uuid = request.form.get('uuid') # unique identifier of the data story
    #print("request.form.get('uuid')", uuid)
    listUUIDS = getListUUIDs()
    # print(listUUIDS)
    if not uuid in listUUIDS:
        # print('zit er niet in')
        return jsonify('uuid not available')



    uploaded_file = request.files['file'] # this is a datastorage object, not the data itself
    filename =  request.files['file'].filename

    #print("request.files['file'].filename: ", request.files['file'].filename)
    #print("request.files['file'].content_type: ", request.files['file'].content_type)

    # filename = uploaded_file.filename
    content_type = request.files['file'].content_type
    
    resources = "/app/data/" + uuid + '/resources' # centraal definieren

    if content_type.startswith('image'):
        store = resources + '/images/'
    elif content_type.startswith('audio'):        
        store = resources + '/audio/'
    elif content_type.startswith('video'):    
        store = resources + '/video/'
    else:
        jsonify('Go Home!')
        # exit()
        
    # https://tedboy.github.io/flask/generated/generated/werkzeug.FileStorage.html

    filepath = store + filename
    data = uploaded_file.read() # je moet de bytes readen uit een DataStorage Object
    with open(filepath, 'ab') as f:
         f.write(data)

    if exists(filepath):
        status = "OK"
    else:
        status = "NOT OK"  

    return jsonify(status)

@app.route('/<uuid>/<resourcetype>/<filename>', methods = ['GET']) 
def resources(uuid, resourcetype, filename):
    # we can severe the api from the real path, safer I think
    # TODO checks and balances maybe 

    filepath = '/app/data/' + uuid + '/resources/' + resourcetype + '/' + filename
    # TODO mime-types? Or does send_file this..
    try:
        return send_file(filepath)
    except FileNotFoundError:
        abort(404)
    
    # # read from file serve right mimetype
    # print(filepath)
    # status = 'OK'
    # return json.dumps(status)


#Start main program

if __name__ == '__main__':
    app.run()

