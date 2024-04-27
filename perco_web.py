from datetime import datetime,date,timedelta
import json
import pyodbc 
from mysql import connector

class PercoWebApi():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "perco_web":
            
            self.con = connector.connect(
                host=self.data['percoweb']['host'],
                user=self.data['percoweb']['user'],
                password=self.data['percoweb']['password'],
                database=self.data['percoweb']['database'],
                port=self.data['percoweb']['port']
            )
    
    
    def get_events(self,todayday): 
        # print(todayday)
        print(self.con)

        cur = self.con.cursor() 
        cur.execute(
            f"SELECT time_label, event_type, device_id, user_id from event WHERE time_label BETWEEN '{todayday.strftime('%Y-%m-%d')} 00:00:00' AND '{todayday.strftime('%Y-%m-%d')} 23:59:59' AND event_type = 17 ORDER BY time_label DESC;"
            )
        events = cur.fetchall()
        # print(events, 'get_events')
        return events

    def get_events_month(self,todayday): 
        # print(todayday)
        today = datetime.date()
        cur = self.con.cursor() 
        cur.execute(
            f"SELECT time_label, event_type, device_id, user_id from event WHERE time_label BETWEEN '{todayday.strftime('%Y-%m-%d')} 00:00:00' AND '{today.strftime('%Y-%m-%d')} 23:59:59' AND event_type = 17 ORDER BY time_label DESC;"
            )
        events = cur.fetchall()
        # print(events, 'get_events')
        return events
        
    
    def collect_events(self,todayday, month=False):  
        collect_events = []
        if month:
            events = self.get_events_month(todayday)
        else:
            events = self.get_events(todayday)
        
        
        for event in events:
            message = event[2]
            userID = event[3]
            dateTo = event[0]
            datetime_object = datetime.strftime(dateTo, "%d.%m.%Y %H:%M:%S")
            cursor = self.con.cursor()

            if userID != None:
                try:
                    cursor.execute(
                        f"SELECT tabel_number,user_id FROM user_staff WHERE user_id = {userID}")
                    user = cursor.fetchone()
                    iin = user[0]
                    fullName = user[0]
                except Exception as e:
                    pass
                    # print(userID, e, event)

                if message == 2:
                    collect_events.append(
                            (
                                iin,
                                fullName,
                            0,
                        datetime_object,
                            todayday
                        ))  
                elif message == 1:
                    collect_events.append(
                        (
                            iin,
                            fullName,
                        1,
                    datetime_object,
                        todayday
                    ))
        return collect_events





