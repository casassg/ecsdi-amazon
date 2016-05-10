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
agn = Namespace("http://www.agentes.org#")

# Message Count
messageCount = 0

# Data Agent
PersonalAgent = Agent('AgenteSimple',
                      agn.AgenteSimple,
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

def find_products():
    global products
    graph = Graph()

    # TODO Load ontology file
    ontologyFile = open('../data/data')
    graph.parse(ontologyFile, format='turtle')

    # TODO Get graph with information
    queryResult = graph.query(
        """
        prefix tio:<http://purl.org/tio/ns#>
        prefix geo:<http://www.w3.org/2003/01/geo/wgs84_pos#>
        prefix dbp:<http://dbpedia.org/ontology/>

        Select ?f
        where {
            ?f rdf:type dbp:Producto .
            }
        """,
        initNs=dict(tio=TIO))

    # TODO Analyse query results (indicate what columns we want to show)
    for res in queryResult:
        products = res

    print products


def sell_products():

    # TODO We need to communicate with Financial Agent
    print "Sell"


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':

    find_products()

    # Run behaviors
    #ab1 = Process(target=agentBehaviour, args=(queue,))
    #ab1.start()

    # Run server
    #app.run(host=hostname, port=port)

    # Wait behaviors
    #ab1.join()
    #print 'The End'
