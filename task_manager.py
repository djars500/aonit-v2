import threading
import time
from aonit_log import IntegrationAonitLog
from era import Ent
from aonit import IntegrationAonit
from aonit_log import IntegrationAonitLog
from datetime import date, datetime,timedelta
import schedule
import json
from perco import Perco
import sqlite3

from rusguard import RusGuardApi



class Task(threading.Thread):
    def __init__(self,seconds):
        super().__init__() 
        with open('conf.json') as f:
            self.data = json.load(f)
        self.delay = seconds 
        self.aonitTp = IntegrationAonit()
        self.aonitLog = IntegrationAonitLog()
        self.con = sqlite3.connect("mydb.db",check_same_thread=False) 
        self.cursor = self.con.cursor()
        self.era = Ent()
        self.rusguard = RusGuardApi()
        if self.data['selected_version'] == "perco":
            self.perco = Perco()
        self.is_done = False 
       
    
    def done(self): 
        self.is_done = True 

    def getJob(self):
        today = date.today()
        self.cursor.execute("DELETE FROM events WHERE created_at = ?;", (today, ))
        if self.data['selected_version'] == "perco":
            events = self.perco.loadEvents(today)
        elif self.data['selected_version'] == "era":
            events = self.era.collect_events(today)
        elif self.data['selected_version'] == "rusguard":
            events = self.rusguard.collect_events(today)
        self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", events)

        self.con.commit()

    def sendJob(self):
        today = date.today()
        if self.data['aonit_type'] == 'log':
            send= self.aonitLog.sendRequestToAonit(today)
        else:     
            send = self.aonitTp.sendRequestToAonit(today)


        if send['code'] == 200:
            print(send,"Успешно отправлено")
        else:
            print("ПРОВЕРТЕ СЕТЬ")
       
 
    def run(self):
        schedule.every().day.at("23:30").do(self.getJob)
        schedule.every().day.at("23:35").do(self.sendJob)
        while not self.is_done: 
            time.sleep(self.delay) 
            schedule.run_pending()
           
        print('thread done') 

       

    

    
 
 


