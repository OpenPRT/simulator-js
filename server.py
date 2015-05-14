from twisted.internet import protocol, reactor
from threading import Timer
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from json import JSONEncoder

import random
import time
import cgi
import json
import uuid

import podcar

podcars = {}
tickets = dict()

# Ticket
class Ticket(JSONEncoder):
    status = 'requested'
    start = []
    requests = 0
    podcar = None
    def __init__(self, location):
        self.start = location
    def asArray(self):
        response = {
            'status':self.status,
            'start':self.start
        }
        if self.podcar is not None:
            response['podcar_id'] = self.podcar.vin
            if self.status == 'accepted':
                response['time'] = self.podcar.timeToLocation(self.start)

        return response


# Server

class Server(protocol.Protocol):
    def connectionMade(self):
        self._peer = self.transport.getPeer()
    def dataReceived(self, data):
        print('Server heard: '+data)
          # method:id:messagedata
        data_info = json.loads(data)

        if data_info['method']=='AVSTART':
            pod_id = data_info['pod_id']
            print('PodCar connected: '+pod_id)
            podcars[pod_id] = podcar.PodCar(data_info['pod_id'],data_info['type'])
            podcars[pod_id].conn = self.transport
        elif data_info['method']=="AVACCEPT":
            print('PodCar accepted: '+data_info['pod_id'])
            ticket_id = uuid.UUID(data_info['ticket_id'])
            if ticket_id in tickets: # If request hasn't already been fulfilled
                if tickets[ticket_id].status == "requested":
                    tickets[ticket_id].status = "accepted"
                    tickets[ticket_id].podcar = podcars[data_info['pod_id']]
                    tickets[ticket_id].podcar.conn.write(json.dumps({
                        'method':'GO',
                        'ticket':tickets[ticket_id].asArray()
                    }))
        else:
            return

    def createRequestTicket(self,location):
        new_id = uuid.uuid4()
        while new_id in tickets:
            new_id = uuid.uuid4()
        ticket = Ticket(location);
        for pod_id in podcars.keys():
            podcars[pod_id].conn.write(json.dumps({
                'method':'REQUEST',
                'ticket_id':str(new_id),
                'location':[
                    str(location[0]),
                    str(location[1])
                ]
            }))
            ticket.requests += 1;

        tickets[new_id] = ticket;
        print("Created new ticket: "+str(new_id))
        return new_id;

server = Server();
class ServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return server

# Server Setup

Timer(0.5, podcar.addPodCar, args=["001","A"]).start()
Timer(5.0, podcar.addPodCar, args=["002","A"]).start()
reactor.listenTCP(1600, ServerFactory())

# ServerAPI for Simulator front end.

class ServerAPI(Resource):
    def render_GET(self, request):
        request.setHeader("content-type", "application/json")

        ticket_id = uuid.UUID(request.args["ticket_id"][0])
        if ticket_id in tickets:
            response = {
                'status':'OK',
                'ticket_id':str(ticket_id),
                'ticket':tickets[ticket_id].asArray()
            }
        else:
            # Setup http response code
            response = {
                'status':'Unknown'
            }
        return json.dumps(response)

    def render_POST(self, request):
        request.setHeader("content-type", "application/json")

        print("New request from: "+json.dumps(request.args))
        new_id = server.createRequestTicket(request.args["location[]"])
        response = {
            'status':'OK',
            'ticket_id':str(new_id),
            'ticket':tickets[new_id].asArray()
        }
        #return '<html><body>You submitted: %s</body></html>' % (cgi.escape(request.args["the-field"][0]),)
        return json.dumps(response)


root = Resource()
root.putChild("ticket", ServerAPI())
factory = Site(root)
reactor.listenTCP(1601, factory)
reactor.run()
