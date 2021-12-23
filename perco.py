from win32com.client.dynamic import Dispatch
import xml.etree.ElementTree as ET
import datetime
from datetime import date



class Perco():

    def __init__(self):
        self.oPERCo = Dispatch("PERCo_S20_SDK.ExchangeMain")
        self.domEvent = Dispatch('Msxml2.DOMDocument.6.0')

    def createEventXml(self, xmlFileName,dateGet):
        requestType = ET.Element('documentrequest')

        beginperiod = f'{dateGet.day}.{dateGet.month}.{dateGet.year}'
        endinperiod = f'{dateGet.day}.{dateGet.month}.{dateGet.year}'

        beginperiodtime = '00:00:00'
        endperiodtime = '23:50:00'

        requestType.set('type','regevents')
        eventsreportSub = ET.SubElement(requestType,'eventsreport')
        eventsreportSub.set('beginperiod',beginperiod)
        eventsreportSub.set('endperiod',endinperiod)
        eventsreportSub.set('beginperiodtime',beginperiodtime)
        eventsreportSub.set('endperiodtime',endperiodtime)
        mydata = ET.tostring(requestType,encoding='unicode')
        myfile = open(xmlFileName,'w')
        myfile.write(mydata)

    def connectServer(self):
        Host = "127.0.0.1"
        Port = "211"
        Login = "ADMIN"
        Pass = ""
        iRet = self.oPERCo.SetConnect(Host, Port, Login, Pass)

        return iRet


    def loadEvents(self,dateGet):
        today = date.today()
        events = []
        self.connectServer()
        self.createEventXml('getEventsTemplate.xml',dateGet)
        self.domEvent.load('getEventsTemplate.xml')
        self.oPERCo.GetData(self.domEvent)
        self.domEvent.save('getEvents.xml')
        root_node = ET.parse('getEvents.xml').getroot()
        for tag in root_node.findall("eventsreport/events/event"): 
            f_areas_nameN = tag.get('f_areas_name')
            if f_areas_nameN == "Неконтролируемая территория":
                f_areas_name = "0"
            else:
                f_areas_name = "1"
            f_fio = tag.get('f_fio')
            f_iin = tag.get('tab_n')
            f_name_ev = tag.get('f_name_ev')
            f_date_ev = tag.get('f_date_ev')
            f_time_ev = tag.get('f_time_ev')
            f_date = f"{f_date_ev} {f_time_ev}"
            event = (
                f_iin,
                f_fio,
                f_areas_name,
                f_date,
                dateGet
            )
            if f_name_ev == 'Проход':
                events.append(event)
        
        return events