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


class SellerAgent:
    def __init__(self):
        pass

    @app.route('/')
    def main_view(self):
        return find_products()

    if __name__ == '__main__':
        app.run()
