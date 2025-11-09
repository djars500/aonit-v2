from collections import defaultdict
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
from secretkey import verify_activation_key
from zkteco import Zkteco


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
        self.zkteco = Zkteco()
        self.rusguard = RusGuardApi()
        if self.data['selected_version'] == "perco":
            self.perco = Perco()
        self.is_done = False 

       
    
    def done(self): 
        self.is_done = True 
        
    def get_device_type(self):
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
        elif self.data['selected_version'] == "zkteco":
            events = self.zkteco
        return events

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
        elif self.data['selected_version'] == "zkteco":
            events = self.zkteco
        new_events = events.collect_events(today)

        self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", new_events)
        self.con.commit()

    def sendAonit(self, today):
        print(today)
        if self.data['aonit_type'] == 'log':
            send= self.aonitLog.sendRequestToAonit(today)
        else:     
            send = self.aonitTp.sendRequestToAonit(today)


        if send['code'] == 200:
            print("Успешно отправлено")
            return 200
        else:
            print("ПРОВЕРТЕ СЕТЬ")
            return 500
            
    def sendProcced(self):
        device = self.get_device_type()
        events = device.collect_events(processed=True)
        grouped_by_date = defaultdict(list)

        if (len(events) == 0):    
            print('No event')

        for record in events:
            date = datetime.strptime(device.get_date_from_data(record), '%d.%m.%Y %H:%M:%S').date()  # Извлекаем дату из datetime
            grouped_by_date[date].append(record)
            self.cursor.execute("DELETE FROM events WHERE created_at = ?;", (date, ))
            self.con.commit()

            
        # Вывод сгруппированных данных
        for date, records in grouped_by_date.items():
            self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", records)
            self.con.commit()
            status = self.sendAonit(date)
            if status == 200:
                device.updateSended(records)
        

    def updateSended(self, records):
        username = 'sa'
        password = '123456qA'
        
        server = self.data["hikvision_server_name"]
        conn = HikvisionApi().connectionToDb(server, 'thirdparty', username, password)
        cur = conn.cursor() 
        for record in records:
            
            cur.execute(f"""UPDATE attlog SET isSended = 1 
                        WHERE 
                        cardNo = '{record[0]}' AND
                        authDateTime = '{record[3]}';
                        """)
            events = cur.commit()
        return events
    
    def sendJob(self):
        if datetime.now().weekday() > 5:
            print('Выходные')
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
        datetime_obj = datetime.strptime(self.data.get('year', '2024-12-31'), '%Y-%m-%d').date()
        type_auth = self.data.get('type', None)
        input_key = self.data.get('key', None)
        if type_auth == 'year':
            if (datetime.now().date() > datetime_obj):
                return
        elif type_auth == 'key':
            is_valid, message = verify_activation_key(input_key)
            if not is_valid:
                return
        else:
            return
        # schedule.every(1).hours.do(self.sendJob)
        # schedule.every(2).minutes.do(self.sendProcced)
        schedule.every(1).minutes.do(self.sendProcced)
        while not self.is_done:
            time.sleep(self.delay) 
            schedule.run_pending()
           
        print('thread done') 

       

    

    
 
 


