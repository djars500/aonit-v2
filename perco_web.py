from datetime import datetime,date,timedelta
import json
import pyodbc 
from mysql import connector

class PercoWebApi():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "perco_web":
            self.reconnect()
            
    def reconnect(self):
        if hasattr(self, 'con') and self.con.is_connected():
            self.con.close()
        self.con = connector.connect(
            host=self.data['percoweb']['host'],
            user=self.data['percoweb']['user'],
            password=self.data['percoweb']['password'],
            database=self.data['percoweb']['database'],
            port=self.data['percoweb']['port'],
            connection_timeout=120
        )
    
    
    def get_events(self,todayday): 
        self.reconnect()
        cur = self.con.cursor() 
        cur.execute(
            f"SELECT time_label, event_type, device_id, user_id, resource_number from event WHERE time_label BETWEEN '{todayday.strftime('%Y-%m-%d')} 00:00:00' AND '{todayday.strftime('%Y-%m-%d')} 23:59:59' AND event_type = 17 ORDER BY time_label DESC;"
            )
        events = cur.fetchall()
        cur.close()
        return events

    def get_events_not_proccesed(self): 
        self.reconnect()

        cur = self.con.cursor() 
        cur.execute(
            f"SELECT time_label, event_type, device_id, user_id, resource_number from event WHERE is_sended != 1 AND event_type = 17 ORDER BY time_label DESC;"
            )
        events = cur.fetchall()
        cur.close()
        return events
    
    def get_date_from_data(self, record):
        return record[3]
    
    def collect_events(self,todayday=None, processed=False):  
        collect_events = []
        if processed:
            events = self.get_events_not_proccesed()
        else:
            events = self.get_events(todayday)
        
        
        for event in events:
            message = event[2]
            userID = event[3]
            dateTo = event[0]
            resource = event[4]
            datetime_object = dateTo
            cursor = self.con.cursor()
            
            if processed is True:
                todayday = datetime_object.date()

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

                if resource == 2:
                    collect_events.append(
                            (
                                iin,
                                fullName,
                            0,
                        datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                            todayday
                        ))  
                elif resource == 1:
                    collect_events.append(
                        (
                            iin,
                            fullName,
                            1,
                        datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                        todayday
                    ))
        return collect_events

    def updateSended(self, records):
        self.reconnect()
        cur = self.con.cursor()
        for record in records:
            cur.execute(f"""UPDATE event SET is_sended = 1 
                        WHERE 
                        event_type = 17 AND
                        time_label = '{datetime.strptime(record[3], '%d.%m.%Y %H:%M:%S').strftime("%Y.%m.%d %H:%M:%S")}';
                        """)
            self.con.commit()




