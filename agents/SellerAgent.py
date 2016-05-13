# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask
/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente
Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import sys
from flask import Flask
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from prettytable import PrettyTable

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
    data = PrettyTable(['Nombre', 'Modelo', 'Marca', 'Precio'])
    for res in queryResult:
        data.add_row([res['nombre'],
                      res['modelo'],
                      res['marca'],
                      res['precio']])
    print data


def findProducts(model=None, brand=None, min_price=0.0, max_price=sys.float_info.max):
    graph = Graph()
    graph.parse(ontologyFile, format='turtle')
    first = second = 0
    query = """
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
            FILTER("""

    if model is not None:
        query += """str(?modelo) = '""" + model + """'"""
        first = 1

    if brand is not None:
        if first == 1:
            query += """ && """
        query += """str(?marca) = '""" + brand + """'"""
        second = 1

    if first == 1 or second == 1:
        query += """ && """
    query += """?precio >= """ + str(min_price) + """ &&
                ?precio <= """ + str(max_price) + """  )}
                order by asc(UCASE(str(?nombre)))"""

    return graph.query(query)


def sell_products(urlProductsList):
    productList = []
    baseURL = 'http://www.owl-ontologies.com/ECSDIAmazon.owl#'
    for f in urlProductsList:
        productList.append(baseURL + f)

    # TODO Send 'vull-comprar' message to financialAgent


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # --------------------------------------- TEST ---------------------------------------------------------
    printProducts(findProducts())
    sell_products(['Producto_1', 'Producto_2'])

    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    # ab1 = Process(target=agentBehaviour, args=(queue,))
    # ab1.start()

    # Run server
    # app.run(host=hostname, port=port)

    # Wait behaviors
    # ab1.join()
    # print 'The End'