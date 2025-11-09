import pyodbc
from datetime import datetime,date,timedelta
import json

class Zkteco():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "zkteco":
            self.con = pyodbc.connect(
                'Driver={PostgreSQL Unicode};'
                'Server=localhost;'
                'Port=7496;'
                'Database=biotime;'
                'Uid=postgres;'
                'Pwd=admin123;'
            )

    def get_events(self,todayday): 
        cur = self.con.cursor()
        start_datetime = datetime.combine(todayday, datetime.min.time()).replace(hour=2)
        end_datetime = datetime.combine(todayday, datetime.min.time()).replace(hour=23, minute=59)
        query = """
                SELECT emp_id, punch_time, terminal_sn, terminal_alias
                FROM iclock_transaction
                WHERE punch_time BETWEEN ? AND ?
                ORDER BY punch_time DESC;
                """

        # Используем параметры вместо вставки строк
        cur.execute(query, (start_datetime, end_datetime))
        events = cur.fetchall()
        return events

    
    def get_events_not_proccesed(self): 
        cur = self.con.cursor()
        cur.execute(f"select emp_id, punch_time, terminal_sn, terminal_alias from iclock_transaction WHERE is_sended != 1 ORDER BY punch_time DESC;")
        events = cur.fetchall()
        return events
    
    def get_date_from_data(self, record):
        return record[3]
    
    def updateSended(self, records):
        
        cur = self.con.cursor()
        for record in records:
            iin = record[0]
            cur.execute(f"select id from personnel_employee where nickname='{iin}'")
            user = cur.fetchone()

            cur.execute(f"""UPDATE iclock_transaction SET is_sended = 1 
                        WHERE 
                        emp_id = '{user[0]}' AND
                        punch_time = '{datetime.strptime(record[3], '%d.%m.%Y %H:%M:%S').strftime("%Y.%m.%d %H:%M:%S")}';
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
            in_doors = self.data['zkteco']['in_doors']
            out_doors = self.data['zkteco']['out_doors']
            door = event[2]
            dateTo = event[1]
            user_info = self.get_iin_by_employee_id(event[0])
            iin = user_info[2]
            fullName = user_info[0] + ' ' + user_info[1]
            datetime_object = dateTo.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            if door in in_doors:
                direction = 1
            elif door in out_doors:
                direction = 0
            else:
                raise Exception('Нету указанных дверей в Zkteco')

            if processed is True:
                todayday = datetime_object.date()

            collect_events.append(
                (
                    iin,
                    fullName,
                    direction,
                    datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday
                ))

        return collect_events


    def get_iin_by_employee_id(self, emp_id):
        """
        Получает ИИН сотрудника по его employeeID из таблицы users.
        Возвращает None, если не найдено.
        """
        if not emp_id:
            return None

        try:
            cur = self.con.cursor()
            query = "SELECT last_name, first_name, nickname FROM personnel_employee WHERE id = ?"
            cur.execute(query, (emp_id,))
            result = cur.fetchone()
            return result if result and result else None
        except Exception as e:
            print(f"Ошибка при получении ИИН по employeeID={emp_id}: {e}")
            return ''
