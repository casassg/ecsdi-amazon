# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def requestOffer():
    # TODO Request Offer.
    print "Request Offer"


def sendCounterOffer():
    # TODO Send Counter Offer.
    print "Send Counter Offer"


def valueOffer():
    # TODO Value Offer.
    print "Value Offer"


def acceptOffer():
    # TODO Accept Offer.
    print "Accept Offer"


class TransportDealer:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
