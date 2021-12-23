import fdb
from datetime import datetime,date,timedelta
import json

class Ent():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "era":
            if self.data['aonit_server_ip'] == "127.0.0.1":
                self.con = fdb.connect(dsn=self.data['c_base_path'], user='SYSDBA', password='masterkey')
            else:
                self.con = fdb.connect(dsn=f"{self.data['aonit_server_ip']}:C:\Program Files\ENT\Server\DB\CBASE.FDB", user='SYSDBA', password='masterkey')
    
    def get_events(self,todayday): 
        self.get_mac_adresses()
        print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"select * from FB_EVN where DT BETWEEN '{todayday.strftime('%Y-%m-%d')} 00:00:00' AND '{todayday.strftime('%Y-%m-%d')} 23:59:59';")
        events = cur.fetchall()
        return events

    def get_mac_adresses(self):
        cur = self.con.cursor() 
        cur.execute(f"select NAME from FB_DVS")
        events = cur.fetchall()
        print(events)
        
    
    def collect_events(self,todayday):  
        collect_events = []
        events = self.get_events(todayday)
        
        for event in events:
            unic_id = event[0]
            date = event[1]
          
            mac_ip = event[2]
            code1 = event[3]
            code2 = event[4]

            code = ''

            yesOrNo = False

            for ip in self.data['mac_addresses']:
                if int(code1) == 3 and int(code2) == 0 and mac_ip == ip:
                    yesOrNo = True
                    code = 1
                    break
                elif int(code1) == 5 and int(code2) == 0 and mac_ip == ip:
                    yesOrNo = True
                    code = 0
                    break
                else:
                    yesOrNo = False
            
            if yesOrNo == False:
                print("NO")
                continue
            else:
                print("OK", code)
        
            user_id = event[7]
            cur = self.con.cursor() 
            cur.execute(f"select * from FB_USR where id={user_id}")
            user = cur.fetchone()

            if user is None:
                continue
            else:    
            
                iin = user[1] 
                surname = user[3]
                name = user[2]
                collect_events.append(
                    (
                        iin,
                    f"{surname} {name}",
                    code,
                    date.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday

                ))

        return collect_events





