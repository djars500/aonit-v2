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
            self.add_column_sended()
    
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
    
    def get_events_not_proccesed(self): 
        # print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"select * from FB_EVN WHERE COALESCE(ISSENDED, 0) != 1 AND EVN IN (3,5) AND USR != 0 ORDER BY DT DESC;")
        events = cur.fetchall()
        return events
    
    def get_date_from_data(self, record):
        return record[3]
    
    def updateSended(self, records):
        
        cur = self.con.cursor()
        for record in records:
            iin = record[0]
            cur.execute(f"select id from FB_USR where tabnum='{iin}'")
            user = cur.fetchone()

            cur.execute(f"""UPDATE FB_EVN SET ISSENDED = 1 
                        WHERE 
                        USR = '{user[0]}' AND
                        DT = '{datetime.strptime(record[3], '%d.%m.%Y %H:%M:%S').strftime("%Y.%m.%d %H:%M:%S")}';
                        """)
            self.con.commit()

    
    def collect_events(self,todayday=None,processed=False):  
        collect_events = []
        if processed:
            events = self.get_events_not_proccesed()
        else:
            events = self.get_events(todayday)
        print(processed, len(events))
        
        for event in events:
            unic_id = event[0]
            date = event[1]
          
            mac_ip = event[2]
            code1 = event[3]
            code2 = event[4]

            code = ''

            yesOrNo = False

            if processed is True:
                todayday = date.date()
                
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

    def add_column_sended(self):
        
        column_name = 'ISSENDED'
        table_name = 'FB_EVN'

        # SQL запрос для проверки существования столбца
        check_column_query = f"""
        SELECT RDB$FIELD_NAME AS FIELD_NAME
        FROM RDB$RELATION_FIELDS
        WHERE RDB$RELATION_NAME= '{table_name}'
        AND RDB$FIELD_NAME = '{column_name}';
        """
        
                # Выполняем запрос на проверку наличия столбца
        cur = self.con.cursor()

        cur.execute(check_column_query)

        # Если столбец не найден (результат пустой), добавляем его
        if cur.fetchone() is None:
            # SQL запрос для добавления нового столбца
            alter_table_query = f"ALTER TABLE {table_name} ADD {column_name} SMALLINT DEFAULT 0;"
            
            # Выполняем запрос для добавления столбц
            cur.execute(alter_table_query)

            # Сохраняем изменения в базе данных
            self.con.commit()
        else:
            print('is Sended already exists')
