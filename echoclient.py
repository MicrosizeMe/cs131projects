#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from __future__ import print_function

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver

import conf


class EchoClient(LineReceiver):
    end = "Bye-bye!"

    def connectionMade(self):
        sendString = raw_input("Write a command...")
        # print sendString
        self.sendLine(sendString)

    def dataReceived(self, data):
        print ("Server said: " + data)
        sendString = raw_input("Write a command...")
        self.sendLine(sendString)



class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def __init__(self):
        self.done = Deferred()


    def clientConnectionFailed(self, connector, reason):
        print('connection failed:', reason.getErrorMessage())
        self.done.errback(reason)


    def clientConnectionLost(self, connector, reason):
        print('connection lost:', reason.getErrorMessage())
        self.done.callback(None)



def main(reactor):
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', conf.PORT_NUM["Hamilton"], factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)
