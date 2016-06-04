# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import random
import time
import datetime

import sys
from flask import Flask, request
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph, URIRef, RDF, Literal, logger, XSD
from utils.ACLMessages import get_message_properties, build_message, register_agent
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.Logging import config_logger
from utils.OntologyNamespaces import ECSDI, ACL

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9035

logger = config_logger(level=1)

# Agent Namespace
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Data Agent
LogisticHubAgent = Agent('LogisticHubAgent',
                         agn.LogisticHubAgent,
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


def get_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt


# AGENT FUNCTIONS ------------------------------------------------------------------------------------------

def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio

    :param gmess:
    :return:
    """

    logger.info('Nos registramos')

    gr = register_agent(LogisticHubAgent, DirectoryAgent, LogisticHubAgent.uri, get_count())
    return gr


@app.route("/comm")
def communication():
    """
    Communication Entrypoint
    """

    logger.info('Peticion de informacion recibida')
    global dsGraph

    gr = None

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=LogisticHubAgent.uri, msgcnt=get_count())
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia
            # de registro
            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)

            # Accion de disponibilidad
            if accion == ECSDI.Pedir_disponibilidad:
                gm.remove((content, None, None))
                for item in gm.subjects(RDF.type, ACL.FipaAclMessage):
                    gm.remove((item, None, None))
                gr = gm
                logger.info('Productos disponibles')

            elif accion == ECSDI.Enviar_lot:
                logger.info('Se envia el lote de productos')
                gm.remove((content, None, None))
                for item in gm.subjects(RDF.type, ACL.FipaAclMessage):
                    gm.remove((item, None, None))
                for item in gm.subjects(RDF.type, ECSDI.Existencia):
                    gm.remove((item, None, None))
                for item in gm.subjects(RDF.type, ECSDI.Pedir_disponibilidad):
                    gm.remove((item, None, None))

                tomorrow = dateToMillis(datetime.date.today() + datetime.timedelta(days=1))
                gr = writeSends(gm, tomorrow)

            # No habia ninguna accion en el mensaje
            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())

    logger.info('Respondemos a la peticion')

    return gr.serialize(format='xml'), 200


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


def agent_behaviour(queue):
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()


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


def writeSends(gr, deliverDate):
    subjectEnvio = ECSDI['Envio_' + str(random.randint(1, sys.float_info.max))]

    print(gr.serialize(format='turtle'))

    gr.add((subjectEnvio, RDF.type, ECSDI.Envio))
    gr.add((subjectEnvio, ECSDI.Fecha_de_entrega, Literal(deliverDate, datatype=XSD.float)))
    for item in gr.subjects(RDF.type, ECSDI.Lote_Producto):
        gr.add((subjectEnvio, ECSDI.Envia, URIRef(item)))

    print(gr.serialize(format='turtle'))

    g = Graph()
    gr += g.parse(open('../data/enviaments'), format='turtle')

    gr.serialize(destination='../data/enviaments', format='turtle')

    return gr


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
