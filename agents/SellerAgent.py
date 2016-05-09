# -*- coding: utf-8 -*-

from flask import Flask
from rdflib import Graph

app = Flask(__name__)


def find_products():
    global products
    graph = Graph()

    # TODO Load ontology file
    ontologyFile = open('')
    graph.parse(ontologyFile, format='turtle')

    # TODO Get graph with information
    queryResult = graph.query()

    # TODO Analyse query results (indicate what columns we want to show)
    for res in queryResult:
        products = res['column']

    print products


def sell_products():
    # TODO We need to communicate with Financial Agent
    print "Sell"


class SellerAgent:
    def __init__(self):
        pass

    if __name__ == '__main__':
        app.run()
