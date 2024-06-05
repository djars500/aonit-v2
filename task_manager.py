import threading
import time
from aonit_log import IntegrationAonitLog
from era import Ent
from aonit import IntegrationAonit
from aonit_log import IntegrationAonitLog
from datetime import date, datetime,timedelta
import schedule
import json
from hikvision import HikvisionApi
from perco import Perco
import sqlite3
from perco_web import PercoWebApi

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
        self.hikvision = HikvisionApi()
        self.perco_web = PercoWebApi()
        self.rusguard = RusGuardApi()
        if self.data['selected_version'] == "perco":
            self.perco = Perco()
        self.is_done = False 
       
    
    def done(self): 
        self.is_done = True 

    def getJob(self, today):
        # today = date.today()
            
        self.cursor.execute("DELETE FROM events WHERE created_at = ?;", (today, ))
        if self.data['selected_version'] == "perco":
            events = self.perco
        elif self.data['selected_version'] == "era":
            events = self.era
        elif self.data['selected_version'] == "rusguard":
            events = self.rusguard
        elif self.data['selected_version'] == "hikvision":
            events = self.hikvision
        elif self.data['selected_version'] == "perco_web":
            events = self.perco_web
        new_events = events.collect_events(today)

        self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", new_events)
        self.con.commit()

    def sendAonit(self, today):
        if self.data['aonit_type'] == 'log':
            send= self.aonitLog.sendRequestToAonit(today)
        else:     
            send = self.aonitTp.sendRequestToAonit(today)


        if send['code'] == 200:
            print("Успешно отправлено")
        else:
            print("ПРОВЕРТЕ СЕТЬ")
    
    def sendJob(self):
        if datetime.now().weekday() < 5:
            print('Вызодные')
            return

        today = date.today()
        
        last_time = datetime.strptime(self.data['last_process_time'], '%Y-%m-%d').date()
        if last_time >= today:
            self.getJob(today=today)
            self.sendAonit(today)
        else:
            start_date = last_time
            day = timedelta(days=1)
            while start_date <= today: 
                print(start_date)
                  
                self.getJob(start_date) 
                self.sendAonit(start_date)
                start_date += day
        
        self.data['last_process_time'] = today.strftime('%Y-%m-%d')
        with open('conf.json', 'w') as f:
            json.dump(self.data,f, ensure_ascii=False, indent=4)
        
       
 
    def run(self):
        datetime_obj = datetime.strptime(self.data['year'], '%Y-%m-%d').date()

        if (datetime.now().date() > datetime_obj):
            return
        schedule.every(55).seconds.do(self.sendJob)
        # schedule.every().hour.at("08:05").do(self.sendJob)
        while not self.is_done: 
            time.sleep(self.delay) 
            schedule.run_pending()
           
        print('thread done') 

       

    

    
 
 


