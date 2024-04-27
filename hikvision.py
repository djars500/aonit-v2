from datetime import datetime,date,timedelta
import json
import pyodbc 

class HikvisionApi():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "hikvision":
            self.con =  pyodbc.connect('Driver={SQL Server};'
                      f"Server={self.data['hikvision_server_name']};"
                      'Database=thirdparty;'
                      'Port=1433;'
                      'uid=sa;'
                      'pwd=123456qA;'
                      )
    
    
    def get_events(self,todayday): 
        # print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"SELECT employeeID, authDateTime, direction, deviceName, personName, cardNo from attlog WHERE authDate BETWEEN '{todayday.strftime('%Y-%m-%d')}' AND '{todayday.strftime('%Y-%m-%d')}' ORDER BY authDateTime DESC;")
        events = cur.fetchall()
        return events
    
    def get_events_month(self,todayday): 
        # print(todayday)
        last_month = todayday - timedelta(days=93)
        cur = self.con.cursor() 
        cur.execute(f"SELECT employeeID, authDateTime, direction, deviceName, personName, cardNo from attlog WHERE authDate BETWEEN '{last_month.strftime('%Y-%m-%d')}' AND '{todayday.strftime('%Y-%m-%d')}' ORDER BY authDateTime DESC;")
        events = cur.fetchall()
        return events

        
    
    def collect_events(self,todayday, month=False):  
        collect_events = []
        if month:
            events = self.get_events_month(todayday)
        else:
            events = self.get_events(todayday)
        print(todayday)
        events = self.get_events(todayday)

        
        for event in events:
            message = event[2]
            door = event[3]
            dateTo = event[1]
            iin = event[5]
            fullName = ''
            datetime_object = dateTo - timedelta(hours=1)
            cursor = self.con.cursor()


            if message == 'IN' and door == self.data['hikvision']['out']:
                collect_events.append(
                        (
                            iin,
                            fullName,
                        0,
                    datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                        todayday
                    ))  
            elif message == 'IN' and door == self.data['hikvision']['in']:
                collect_events.append(
                    (
                        iin,
                        fullName,
                    1,
                datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday
                ))

        return collect_events





