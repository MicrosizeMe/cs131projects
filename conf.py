# A configuration file for the Twisted Places proxy herd

# Google Places API key
API_KEY="AIzaSyDWMr_PUlrgQ2ssarP7TK5CRtu3VlpMdMQ"

# TCP port numbers for each server instance (server ID: case sensitive)
# Please use the port numbers allocated by the TA.
PORT_NUM = {
    'Alford': 12000,
    'Ball': 12001,
    'Hamilton': 12002,
    'Holiday': 12003,
    'Welsh': 12004
}

# TCP host IPs for each server instance (server ID: case sensitive)
# These are all set to localhost, but for other purposes, these could
# be not on the same machine.
HOST_NAME = {
    'Alford': '127.0.0.1',
    'Ball': '127.0.0.1',
    'Hamilton': '127.0.0.1',
    'Holiday': '127.0.0.1',
    'Welsh': '127.0.0.1'
}

PROJ_TAG="Fall 2016"

logName = "alford.log"


# Project configuration files
AlfordConfig = {
    "name": "Alford",
    "serverPort": PORT_NUM["Alford"],
    "serverHost": HOST_NAME["Alford"] 
}
BallConfig = {
    "name": "Ball",
    "serverPort": PORT_NUM["Ball"],
    "serverHost": HOST_NAME["Ball"] 
}
HamiltonConfig = {
    "name": "Hamilton",
    "serverPort": PORT_NUM["Hamilton"],
    "serverHost": HOST_NAME["Hamilton"]
}
HolidayConfig = {
    "name": "Holiday",
    "serverPort": PORT_NUM["Holiday"],
    "serverHost": HOST_NAME["Holiday"]
}
WelshConfig = {
    "name": "Welsh",
    "serverPort": PORT_NUM["Welsh"],
    "serverHost": HOST_NAME["Welsh"]
}


alfordSiblings = [
    WelshConfig,
    HamiltonConfig
]
ballSiblings = [
    HolidayConfig,
    WelshConfig
]
hamiltonSiblings = [
    AlfordConfig,
    HolidayConfig
]
holidaySiblings = [
    HamiltonConfig,
    BallConfig
]
welshSiblings = [
    BallConfig,
    AlfordConfig
]