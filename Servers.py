from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import time
import conf
import requests
import json

def printMessage(message):
    print("" + str(time.time()) + ": " + message)

class Places(LineReceiver):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        printMessage("Made connection...")

    def connectionLost(self, reason):
        printMessage("Lost connection...")

    def lineReceived(self, line):
        printMessage("Line recieved: " + line)
        args = line.strip().split()
        # Subsequent action depends on the first argument.
        print args
        if args[0] == "IAMAT":
            print "Iamat!"
            returnArg = self.saveLocationData(args)
            if returnArg.has_key("error"):

                self.sendLine(returnArg["error"])
            else:
                self.sendATResponse(args, returnArg)
        elif args[0] == "WHATSAT":
            # Approach taken: If we don't find it on this node, pretend
            # that it's not here. It might be on another node and 
            # it might get here soon, but from our perspective, it
            # might as well not exist at this moment in time. 
            returnArg = self.getWHATSATData(args)
            if returnArg.has_key("error"):
                self.sendLine(returnArg["error"])
            else:
                printMessage("Sending data: " + returnArg["data"])
                self.sendLine(returnArg["data"])

    # def handle_CHAT(self, message):
    #     message = "<%s> %s" % (self.client, message)
    #     for client, protocol in self.clients.iteritems():
    #         if protocol != self:
    #             protocol.sendLine(message)

    def saveLocationData(self, args):
        returnArg = {}
        if len(args) != 4:
            returnArg["error"] = "invalid arguments"
            return returnArg
        # Save data
        client = args[1]
        location = args[2].replace('+', " +").replace("-", " -").strip().split()
        if len(location) != 2:
            returnArg["error"] = "invalid coordinate"
            return returnArg
        locationString = location[0] + ',' + location[1]
        timestamp = float(args[3])
        returnArg["client"] = client
        returnArg["location"] = locationString
        returnArg["timestamp"] = timestamp
        self.factory.clients[client] = returnArg
        # print returnArg
        print self.factory.clients
        return returnArg

    def getWHATSATData(self, args):
        returnArg = {}
        if len(args) != 4:
            returnArg["error"] = "invalid arguments"
            return returnArg
        # Get parameters
        client = args[1]
        
        radius = int(args[2])
        if radius > 50:
            returnArg["error"] = "Radius too large"
            return returnArg

        upperBound = int(args[3])
        if upperBound > 20:
            returnArg["error"] = "Upper bound too large"
            return returnArg

        # Get client
        clientInfo = {};
        if not self.factory.clients.has_key(client):
            returnArg["error"] ="No such client"
            return returnArg
        else :
            clientInfo = self.factory.clients[client]
        # Get data
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + 
                "location=" + clientInfo["location"] +
                "&radius=" + str(radius) +
                "&key=" + conf.API_KEY
        )
        jsonEncoding = r.json()
        # Process data
        # Remove extra requests.
        if not jsonEncoding.has_key("results"):
            returnArg["error"] = "Malformed request."
            return returnArg
        jsonEncoding["results"] = jsonEncoding["results"][:upperBound]
        # Pack into text
        jsonText = json.dumps(jsonEncoding, indent=4, sort_keys=False)
        text = "\n".join(filter(None, jsonText.strip().split('\n'))) + "\n\n"
        returnArg["data"] = text
        return returnArg
 


    def sendATResponse(self, args, returnArg):
        if returnArg != None and not returnArg.has_key("error"):
            timestamp = None
            if (time.time() - returnArg["timestamp"] >= 0):
                timestamp = "+" + str(time.time() - returnArg["timestamp"])
            else:
                timestamp = "-" + str(time.time() - returnArg["timestamp"])
            message = ("AT " + self.factory.serverName + 
                    " " + str(time.time() - returnArg["timestamp"]) + 
                    " " + " ".join(args[1:])
            )
            printMessage("Sending line: " + message)
            self.sendLine(message)

    # def propogateData(self, )



class PlacesFactory(Factory):

    def __init__(self, serverName, ):
        self.clients = {} # maps user clients to Chat instances
        self.siblings = [] # Lists adjacent server nodes
        self.serverName = serverName
        printMessage("Staring server " + serverName)

    def buildProtocol(self, addr):
        return Places(self)

reactor.listenTCP(8000, PlacesFactory("Alford"))
reactor.run()