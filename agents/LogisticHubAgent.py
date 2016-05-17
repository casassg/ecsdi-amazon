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

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9035

# Agent Namespace
agn = Namespace("http://www.agentes.org#") #Revisar url -> definir nuevo espacio de nombre incluyendo agentes nuestros

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

def sendProducts():

    # TODO Receive communication of send something and send it.
    print("Send Products")


def recordDeliveries():

    # TODO Record Receive communication of availability discussion and record deliveries.
    print("Record Deliveries")


def requestTransport():

    # TODO Discuss with Transport Dealer.
    print("Request Transport")


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # Run behaviors
    ab1 = Process(target=agentBehaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
