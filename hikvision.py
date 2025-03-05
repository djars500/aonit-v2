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
        return events
    
    def get_events_not_proccesed(self): 
        # print(todayday)
        cur = self.con.cursor() 
        cur.execute(f"SELECT employeeID, authDateTime, direction, deviceName, personName, cardNo from attlog WHERE isSended = 0 ORDER BY authDateTime DESC;")
        events = cur.fetchall()
        return events
        
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
    
    def get_date_from_data(record):
        return record[3]
    
    def collect_events(self,todayday=None, processed=False):  
        collect_events = []
        if processed:
            events = self.get_events_not_proccesed()
        else:
            events = self.get_events(todayday)
        print(processed, events)
        # events = self.get_events(todayday)

        
        for event in events:
            
            message = event[2]
            dateTo = event[1]
            iin = event[5]
            fullName = ''
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
        conn = self.connectionToDb(server, 'master', username, password)
        print("Connected to SQL Server successfully")

        # Create a cursor from the connection
        cursor = conn.cursor()
        check_db_query = f"""
        SELECT database_id 
        FROM sys.databases 
        WHERE name = '{new_db_name}'
        """
        
        cursor.execute(check_db_query)
        result = cursor.fetchone()

        if result:
            print(f"Database '{new_db_name}' already exists.")
        else:
            conn.autocommit = True
            # If the database doesn't exist, create it
            create_db_query = f"CREATE DATABASE {new_db_name}"
            cursor.execute(create_db_query)
            print(f"Database '{new_db_name}' created successfully.")
            conn.commit()  # Commit the transaction to create the database
            conn.autocommit = False

        # Change the connection to the new database
        conn.close()  # Close the current connection to the 'master' database
        conn = self.connectionToDb(server, new_db_name, username, password)
        cursor = conn.cursor()

        table_name = 'attlog'
        check_table_query = f"""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = '{table_name}'
        """
        cursor.execute(check_table_query)
        table_exists = cursor.fetchone()[0]

        if table_exists:
            print(f"Table '{table_name}' already exists.")
        else:
            # Create the table if it doesn't exist
            conn.autocommit = True
            create_table_query = f"""
            CREATE TABLE {table_name} (
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
            """
            cursor.execute(create_table_query)
            print(f"Table '{table_name}' created successfully.")
            conn.commit()  # Commit the transaction to create the table

            conn.autocommit = False
        self.con = conn
        
    def connectionToDb(self, server, db_name, username, password):
        driver = '{SQL Server};'
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={db_name};UID={username};PWD={password}'
        conn = pyodbc.connect(connection_string)
        
        return conn