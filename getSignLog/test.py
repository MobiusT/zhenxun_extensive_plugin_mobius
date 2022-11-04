import os

LOG_PATH =  os.path.join(os.path.dirname(__file__), "log/sign.log")

logFile = open(LOG_PATH,'r')
try:
    log = logFile.read()
    print (log)
    print (log.replace('\n','\\n'))
finally:
    logFile.close()



