# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def distributeDelivery():
    # TODO Get products availability and send them.
    print "Distribute Delivery"


def recordExternalProduct():
    # TODO Record product of an external seller.
    print "RecordExternalProduct"


class ProductsAgent:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
