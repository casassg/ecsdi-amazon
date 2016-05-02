# -*- coding: utf-8 -*-

from flask import Flask
from rdflib import Graph


app = Flask(__name__)


@app.route('/')
def main_view():
    return find_products()


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


if __name__ == '__main__':
    app.run()
