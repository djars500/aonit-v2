
from PyQt5.QtWidgets import QApplication,QFileDialog,QHBoxLayout,QVBoxLayout, QMainWindow, QGridLayout,QComboBox, QWidget,QDateEdit, QTableWidget, QTableWidgetItem, QPushButton,QBoxLayout,QDialog,QTabWidget,QLineEdit,QLabel,QLayout
from PyQt5.QtCore import QSize, Qt
from PyQt5 import QtCore
from datetime import date, datetime,timedelta
import sqlite3
from era import Ent
from hikvision import HikvisionApi
from perco import Perco
from aonit import IntegrationAonit
from aonit_log import IntegrationAonitLog
from perco_web import PercoWebApi
from secretkey import verify_activation_key
from task_manager import Task
import json
from PyQt5 import QtGui
import os.path
from rusguard import RusGuardApi
from zkteco import Zkteco


class MainWindow(QMainWindow):
    # Переопределяем конструктор класса
    def __init__(self): 
        if os.path.exists('conf.json') == False:
            with open('conf.json', 'w+') as f:
                data = {
                    "ip_addresses": [
                        "http://10.245.12.102/bip-sync/?wsdl",
                        "http://10.61.42.29/bip-sync/?wsdl",
                        "http://10.245.12.102/bip-sync-wss-gost/?wsdl",
                        "http://10.245.12.67/shep/bip-sync-wss-gost/?wsdl"
                    ],
                    "mac_addresses": [
                        "000B3A007AE6"   
                    ],
                    "selected_ip_address": "http://10.245.12.102/bip-sync/?wsdl",
                    "gost_pass": "null",
                    "gost_path": "null",
                    "login": "null",
                    "password": "null",
                    "c_base_path": "C:/Program Files/ENT/Server/DB/CBASE.FDB",
                    "aonit_server_ip": "127.0.0.1",
                    "rusguard_server_name":"VDSWIN2K19\\RUSGUARD",
                    "hikvision_server_name":"10.243.184.249",
                    "aonit_type": "log",
                    "selected_version": "perco_web",
                    "year": "2024-12-31",
                    "last_process_time": "2024-05-27",
                    "perco_host": "10.1.80.200",
                    "percoweb": {
                        "host": "127.0.0.1",
                        "user": "root",
                        "password": "AAss!@#$",
                        "database": "perco",
                        "port": 49001
                    },
                    "hikvision": {
                        "in": "10.243.184.221",
                        "out": "10.243.184.222",
                        "timezone": 0
                    }
                    }
                json.dump(data,f, ensure_ascii=False, indent=4)
            with open('conf.json') as f:
                self.data = json.load(f)
        else:
            with open('conf.json') as f:
                self.data = json.load(f)
        
        # Обязательно нужно вызвать метод супер класса
        QMainWindow.__init__(self)
        self.con = sqlite3.connect("mydb.db",check_same_thread=False) 
        self.aonitTp = IntegrationAonit()
        self.aonitLog = IntegrationAonitLog()
        self.cursor = self.con.cursor()
        self.era = Ent()
        self.rusguard = RusGuardApi()
        self.hikvision = HikvisionApi()
        self.perco_web = PercoWebApi()
        self.zkteco = Zkteco()

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

        if self.data['selected_version'] == "perco":
            self.perco = Perco()
        
        self.setMinimumSize(QSize(800, 400))             # Устанавливаем размеры
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowTitle("Приложение Интеграций ПИК 2.0 @2024") 
        central_widget = QWidget(self)      
        self.setCentralWidget(central_widget)    
        grid_layout = QGridLayout()    
        central_widget.setLayout(grid_layout) 

        self.tabs = QTabWidget()
        self.table = QTableWidget(self)
        self.responseTable = QTableWidget(self)
        
        self.scheduleTable = QTableWidget(self)

        self.confTable = QWidget(self)
        conf_layout = QGridLayout() 
        gosth_layout = QHBoxLayout()

        self.scheduleWidget = QWidget(self)
        schedule_layout = QGridLayout() 

        self.scheduleWidget.setLayout(schedule_layout)

        self.pickDate = QPushButton("Выбрать данные")


        def pickDateMethod():
            value = self.calendar.date().toPyDate()
            self.createData(value)
            print(value)

        def sendDateMethod():
            today = self.calendar.date().toPyDate()
         
            if self.data['aonit_type'] == 'log':
                send= self.aonitLog.sendRequestToAonit(today)
            else:     
                send = self.aonitTp.sendRequestToAonit(today)
            print(send)
            if send['code'] == 200:
                self.showDialog("Данные успешно отправлены по адресу:"+send['url'])
            elif send['code'] == 500:
                self.showDialog("Проверьте подключение к сети. Сеть:"+send['url'])
            else:
                self.showDialog("Упс что то не так")
           
        
        self.pickDate.clicked.connect(pickDateMethod)
        self.sendPickDate = QPushButton("Отправить по этому дню")
        self.sendPickDate.clicked.connect(sendDateMethod)
        self.calendar = QDateEdit(self)
   



        

        schedule_layout.addWidget(self.calendar)
        schedule_layout.addWidget(self.pickDate)
        schedule_layout.addWidget(self.sendPickDate)
        schedule_layout.addWidget(self.scheduleTable)

        self.confTable.setLayout(conf_layout)


        
        self.choiseGOST = QPushButton("...")
        self.choiseGOSTLabel = QLineEdit(self.data['gost_path'])
        self.choiseGOSTPassword = QLineEdit(self.data['gost_pass'])
        
        self.loginBtn = QLineEdit(self.data['login'])
        self.passwordBtn = QLineEdit(self.data['password']) 
        self.loginLabel = QLabel("ЛОГИН СИСТЕМЫ")
        self.ipLabel = QLabel("Выберите ip")
        self.ipLabelSelected = QLabel("Выбрано: "+self.data['selected_ip_address'])
        self.passwordLabel = QLabel("Пароль СИСТЕМЫ")
        self.saveBUTTON = QPushButton("Сохранить")

        self.combobox1 = QComboBox()
    
        self.combobox1.addItems(self.data['ip_addresses'])
        
        self.combobox1.currentTextChanged.connect(self.selected_ip_address_changed)
        self.saveBUTTON.clicked.connect(self.saveDATA)
        self.choiseGOST.clicked.connect(self.showDialogFileInput)

    
        conf_layout.addLayout(gosth_layout,0,0)

        gosth_layout.addWidget(self.choiseGOST)
        gosth_layout.addWidget(self.choiseGOSTLabel)
        gosth_layout.addWidget(self.choiseGOSTPassword)
        conf_layout.addWidget(self.loginLabel)
        conf_layout.addWidget(self.loginBtn)
        conf_layout.addWidget(self.passwordLabel)
        conf_layout.addWidget(self.passwordBtn)
        conf_layout.addWidget(self.ipLabel)
        conf_layout.addWidget(self.ipLabelSelected)
        conf_layout.addWidget(self.combobox1)
        conf_layout.addWidget(self.saveBUTTON)

        self.responseTable.setColumnCount(3)
        self.table.setColumnCount(5)     # Устанавливаем три колонки
             # и одну строку в таблице
        self.scheduleTable.setColumnCount(5) 
 
        # Устанавливаем заголовки таблицы
        self.table.setHorizontalHeaderLabels(["ИИН","ИМЯ","СОБЫИТИЕ","ВРЕМЯ", "ДАТА"])
        self.responseTable.setHorizontalHeaderLabels(["Статус","ТЕКСТ","ДАТА"])
        self.scheduleTable.setHorizontalHeaderLabels(["ИИН","ИМЯ","СОБЫИТИЕ","ВРЕМЯ", "ДАТА"])
 
       
        self.collectDataBtn = QPushButton("Обновить данные")
        self.createDataBtn = QPushButton("Создать данные")   
        self.pushDataBtn = QPushButton("Отправить данные")
     
        grid_layout.addWidget(self.collectDataBtn,1,0)
        grid_layout.addWidget(self.createDataBtn,1,1)
        grid_layout.addWidget(self.pushDataBtn,1,2)
        
        self.table.resizeColumnsToContents()
        self.responseTable.resizeColumnsToContents()
        self.tabs.addTab(self.table, "Собитий")
        self.tabs.addTab(self.responseTable,"Отправленные данные")
        self.tabs.addTab(self.confTable,"Конфигурация")
        self.tabs.addTab(self.scheduleWidget,"Отправка по расписаний")
        grid_layout.addWidget(self.tabs, 20, 0)  


    def showDialogFileInput(self):
        fname = QFileDialog.getOpenFileName(self, 'Дияр лох', '/home')
        if fname: 
            print(fname[0])
            self.choiseGOSTLabel.setText(fname[0])
            self.data['gost_path'] = fname[0]
            with open('conf.json', 'w') as f:
                json.dump(self.data,f, ensure_ascii=False, indent=4)
            

    def selected_ip_address_changed(self, selected_ip):
        self.data['selected_ip_address'] = selected_ip
        self.ipLabelSelected.setText("Выбрано: "+selected_ip)
        with open('conf.json', 'w') as f:
            json.dump(self.data,f, ensure_ascii=False, indent=4)
    
    def saveDATA(self):
        self.data['login'] = self.loginBtn.text()
        self.data['password'] = self.passwordBtn.text()
        self.data['gost_path'] = self.choiseGOSTLabel.text()
        self.data['gost_pass'] = self.choiseGOSTPassword.text()
        with open('conf.json', 'w') as f:
            json.dump(self.data,f, ensure_ascii=False, indent=4)
        

    def createBase(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS events
                (id INTEGER PRIMARY KEY,f_iin text, f_fio text,
                f_event text, f_date text,created_at date)
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS responses
                (
                    id INTEGER PRIMARY KEY,
                    status_code text,
                    response_text text,
                    created_at date
                )
        """)
        self.con.commit()
        

    def collectData(self,today):
            if today:
                self.cursor.execute("SELECT * FROM events WHERE created_at = ?;", (today, ))
            else:
                todayday = date.today()
                self.cursor.execute("SELECT * FROM events WHERE created_at = ?;", (todayday, ))
            
            events = self.cursor.fetchall()
    
            self.cursor.execute("SELECT * FROM responses;")
            responses = self.cursor.fetchall()
            self.table.setRowCount(len(events))
            self.scheduleTable.setRowCount(len(events))  
            self.responseTable.setRowCount(len(responses)) 
            for index,item in enumerate(responses):
                self.responseTable.setItem(index,0,QTableWidgetItem(item[1]))
                self.responseTable.setItem(index,1,QTableWidgetItem(item[2]))
                self.responseTable.setItem(index,2,QTableWidgetItem(item[3]))
            for index,item in enumerate(events):
                self.table.setItem(index, 0, QTableWidgetItem(item[1]))
                self.table.setItem(index, 1, QTableWidgetItem(item[2]))
                self.table.setItem(index, 2, QTableWidgetItem(item[3]))
                self.table.setItem(index, 3, QTableWidgetItem(item[4]))
                self.table.setItem(index, 4, QTableWidgetItem(item[5]))
            for index,item in enumerate(events):
                self.scheduleTable.setItem(index, 0, QTableWidgetItem(item[1]))
                self.scheduleTable.setItem(index, 1, QTableWidgetItem(item[2]))
                self.scheduleTable.setItem(index, 2, QTableWidgetItem(item[3]))
                self.scheduleTable.setItem(index, 3, QTableWidgetItem(item[4]))
                self.scheduleTable.setItem(index, 4, QTableWidgetItem(item[5]))
    
            
    def showDialog(self,name):
        dlg = QDialog()
        dlg.setWindowTitle('Заявка')
        dlg.setMinimumSize(QSize(600,100))
        b1 = QPushButton(name,dlg)
        b1.move(50,50)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.exec_()

    def createData(self,today):
        events = []
        if today:
            self.cursor.execute("DELETE FROM events WHERE created_at = ?;", (today, ))
            if self.data['selected_version'] == "perco":
                events = self.perco.collect_events(today)
            elif self.data['selected_version'] == "era":
                events = self.era.collect_events(today)
            elif self.data['selected_version'] == "rusguard":
                events = self.rusguard.collect_events(today)
            elif self.data['selected_version'] == "hikvision":
                events = self.hikvision.collect_events(today)
            elif self.data['selected_version'] == "perco_web":
                events = self.perco_web.collect_events(today)
            elif self.data['selected_version'] == "zkteco":
                events = self.zkteco.collect_events(today)
            
            self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", events)
            self.con.commit()
            self.collectData(today)
            
        else:
            todayday = date.today()
            self.cursor.execute("DELETE FROM events WHERE created_at = ?;", (todayday, ))

            if self.data['selected_version'] == "perco":
                events = self.perco.collect_events(todayday)
            elif self.data['selected_version'] == "era":
                events = self.era.collect_events(todayday)
            elif self.data['selected_version'] == "rusguard":
                events = self.rusguard.collect_events(todayday)
            elif self.data['selected_version'] == "hikvision":
                events = self.hikvision.collect_events(todayday)
            elif self.data['selected_version'] == "perco_web":
                events = self.perco_web.collect_events(todayday)
            elif self.data['selected_version'] == "zkteco":
                events = self.zkteco.collect_events(todayday)
            
            self.cursor.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?)", events)
            self.con.commit()
            self.collectData(todayday)
            
        
        

    def sendData(self):
        today = date.today()
        if self.data['aonit_type'] == 'log':
            send= self.aonitLog.sendRequestToAonit(today)
        else:     
            send = self.aonitTp.sendRequestToAonit(today)
        print(send)
        if send['code'] == 200:
            self.showDialog("Данные успешно отправлены по адресу:"+send['url'])
        elif send['code'] == 500:
            self.showDialog("Проверьте подключение к сети. Сеть:"+send['url'])
        else:
            self.showDialog("Упс что то не так")
        

    def start(self):
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
        self.createBase()
        
        self.collectDataBtn.clicked.connect(self.collectData)
        self.pushDataBtn.clicked.connect(self.sendData)
        self.createDataBtn.clicked.connect(self.createData)
 
 
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    mw = MainWindow()
    task = Task(1)
    task.start()
    mw.start()
    mw.show()
    def closeApp():
        app.exec()
        task.done()
    sys.exit(closeApp())