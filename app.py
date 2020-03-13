from flask import Flask, render_template, request, send_from_directory, flash, redirect, session, abort
from flask_socketio import SocketIO, send, emit
from flask_socketio import ConnectionRefusedError

import os
import socket
import sys
import time
import threading 
import subprocess
import eventlet
eventlet.monkey_patch()

gShutdownFlag = False
gApp_path =os.path.join(os.path.dirname(os.path.realpath(__file__)),'./website/')

app = Flask("LogStream",  root_path=gApp_path)
socketio = SocketIO(app)

@app.route('/')
def home():
    return redirect("/site/LogStream", code=302)
	
@app.route('/site/<path:path>')
def send_site(path):
    return send_from_directory('site', path + "/index.html")

@app.route('/script/<path:path>')
def send_script(path):
    return send_from_directory('site', path)
	
@app.route('/shutdown')
def start_shutdown():
    global gShutdownFlag
    gShutdownFlag = True
    return "<script>window.close();</script>"

@socketio.on('connect')
def socket_connect():
    print("New Connection")
    return "Connected"

@socketio.on('disconnect')
def socket_disconnect():
    print('Client disconnected')

def Flask_Thread(iPort):
    app.secret_key = os.urandom(12)
    port = int(iPort)
    socketio.run(app, host='0.0.0.0', port=port, debug=False)


def Logger_Thread(iPort, iDirectory, iRecursive,iExtension):

    out = subprocess.Popen(["start", "chrome", "-incognito", "http://localhost:{}/".format(iPort)], 
           stdout=subprocess.DEVNULL, 
           stderr=subprocess.DEVNULL,
           shell=True)
    

    wLogDirectory = os.path.abspath(iDirectory)

    if False == os.path.exists(wLogDirectory):
        print("Input Directory [{}] does not exist".format(wLogDirectory))
        print("Exiting Software")
        time.sleep(10)
        return
    else:
        print("Streaming logs from directory [{}]".format(wLogDirectory))

    wMonitoredFileList = {}
    
    for (dirpath, dirnames, wDirfilenames) in os.walk(wLogDirectory):
       
        for wFileName in wDirfilenames:
            wFullName = os.path.join(dirpath, wFileName)
            name, extension = os.path.splitext(wFileName)                
            if extension  in iExtension:
                if wFullName not in wMonitoredFileList:
                    
                    wLineCount = 0
                    wFile = open(wFullName,"r")
                    if wFile.mode == 'r':
                        wLines = wFile.readlines()
                        wLineCount = len(wLines)
                    wFile.close() 

                    wFileHandle = {}
                    wFileHandle["Name"] = wFileName
                    wFileHandle["FullPath"] = wFullName
                    wFileHandle["CurrentLine"] = 0
                    if wLineCount >= 1:
                        wFileHandle["CurrentLine"] = wLineCount - 1
                    wMonitoredFileList[wFullName] = wFileHandle
                    print("Adding file {}".format(wFileHandle))

        if False == iRecursive:
            break

    while False == gShutdownFlag:
        
        for (dirpath, dirnames, wDirfilenames) in os.walk(wLogDirectory):
           
            for wFileName in wDirfilenames:
                wFullName = os.path.join(dirpath, wFileName)
                name, extension = os.path.splitext(wFileName)                
                if extension  in iExtension:
                    if wFullName not in wMonitoredFileList:
                        wFileHandle = {}
                        wFileHandle["Name"] = wFileName
                        wFileHandle["FullPath"] = wFullName
                        wFileHandle["CurrentLine"] = 0
                        wMonitoredFileList[wFullName] = wFileHandle
                        print("Adding file {}".format(wFileHandle))

            if False == iRecursive:
                break

        wDeletedFiles = []
        for wKey, wValue in wMonitoredFileList.items():
            if  False == os.path.exists(wKey):
                wDeletedFiles.append(wKey)
                continue
            wFileName = wValue["Name"]
            wFile = open(wKey,"r")
            if wFile.mode == 'r':
                wLines = wFile.readlines()
                while wValue["CurrentLine"] < len(wLines):
                    wIndex = wValue["CurrentLine"]
                    NewMessage = {}
                    NewMessage["FileName"] = wFileName
                    NewMessage["FullPath"] = wKey
                    NewMessage["Line"] = wIndex+1
                    NewMessage["Log"] = wLines[wIndex]
                    socketio.emit('Send Log', NewMessage, json = True, broadcast=True)
                    wIndex += 1
                    wValue["CurrentLine"] = wIndex

            wFile.close() 


        for wKey in wDeletedFiles:
            print("Log File deleted {}".format(wValue["Name"]))
            del wMonitoredFileList[wKey]

        time.sleep(1)



def main():	

    wPort = int(os.environ.get('PORT', 2000))
    wSearchDirectory = ".\\"
    wExtensionList = [".txt",".log"]
        
    wRecursive = False
    
    wi = 1
    while wi < len(sys.argv):
        print(sys.argv[wi])
        if "-port" == sys.argv[wi]:
            wi+=1
            if(wi < len(sys.argv)):
                wPort = sys.argv[wi]
        elif "-dir" == sys.argv[wi]:
            wi+=1
            if(wi < len(sys.argv)):
                wSearchDirectory = sys.argv[wi]
        elif "-r" == sys.argv[wi]:
            wRecursive = True
        else:
            if sys.argv[wi] not in  wExtensionList:
                wExtensionList.append(sys.argv[wi])
        wi+=1

    # creating thread 
    wThread_Flask = threading.Thread(target=Flask_Thread, args=(wPort,)) 
    wThread_Logger = threading.Thread(target=Logger_Thread, args=(wPort,wSearchDirectory, wRecursive,wExtensionList)) 

    # Daemon Setup
    wThread_Flask.setDaemon(True)
    
    #starting thread 
    wThread_Flask.start() 
    wThread_Logger.start()
  
    # wait for thread completion
    wThread_Logger.join() 
    wThread_Flask.join(0.1) 

    # Completion
    print("Bye!") 
    sys.exit()


if __name__ == '__main__':
    main()