import pyodbc 
class RusGuardApi():

   def __init__(self):
      self.conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=VDSWIN2K19\RUSGUARD;'
                      'Database=RusGuardDB;'
                      'Trusted_Connection=yes;')
      self.cursor = self.conn.cursor()

   def getEvents(self):
      events = []
      eventsExecute = self.cursor.execute('SELECT DateTime,Message,EmployeeID FROM [dbo].[Log]')
      eventsFetch = eventsExecute.fetchall()
      for event in eventsFetch:
         userExecute = self.cursor.execute(f"SELECT TableNumber,FirstName,SecondName,LastName FROM [dbo].[Employee] WHERE [_id]='{event[2]}'")
         user = userExecute.fetchone()
         events.append(
            (
               user[0],
               event[0],
               event[1]
            )
         )
      return events


rusGuardApi = RusGuardApi()

events = rusGuardApi.getEvents()
print(events)

   
   