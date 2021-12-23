import string,random
import requests
import arrow
import sqlite3
from datetime import datetime,date
import json
import os.path
import win32com.client
import constants


KalkanCOMTest = win32com.client.Dispatch("KalkanCryptCOMLib.KalkanCryptCOM.2")
KalkanCOMTest.Init()


class IntegrationAonit():

    

    def __init__(self):
        if os.path.exists('conf.json') == False:
            with open('conf.json', 'w+') as f:
                data = {"ip_addresses": [
                        "10.245.12.102",
                        "10.245.12.67"
                    ],
                    "mac_addresses": ["000B3D000058","000B3A007F26"],
                    "gost_pass": "null",
                    "gost_path": "null",
                    "selected_ip_address": "10.245.12.67",
                    "login": "null",
                    "password": "null",
                    "aonit_server_ip": "127.0.0.1"}
                json.dump(data,f, ensure_ascii=False, indent=4)
            with open('conf.json') as f:
                self.data = json.load(f)
        else:
            with open('conf.json') as f:
                self.data = json.load(f)

        self.login = self.data['login']
        self.path = self.data['gost_path']
        self.password = self.data['password']
        self.con = sqlite3.connect("mydb.db",check_same_thread=False) 
        self.cursor = self.con.cursor()
        self.url=self.data['selected_ip_address']
        self.headers = {'content-type': 'application/soap+xml; charset=utf-8'}
        self.dateToBody = arrow.get(datetime.now())

    def sendRequestToAonit(self,todayday): 
        try:
            
            response = requests.get(self.url,headers=self.headers)
            print(self.login,self.password,self.url)
        
            self.cursor.execute("SELECT * FROM events WHERE created_at = ?;",(todayday,))
            events = self.cursor.fetchall()
          
            def iinIterable():
                string = ''
                for event in events:
                    string += f"<value>{event[1]}</value>"

                return string

            def eventCodeIterable():
                string = ''
                for event in events:
                    string += f"<value>{event[3]}</value>"

                return string

            def datetimeIterable():
                string = ''
                for event in events:
                    string += f"<value>{event[4]}</value>"

                return string


            def testItrable():
                string = ''
                for event in events:
                    string += f"<value>Не задано</value>"

                return string

            body = f"""
                <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" wsu:Id="id-0002">
                <m:SendMessage xmlns:m="http://bip.bee.kz/SyncChannel/v10/Types">
                    <request>
                        <requestInfo>
                            <messageId>String</messageId>
                            <serviceId>EKyzmetUniversalService</serviceId>
                            <messageDate>{self.dateToBody}</messageDate>
                            <sender>
                                <senderId>{self.login}</senderId>
                                <password>{self.password}</password>
                            </sender>
                            <properties>
                                <key></key>
                                <value></value>
                            </properties>
                        </requestInfo>
                        <requestData>
                            <data>
                            <Request serviceName="sendEventFromACSList" xsi:noNamespaceSchemaLocation="EKyzmetUniversalService.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                            <param>
                                <key>ИИН</key>
                                <type>String</type>
                                <values>
                                    {iinIterable()}							
                                </values>
                    
                            </param>
                            <param>
                                <key>Событие</key>
                                <type>String</type>
                                <values>
                                    {eventCodeIterable()}
                                </values>
                            </param>					
                            <param>
                                <key>Время</key>
                                <type>String</type>
                                <values>
                                    {datetimeIterable()}
                                </values>
                            </param>					
                            <param>
                                <key>БИН</key>
                                <type>String</type>
                                <values>
                                    {testItrable()}
                                </values>
                            </param>	
                            <param>
                                <key>Номер этажа</key>
                                <type>String</type>
                                <values>
                                    {testItrable()}
                                </values>
                            </param>
                            <param>
                                <key>Наименование здания</key>
                                <type>String</type>
                                <values>
                                    {testItrable()}
                                </values>
                            </param>												
                        </Request>
                            </data>
                        </requestData>
                    </request>
                </m:SendMessage>
        </soap:Body></soap:Envelope>
        """
        
            inData = body  
            


            KalkanCOMTest.LoadKeyStore(constants.KCST_PKCS12,self.data["gost_pass"],self.path, 'test')
            err = KalkanCOMTest.GetLastError()
            if err > 0:
                print(" Error: " + str(hex(int(err))) + "\n" )
            
            signNodeId = "id-0002"
            outData = ""
            outSign = KalkanCOMTest.SignWSSE("test", 0, inData,signNodeId,outData)
            
            KalkanCOMTest.XMLFinalize()
        
            with open('xml-format.xml', 'w') as xml:
                xml.write(outSign)
            
            strErr, err = KalkanCOMTest.GetLastErrorString()
            if err > 0:
                print(" Error: " + str(hex(int(err))) + "\n" + strErr.replace("\n","\r\n"))


            outSign = outSign.encode('utf-8')
            response = requests.post(self.url,data=outSign, headers=self.headers)
            responseTurple = (0, "0", "12.08.2002")
            if response.status_code == 200:
                responseTurple = (response.status_code, response.text,todayday)
                self.cursor.execute("INSERT INTO responses VALUES (NULL,?,?,?)", responseTurple)
                self.con.commit()
              
                print(f'Сообщение успешно отправлено КОД:{response.status_code}')
                print(response.text)
            else:
                responseTurple = (response.status_code, response.text, todayday)
                self.cursor.execute("INSERT INTO responses VALUES (NULL,?,?,?)", responseTurple)
                self.con.commit()
               
                print(response.text)
                print(f'Есть ошибка КОД:{response.status_code}')
            return {
                "code": 200,
                "url": self.url
            }
        except requests.exceptions.ConnectionError:
            return {
                "code": 500,
                "url": self.url
            }

      