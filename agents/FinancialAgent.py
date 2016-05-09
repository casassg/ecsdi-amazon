# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def payDelivery():
    # TODO Record the purchase.
    print "PayDelivery"


def confirmTransfer():
    # TODO Confirm the transfer, deliver receipt and communicate with Products Agent.
    print "ConfirmTransfer"


class FinancialAgent:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
