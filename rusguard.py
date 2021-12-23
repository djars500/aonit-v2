from datetime import datetime,date,timedelta
import json
import pyodbc 

class RusGuardApi():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "rusguard":
            self.con =  pyodbc.connect('Driver={SQL Server};'
                      f"Server={self.data['rusguard_server_name']};"
                      'Database=RusGuardDB;'
                      'Trusted_Connection=yes;')
    
    
    def get_events(self,todayday): 
        print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"SELECT DateTime,Message,EmployeeID from [dbo].[Log] WHERE DateTime BETWEEN '{todayday.strftime('%Y-%m-%d')} 00:00:00' AND '{todayday.strftime('%Y-%m-%d')} 23:59:59';")
        events = cur.fetchall()
        print(events)
        return events

        
    
    def collect_events(self,todayday):  
        collect_events = []
        events = self.get_events(todayday)

        print("sad")
        
        for event in events:
            message = event[1]
            userID = event[2]
            dateTo = event[0]
            datetime_object = datetime.strptime(dateTo, '%Y-%m-%d %H:%M:%S')
            cursor = self.con.cursor()
            userExecute = cursor.execute(f"SELECT TableNumber,FirstName,SecondName,LastName FROM [dbo].[Employee] WHERE [_id]='{userID}'")
            user = userExecute.fetchone()
            iin = user[0]
            fullName = f"{user[1]} {user[2]} {user[3]}"

            if message == 'Выход':
               collect_events.append(
                    (
                        iin,
                        fullName,
                    0,
                   datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday
                ))  
            elif message == 'Вход':
                collect_events.append(
                    (
                        iin,
                        fullName,
                    1,
                   datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday
                ))

        return collect_events





