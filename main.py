import os.path
import sqlite3
from datetime import *

import summary

LOGS_FROM_DAYS = -1  # Go back X amount of days
LOGDIRECTORY = "//DCVM-WEB/c$/inetpub/logs/LogFiles/W3SVC1/"
DTSTRING = datetime.now().strftime("%y%m%d")
CONNECTIONSTRING = os.path.realpath(r"\Users\chollinger\iisparser") + "\\" + DTSTRING + str(datetime.now().second) + ".db"

connection = sqlite3.connect(CONNECTIONSTRING)  # TODO holy crap lol this sucks
connection.execute("CREATE TABLE logtable (dt TEXT, uri TEXT, status INTEGER, timereq INTEGER);")

currentdate = datetime.now()
filenames = []

# Create filenames for the log files to be loaded
i = 0
while i > LOGS_FROM_DAYS:
    dt = datetime.now() + timedelta(days=i)
    filenames.append(os.path.join(LOGDIRECTORY, ("u_ex%s_x.log" % dt.strftime("%y%m%d"))))
    i -= 1
del i

filenames.reverse()  # Reverse so the oldest logs are displayed last

cursor = connection.cursor()

for filename in filenames:
    try:
        print("Opening " + filename + "...")
        file = open(filename)
        lines = file.readlines()

        for line in lines:
            if line.startswith('#'):
                continue

            values = line.split(' ')
            sqlcommand = ("""INSERT INTO logtable VALUES("%s", "%s", %s, %s);""" %
                          (values[0] + " " + values[1], values[4], values[11], values[14])).replace('\n', '')
            #print(sqlcommand)
            cursor.execute(sqlcommand)
            summary.total_requests += 1

            if int(values[11]) >= 400:
                summary.total_errors += 1

    except IOError:
        print("Could not load log file \"" + filename + "\", skipping.")
    except:
        print("Could not execute SQL command. Skipping...")

summary.initialize(connection.cursor(), LOGS_FROM_DAYS)
connection.commit()

connection.close()
