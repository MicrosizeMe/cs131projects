from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import conf
import json

conf.logName = "hamilton.log"
import Servers


# Alford = Servers.PlacesFactory("Alford", conf.alfordSiblings, conf.AlfordConfig)
# Ball = Servers.PlacesFactory("Ball", conf.ballSiblings, conf.BallConfig)
Hamilton = Servers.PlacesFactory("Hamilton", conf.hamiltonSiblings, conf.HamiltonConfig)
# Holiday = Servers.PlacesFactory("Holiday", conf.holidaySiblings, conf.HolidayConfig)
# Welsh = Servers.PlacesFactory("Welsh", conf.welshSiblings, conf.WelshConfig)

# Alford.connectSiblings(reactor)
# Ball.connectSiblings(reactor)
Hamilton.connectSiblings(reactor)
# Holiday.connectSiblings(reactor)
# Welsh.connectSiblings(reactor)

# reactor.listenTCP(conf.PORT_NUM["Alford"], Alford)
# reactor.listenTCP(conf.PORT_NUM["Ball"], Ball)
reactor.listenTCP(conf.PORT_NUM["Hamilton"], Hamilton)
# reactor.listenTCP(conf.PORT_NUM["Holiday"], Holiday)
# reactor.listenTCP(conf.PORT_NUM["Welsh"], Welsh)
reactor.run()