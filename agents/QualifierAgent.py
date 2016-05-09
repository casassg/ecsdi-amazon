# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


def recommend():
    # TODO Recommend some products to user.
    print "Recommend"


def value():
    # TODO Value some products by user.
    print "Value"


class FinancialAgent:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
