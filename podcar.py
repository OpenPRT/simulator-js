from thread import start_new_thread

import json
import socket

class PodCar():
    vin = None
    type = 'A'
    conn = None
    def __init__(self,start_vin, start_type):
        self.vin = start_vin
        self.type = start_type

    def timeToLocation(self,location):
        return 500

class PodCarServer():
    vin = '' #Unique identifier for PodCar
    type = 'A' #A-Passenger
    status = 'connecting'
    # Ready
    # Accepted
    # Coming
    # Arrived
    # Going
    # Done
    location = []
    def __init__(self, start_vin, start_type):
        self.vin = start_vin
        self.type = start_type
    def receivedData(self,data,conn):
        print('PodCar Received: '+data)
        data_info = json.loads(data)
        if data_info['method']=='REQUEST':
            if self.status == 'ready':
                self.status == 'accepted'
                conn.send(json.dumps({
                    'method':'AVACCEPT',
                    'ticket_id':data_info['ticket_id'],
                    'pod_id':self.vin,
                    'location':self.location,
                    'type':self.type
                }))
        elif data_info['method'] == 'GO':
            self.status = 'coming'
            print('PodCar '+self.vin+' is Going')


def addPodCar(vin,type):
    podcar = PodCarServer(vin,type)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 1600))
    start_new_thread(podCarThread ,(s,podcar,))

#Function for handling connections. This will be used to create threads
def podCarThread(conn,podcar):
    #Sending message to connected client
    conn.send(json.dumps({
        'method':'AVSTART',
        'pod_id':podcar.vin,
        'type':podcar.type
    }));
    podcar.status = 'ready'

    #infinite loop so that function do not terminate and thread do not end.
    while 1:
        #Receiving from client
        data = conn.recv(1024)
        podcar.receivedData(data,conn)

    #came out of loop
