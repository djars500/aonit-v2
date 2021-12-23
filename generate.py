import constants
import win32com.client
KalkanCOMTest = win32com.client.Dispatch("KalkanCryptCOMLib.KalkanCryptCOM.2")
KalkanCOMTest.Init()


KalkanCOMTest.LoadKeyStore(constants.KCST_PKCS12,"123456zZ","GOSTKNCA_232d3c8713081bef3a2ef83dccfe45824d3748cb.p12", 'test')

inData = f"""
                <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" wsu:Id="id-0002">
                <m:SendMessage xmlns:m="http://bip.bee.kz/SyncChannel/v10/Types">
                    <request>
                        <requestInfo>
                            <messageId>String</messageId>
                            <serviceId>EKyzmetUniversalService</serviceId>
                            <messageDate></messageDate>
                            <sender>
                                <senderId></senderId>
                                <password></password>
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
                                  						
                                </values>
                    
                            </param>
                            <param>
                                <key>Событие</key>
                                <type>String</type>
                                <values>
                                  
                                </values>
                            </param>					
                            <param>
                                <key>Время</key>
                                <type>String</type>
                                <values>
                                  
                                </values>
                            </param>					
                            <param>
                                <key>БИН</key>
                                <type>String</type>
                                <values>
                                   
                                </values>
                            </param>	
                            <param>
                                <key>Номер этажа</key>
                                <type>String</type>
                                <values>
                                  
                                </values>
                            </param>
                            <param>
                                <key>Наименование здания</key>
                                <type>String</type>
                                <values>
                                 
                                </values>
                            </param>												
                        </Request>
                            </data>
                        </requestData>
                    </request>
                </m:SendMessage>
        </soap:Body></soap:Envelope>
        """
err = KalkanCOMTest.GetLastError()
if err > 0:
    print(" Error: " + str(hex(int(err))) + "\n" )

signNodeId = "id-0002"
outData = ""
outSign = KalkanCOMTest.SignWSSE("test", 0, inData,signNodeId,outData)

KalkanCOMTest.XMLFinalize()

with open('generated-cer.xml', 'w') as xml:
    xml.write(outSign)

strErr, err = KalkanCOMTest.GetLastErrorString()
if err > 0:
    print(" Error: " + str(hex(int(err))) + "\n" + strErr.replace("\n","\r\n"))
