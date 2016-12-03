from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import time
import conf
import requests
import json
import copy

import logging 

LogName = conf.logName

logging.basicConfig(filename=LogName, level=logging.DEBUG)

def printMessage(header, message):
    logging.info("" + header + "@" + str(time.time()) + ": " + message)


# Primary json data format for line:
# {'timestamp': time, 'client': 'String', 'location': 'string', 'source': ['serverName']}
# self.factory.siblingConfigs entry format
# {
#   "name": "ServerName",
#   "serverPort": portNumber,
#   "serverHost": hostname,
#   "protocol": protocol
# }
class PlacesServerServer(LineReceiver):

    def __init__(self, factory, partnerName):
        self.factory = factory
        self.partnerName = partnerName 

    def connectionMade(self):
        for serverConfig in self.factory.siblingConfigs:
            if serverConfig["name"] == self.partnerName:
                serverConfig["protocol"] = self
                break
        printMessage(self.factory.serverName, "Found peer server " + self.partnerName + "!")

        # Once we've connected, we should establish the thing exists.

    def connectionLost(self, reason):
        for serverConfig in self.factory.siblingConfigs:
            if serverConfig["name"] == self.partnerName:
                serverConfig["protocol"] = None
                break
        printMessage(self.factory.serverName, "Server " + self.partnerName + " dropped!")

    # Servers send pure json data to and from each other for easy encoding and storage.
    def lineReceived(self, line):
        jsonLine = json.loads(line)
        source = jsonLine['source']
        printMessage(self.factory.serverName, "Received interserver data from " + ','.join(source))
        # propagate to neighbors
        self.propagateMessage(jsonLine)
        # Save the message
        self.saveMessage(jsonLine)

    # Code useful in propagating messages. If the jsonField has a source key, 
    # don't propagate it to any server in the source list (or you echo). Otherwise, propagate 
    # to adjacent servers not on the list
    # Note that this object we pass is NOT cloned, so use of this function from
    # the outside should clone the object to avoid having data appended.
    def propagateMessage(self, jsonLine):
        newSource = []
        if jsonLine.has_key("source"): 
            newSource = jsonLine["source"]
        newSource.append(self.factory.serverName)
        jsonLine["source"] = newSource
        for serverConfig in self.factory.siblingConfigs:
            if serverConfig["name"] not in newSource and serverConfig.has_key("protocol") and serverConfig["protocol"] != None:
                serverConfig["protocol"].sendLine(json.dumps(jsonLine))
                printMessage(self.factory.serverName, "Sent interserver data to " + serverConfig["name"])

    # Saves a received json line. Should only really be used for interserver communication
    def saveMessage(self, jsonLine):
        if jsonLine.has_key("source"):
            del jsonLine["source"]
        self.factory.clients[jsonLine["client"]] = jsonLine


class PlacesClientServer(LineReceiver):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        printMessage(self.factory.serverName, "Made connection with client.")

    def connectionLost(self, reason):
        printMessage(self.factory.serverName, "Lost connection with client.")

    def lineReceived(self, line):
        printMessage(self.factory.serverName, "Line received: " + line)
        args = line.strip().split()
        # Subsequent action depends on the first argument.
        if args[0] == "IAMAT":
            returnArg = self.saveLocationData(args)
            if returnArg.has_key("error"):
                self.sendLine(returnArg["error"])
            else:
                # Send client a response.
                self.sendATResponse(args, returnArg)
                # Propagate data to sibling servers.
                self.beginPropagation(returnArg)
        elif args[0] == "WHATSAT":
            # Approach taken: If we don't find it on this node, pretend
            # that it's not here. It might be on another node and 
            # it might get here soon, but from our perspective, it
            # might as well not exist at this moment in time. 
            returnArg = self.getWHATSATData(args)
            if returnArg.has_key("error"):
                self.sendLine(returnArg["error"])
            else:
                printMessage(self.factory.serverName, "Sending data: " + returnArg["data"])
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
            printMessage(self.factory.serverName, "Sending line: " + message)
            self.sendLine(message)

    def beginPropagation(self, returnArg): 
        # Sends the returnArg object (really a copy of it)
        sendArgument = copy.deepcopy(returnArg)
        self.factory.beginPropagation(returnArg)
        



class PlacesFactory(ClientFactory):

    # siblingConfigs entry format
    # {
    #   "name": "ServerName",
    #   "serverPort": portNumber,
    #   "serverHost": hostname,
    #   "protocol": protocol
    # }
    # 
    # serverName is just the name of the server, eg Alford
    def __init__(self, serverName, siblingConfigs, myConfig):
        # maps user clients to location data.
        self.clients = {} 
        # siblingConfigs will have its items appended with a field storing
        # the connection data, to be stored in protocol.
        self.siblingConfigs = siblingConfigs # Lists adjacent server nodes. 
        self.serverName = serverName
        self.config = myConfig
        printMessage(self.serverName, "Staring server " + serverName)

    def buildProtocol(self, addr):
        # We only care about the attributes of addr.
        addr = vars(addr)
        for sibling in self.siblingConfigs:
            # In this case, if the connecting client has the 
            # same port and hostname as one of our siblings, 
            # then it's actually a server that started after we did.
            # Make a different protocol for it.
            if sibling["serverPort"] == addr["port"] \
                    and sibling["serverHost"] == addr["host"]: 
                return PlacesServerServer(self, sibling["name"])

        return PlacesClientServer(self)

    def clientConnectionFailed(self, connector, reason):
        if reason.getErrorMessage() == "Couldn't bind: 10048: Only one usage of each socket address (protocol/network address/port) is normally permitted.":
            print("Connection failed: Odds are good that there's some TCP timeout on this port or the sever isn't up yet. You may have to restart this node later.")
            print("Port in question: " + 
                str(connector.getDestination().host) + 
                ":" + 
                str(connector.getDestination().port)
            )

    # This code is called when we initially create the factory after the reacter
    # is ready. 
    # As a consequence, since siblings is set and since
    # buildProtocol is created, we can attempt to connect to our
    # sibling nodes now. Do that. 
    def connectSiblings(self, passedReactor):
        for sibling in self.siblingConfigs: 
            # 5 second timeout for connections.
            print("Attempting to connect to " + sibling["name"])
            passedReactor.connectTCP(
                sibling["serverHost"], 
                sibling["serverPort"], 
                self, 
                5,
                (self.config["serverHost"], self.config["serverPort"])
            ).getDestination()

    # Sends the object to all adjacent servers. Does this by calling
    # one of the propagateMessage functions of one of the server connections.
    def beginPropagation(self, object):
        for sibling in self.siblingConfigs:
            if sibling.has_key("protocol") and sibling["protocol"] != None:
                sibling["protocol"].propagateMessage(object)
                break

# Alford = PlacesFactory("Alford", copy.deepcopy(conf.alfordSiblings), copy.deepcopy(conf.AlfordConfig))
# Ball = PlacesFactory("Ball", copy.deepcopy(conf.ballSiblings), copy.deepcopy(conf.BallConfig))
# Hamilton = PlacesFactory("Hamilton", copy.deepcopy(conf.hamiltonSiblings), copy.deepcopy(conf.HamiltonConfig))
# Holiday = PlacesFactory("Holiday", copy.deepcopy(conf.holidaySiblings), copy.deepcopy(conf.HolidayConfig))
# Welsh = PlacesFactory("Welsh", copy.deepcopy(conf.welshSiblings), copy.deepcopy(conf.WelshConfig))

# # Alford.connectSiblings(reactor)
# reactor.listenTCP(conf.PORT_NUM["Alford"], Alford)
# Ball.connectSiblings(reactor)
# reactor.listenTCP(conf.PORT_NUM["Ball"], Ball)
# Hamilton.connectSiblings(reactor)
# reactor.listenTCP(conf.PORT_NUM["Hamilton"], Hamilton)
# Holiday.connectSiblings(reactor)
# reactor.listenTCP(conf.PORT_NUM["Holiday"], Holiday)
# Welsh.connectSiblings(reactor)
# reactor.listenTCP(conf.PORT_NUM["Welsh"], Welsh)

# reactor.run()