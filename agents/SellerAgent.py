# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""

from flask import Flask
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.OntologyNamespaces import TIO

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9025

# Agent Namespace
agn = Namespace("http://www.agentes.org#")  # Revisar url -> definir nuevo espacio de nombre incluyendo agentes nuestros

# Message Count
messageCount = 0

# Data Agent
SellerAgent = Agent('AgenteVendedor',
                    agn.AgenteVendedor,
                    'http://%s:%d/comm' % (hostname, port),
                    'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)

# Global triplestore graph
dsGraph = Graph()

# Queue
queue = Queue()

# Flask app
app = Flask(__name__)


# AGENT FUNCTIONS ------------------------------------------------------------------------------------------

@app.route("/comm")
def communication():
    """
    Communication Entrypoint
    """

    global dsGraph
    global messageCount
    pass


@app.route("/Stop")
def stop():
    """
    Entrypoint to the agent
    :return: string
    """

    tidyUp()
    shutdown_server()
    return "Stopping server"


def tidyUp():
    """
    Previous actions for the agent.
    """

    # TODO Actions

    pass


def agentBehaviour(queue):
    """
    Agent Behaviour in a concurrent thread.

    :param queue: the queue
    :return: something
    """

    # TODO Behaviour

    pass


# DETERMINATE AGENT FUNCTIONS ------------------------------------------------------------------------------

ontologyFile = open('../data/data')


def printProducts(queryResult):
    products = []
    for res in queryResult:
        prod = 'NOMBRE: ' + res['nombre'] + ' ' + \
               'MODELO: ' + res['modelo'] + ' ' + \
               'MARCA: ' + res['marca'] + ' ' + \
               'PRECIO: ' + res['precio'] + ' '
        products.append(prod)

    for prod in products:
        print prod


def findAllProducts():
    graph = Graph()
    graph.parse(ontologyFile, format='turtle')
    printProducts(graph.query(
        """
        prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix xsd:<http://www.w3.org/2001/XMLSchema#>
        prefix default:<http://www.owl-ontologies.com/ECSDIAmazon.owl#>
        prefix owl:<http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?nombre ?marca ?modelo ?precio
        where {
            ?producto a default:Producto .
            ?producto default:Nombre ?nombre .
            ?producto default:Marca ?marca .
            ?producto default:Modelo ?modelo .
            ?producto default:Precio ?precio
            }
        """))


def findProductsBetweenPrices(min_price, max_price):
    graph = Graph()
    graph.parse(ontologyFile, format='turtle')
    printProducts(graph.query(
        """
        prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix xsd:<http://www.w3.org/2001/XMLSchema#>
        prefix default:<http://www.owl-ontologies.com/ECSDIAmazon.owl#>
        prefix owl:<http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?nombre ?marca ?modelo ?precio
        where {
            ?producto a default:Producto .
            ?producto default:Nombre ?nombre .
            ?producto default:Marca ?marca .
            ?producto default:Modelo ?modelo .
            ?producto default:Precio ?precio .
            FILTER(
                ?precio >= """ + str(min_price) + """ &&
                ?precio <= """ + str(max_price) + """
            )
            }
        """))


def findProductsOfBrand(brand):
    graph = Graph()
    graph.parse(ontologyFile, format='turtle')
    printProducts(graph.query(
        """
        prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix xsd:<http://www.w3.org/2001/XMLSchema#>
        prefix default:<http://www.owl-ontologies.com/ECSDIAmazon.owl#>
        prefix owl:<http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?nombre ?marca ?modelo ?precio
        where {
            ?producto a default:Producto .
            ?producto default:Nombre ?nombre .
            ?producto default:Marca ?marca .
            ?producto default:Modelo ?modelo .
            ?producto default:Precio ?precio .
            FILTER(
                str(?marca) = '""" + brand + """'
            )
            }
        """))


def sell_products():
    # TODO We need to communicate with Financial Agent
    print "Sell"


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # --------------------------------------- TEST ---------------------------------------------------------
    # findAllProducts()
    # findProductsBetweenPrices(250.0, 400.0)
    findProductsOfBrand('Google')

    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    # ab1 = Process(target=agentBehaviour, args=(queue,))
    # ab1.start()

    # Run server
    # app.run(host=hostname, port=port)

    # Wait behaviors
    # ab1.join()
    # print 'The End'
