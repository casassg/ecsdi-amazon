# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def sendProducts():
    # TODO Receive communication of send something and send it.
    print "Send Products"


def recordDeliveries():
    # TODO Record Receive communication of availability discussion and record deliveries.
    print "Record Deliveries"


def requestTransport():
    # TODO Discuss with Transport Dealer.
    print "Request Transport"


class LogisticHubAgent:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
