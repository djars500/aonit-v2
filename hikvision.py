from datetime import datetime,date,timedelta
import json
import pyodbc 

class HikvisionApi():
    def __init__(self):
        with open('conf.json') as f:
            self.data = json.load(f)
        
        if self.data['selected_version'] == "hikvision":
            self.createDb()
    
    
    def get_events(self,todayday): 
        # print(todayday)
        cur = self.con.cursor() 
        start_datetime = datetime.combine(todayday, datetime.min.time()).replace(hour=2)  # 08:00:00
        end_datetime = datetime.combine(todayday, datetime.min.time()).replace(hour=23, minute=59)  # 20:15:00

        query = """
        SELECT employeeID, authDateTime, direction, deviceName, personName, cardNo
        FROM attlog
        WHERE authDateTime BETWEEN ? AND ?
        ORDER BY authDateTime DESC;
        """

        # Используем параметры вместо вставки строк
        cur.execute(query, (start_datetime, end_datetime))
        events = cur.fetchall()
        
        self.update_users_table(events=events)
        return events
    
    def get_events_not_proccesed(self): 
        # print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"SELECT employeeID, authDateTime, direction, deviceName, personName, cardNo from attlog WHERE isSended = 0 ORDER BY authDateTime DESC;")
        events = cur.fetchall()
        
        self.update_users_table(events=events)
        return events
        
    def updateSended(self, records):
        username = 'sa'
        password = '123456qA'
        events = []
        server = self.data["hikvision_server_name"]
        conn = HikvisionApi().connectionToDb(server, 'thirdparty', username, password)
        cur = conn.cursor() 
        for record in records:
            try:
                datetime_obj = datetime.strptime(record[3], '%d.%m.%Y %H:%M:%S')

                cur.execute("""
                        UPDATE attlog 
                        SET isSended = 1 
                        WHERE authDateTime = ?
                    """, (datetime_obj))
                events = cur.commit()
            except Exception as e:
                print(record, e)
        
        return events
    
    def get_date_from_data(self, record):
        return record[3]
    
    def collect_events(self,todayday=None, processed=False):  
        collect_events = []
        if processed:
            events = self.get_events_not_proccesed()
        else:
            events = self.get_events(todayday)
        print(processed, f'count events {len(events)}')

        
        for event in events:
            
            message = event[2]
            dateTo = event[1]
            iin = self.get_iin_by_employee_id(event[0])
            fullName = self.decode_messed_text(event[4])
            datetime_object = dateTo - timedelta(hours=self.data['hikvision']['timezone'])
            
            if processed is True:
                todayday = datetime_object.date()
            

            if message == 'OUT':
                collect_events.append(
                        (
                            iin,
                            fullName,
                        0,
                    datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                        todayday
                    ))  
            elif message == 'IN':
                collect_events.append(
                    (
                        iin,
                        fullName,
                    1,
                datetime_object.strftime("%d.%m.%Y %H:%M:%S"),
                    todayday
                ))

        return collect_events



    def createDb(self):
        new_db_name = 'thirdparty'
        username = 'sa'
        password = '123456qA'
        server = self.data["hikvision_server_name"]

        try:
            # Подключение к master
            conn = self.connectionToDb(server, 'master', username, password)
            print("Успешное подключение к SQL Server.")
            cursor = conn.cursor()

            # Проверка существования базы
            cursor.execute("SELECT database_id FROM sys.databases WHERE name = ?", (new_db_name,))
            if cursor.fetchone():
                print(f"База данных '{new_db_name}' уже существует.")
            else:
                conn.autocommit = True
                cursor.execute(f"CREATE DATABASE {new_db_name}")
                print(f"База данных '{new_db_name}' успешно создана.")
                conn.commit()
                conn.autocommit = False
        except Exception as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return
        finally:
            conn.close()

        # Подключаемся к новой базе
        conn = self.connectionToDb(server, new_db_name, username, password)
        self.con = conn

        # Таблицы и их схемы
        tables = {
            "attlog": """
                CREATE TABLE attlog (
                    employeeID NVARCHAR(100), 
                    authDateTime DATETIME,
                    authTime TIME(7),
                    authDate DATE,
                    direction NVARCHAR(100), 
                    deviceName NVARCHAR(100),
                    serialNo NVARCHAR(100),
                    personName NVARCHAR(100),
                    cardNo NVARCHAR(100),
                    isSended BIT DEFAULT 0
                )
            """,
            "users": """
                CREATE TABLE users (
                    employeeID NVARCHAR(100) NULL,
                    iin NVARCHAR(100) NULL
                )
            """
        }

        # Создание таблиц
        for table_name, create_sql in tables.items():
            self.createTableIfNotExists(conn, table_name, create_sql)

    def createTableIfNotExists(self, conn, table_name, create_sql):
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?
            """, (table_name,))
            if cursor.fetchone()[0]:
                print(f"Таблица '{table_name}' уже существует.")
            else:
                conn.autocommit = True
                cursor.execute(create_sql)
                print(f"Таблица '{table_name}' успешно создана.")
                conn.commit()
                conn.autocommit = False
        except Exception as e:
            print(f"Ошибка при создании таблицы '{table_name}': {e}")

        
    def connectionToDb(self, server, db_name, username, password):
        driver = '{SQL Server};'
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={db_name};UID={username};PWD={password}'
        conn = pyodbc.connect(connection_string)
        
        return conn
    
    
    def update_users_table(self, events):
        cur = self.con.cursor()

        # Уникальные пары из событий
        unique_pairs = {
            (employeeID, cardNo)
            for employeeID, _, _, _, _, cardNo in events
            if employeeID and cardNo and cardNo.__len__() == 12
        }

        if not unique_pairs:
            return  # Нет данных для вставки

        # Получаем уже существующие пары из таблицы users
        cur.execute("SELECT employeeID, iin FROM users")
        existing_pairs = set((row[0], row[1]) for row in cur.fetchall())  # ✅

        # Вычисляем только новые пары, которых ещё нет в таблице
        new_pairs = list(unique_pairs - existing_pairs)

        if not new_pairs:
            return  # Всё уже есть в базе

        # Создаём SQL-выражение для bulk insert
        placeholders = ",".join(["(?, ?)"] * len(new_pairs))
        flat_values = [value for pair in new_pairs for value in pair]

        insert_query = f"INSERT INTO users (employeeID, iin) VALUES {placeholders}"

        try:
            cur.execute(insert_query, flat_values)
            print(f"Добавлено {len(new_pairs)} новых связок в таблицу users.")
        except Exception as e:
            print(f"Ошибка при bulk insert в users: {e}")

        self.con.commit()

    def get_iin_by_employee_id(self, employeeID):
        """
        Получает ИИН сотрудника по его employeeID из таблицы users.
        Возвращает None, если не найдено.
        """
        if not employeeID:
            return None

        try:
            cur = self.con.cursor()
            query = "SELECT iin FROM users WHERE employeeID = ?"
            cur.execute(query, (employeeID,))
            result = cur.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Ошибка при получении ИИН по employeeID={employeeID}: {e}")
            return ''
        
    def decode_messed_text(self, text):
        try:
            # Сначала перекодируем строку в байты, считая, что она была ошибочно прочитана как latin-1
            
            return text.encode('cp1251').decode('utf-8')
        except Exception as e:
            return text