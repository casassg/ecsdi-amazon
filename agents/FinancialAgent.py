# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import time
from flask import Flask, request
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph, URIRef, RDF, Literal, logger

from agents.ProductsAgent import mss_cnt
from utils.ACLMessages import get_message_properties, build_message
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.OntologyNamespaces import ECSDI, ACL

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9015

# Agent Namespace
agn = Namespace("http://www.agentes.org#")  # Revisar url -> definir nuevo espacio de nombre incluyendo agentes nuestros

# Message Count
messageCount = 0

lista_productos = []

# Data Agent
FinancialAgent = Agent('AgenteFinanzas',
                       agn.AgenteFinanzas,
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
    logger.info('Peticion de informacion recibida')

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=FinancialAgent.uri, msgcnt=messageCount)
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia
            # de registro
            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)

            # Accion de enviar venta
            if accion == ECSDI.Peticion_compra:
                list = gm.value(subject=content, predicate=ECSDI.Lista_productos_seleccionados)
                global lista_productos
                for item in list:
                    lista_productos.append(gm.value(subject=content,predicate=ECSDI.Producto))

                payDelivery()

            elif accion == ECSDI.Peticion_retorno:
                #TODO retorn compra
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=mss_cnt)

            elif accion == ECSDI.Transferencia_comfirmada:

                confirmTransfer()

                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=mss_cnt)

            # Ninguna accion a realizar
            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=mss_cnt)
    messageCount += 1

    logger.info('Respondemos a la peticion')

    return gr.serialize(format='xml')


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

    # TODO Behaviour

    pass


# DETERMINATE AGENT FUNCTIONS ------------------------------------------------------------------------------

def payDelivery():
    # TODO Record the purchase.
    productList = ['Producto_2', 'Producto_3']
    writeSells(1, 15.30, productList, 'Ciudad_1')

    rsp_obj = agn['Productos']

    message = build_message(gmess=Graph(),
                            perf=ACL.request,
                            sender=FinancialAgent.uri,
                            receiver=BankAgent.uri,
                            content=rsp_obj,
                            msgcnt=messageCount)

    gr = send_message(message, BankAgent.address)
    messageCount += 1
    return gr


    print("PayDelivery")


def confirmTransfer():
    # TODO Confirm the transfer, deliver receipt and communicate with Products Agent.



    print("ConfirmTransfer")



def writeSells(paid, totalPrice, productsList, sendTo):
    URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    millis = int(round(time.time() * 1000))
    URISell = URI + "Compra_" + str(millis)

    ontologyFile = open('../data/data')

    g = Graph()
    g.parse(ontologyFile, format='turtle')
    g.add((URIRef(URISell), RDF.type, ECSDI.Compra))
    g.add((URIRef(URISell), ECSDI.Pagat, Literal(paid)))
    g.add((URIRef(URISell), ECSDI.Precio_total, Literal(totalPrice)))
    g.add((URIRef(URISell), ECSDI.Enviar_a, URIRef(URI + sendTo)))
    for p in productsList:
        g.add((URIRef(URISell), ECSDI.Productos, URIRef(URI + p)))

    g.serialize(destination='../data/data', format='turtle')


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # ---------------------------------------------- TEST --------------------------------------------------
    confirmTransfer()

    # ------------------------------------------------------------------------------------------------------

    # Run behaviors
    ab1 = Process(target=agentBehaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
