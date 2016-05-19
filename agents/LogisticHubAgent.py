# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import time
import datetime
from flask import Flask
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph, URIRef, RDF, Literal
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.OntologyNamespaces import ECSDI

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9035

# Agent Namespace
agn = Namespace("http://www.agentes.org#")  # Revisar url -> definir nuevo espacio de nombre incluyendo agentes nuestros

# Message Count
messageCount = 0

# Data Agent
LogisticsAgent = Agent('AgenteLogistics',
                       agn.AgenteLogistics,
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

    global queue
    queue.add(0)

    pass


def agentBehaviour(queue):
    """
    Agent Behaviour in a concurrent thread.

    :param queue: the queue
    :return: something
    """

    fin = False
    while not fin:
        while queue.empty():
            pass
        v = queue.get()
        if v == 0:
            fin = True
        else:
            print v

    pass


# DETERMINATE AGENT FUNCTIONS ------------------------------------------------------------------------------

def sendProducts():
    # TODO Receive communication of send something and send it.
    print("Send Products")


def recordDeliveries():
    # TODO Record Receive communication of availability discussion and record deliveries.
    print("Record Deliveries")


def requestTransport():
    # TODO Discuss with Transport Dealer.
    print("Request Transport")


def dateToMillis(date):
    return int(round((date - datetime.datetime(1970, 1, 1)).total_seconds())) * 1000.0


def writeSends(productList, deliverDate):
    URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    n = int(round(time.time() * 1000))
    data = URI + "Envio_" + str(n)

    ontologyFile = open('../data/data')

    gm = Graph()
    gm.parse(ontologyFile, format='turtle')
    gm.add((URIRef(data), RDF.type, ECSDI.Envio))
    gm.add((URIRef(data), ECSDI.Fecha_de_entrega, Literal(dateToMillis(deliverDate))))
    for a in productList:
        gm.add((URIRef(data), ECSDI.Envia, URIRef(URI + a)))

    gm.serialize(destination='../data/data', format='turtle')

    # TODO Write Existences
    # def writeExistences(exists, qtt):
    #   URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    #   data = Namespace(URI)

    #   gm = Graph()
    #   gm.add()


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # ---------------------------------------------- TEST --------------------------------------------------
    productsList = ['Producto_1', 'Producto_2', 'Producto_3']
    t = datetime.datetime(2009, 10, 21, 0, 0)
    writeSends(productsList, t)

    # ------------------------------------------------------------------------------------------------------

    # Run behaviors
    # ab1 = Process(target=agentBehaviour, args=(queue,))
    # ab1.start()

    # Run server
    # app.run(host=hostname, port=port)

    # Wait behaviors
    # ab1.join()

    print('The End')
