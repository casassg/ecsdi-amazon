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
from utils.ACLMessages import get_message_properties, build_message, send_message, get_agent_info, register_agent
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
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Lista de productos a enviar
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

    gr = register_agent(FinancialAgent, DirectoryAgent, FinancialAgent.uri, get_count())
    return gr


@app.route("/comm")
def communication():
    """
    Communication Entrypoint
    """

    global dsGraph
    logger.info('Peticion de informacion recibida')

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    gr = None

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=FinancialAgent.uri, msgcnt=get_count())
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

            # Accion de enviar venta
            if accion == ECSDI.Peticion_compra:
                # TODO Estudiar como tratar el listado de productos de la Peticion de compra (Mirar el predicate)
                list = gm.value(subject=content, predicate=ECSDI.Lista_productos_seleccionados)

                global lista_productos
                for item in list:
                    lista_productos.append(gm.value(subject=content, predicate=ECSDI.Producto))

                registerSells()
                payDelivery()

            elif accion == ECSDI.Peticion_retorno:
                # TODO retorn compra (Aun no hace falta hacerlo. Se hara una vez acabado la compra de productos)
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())

            elif accion == ECSDI.Transferencia_comfirmada:
                # TODO accion recibida del BankAgent que su funcionalidad es enviar el mensaje a Product agent para que envie los productos
                confirmTransfer()

            # Ninguna accion a realizar
            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())

    logger.info('Respondemos a la peticion')

    return gr.serialize(format='xml')


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

def payDelivery():
    content = ECSDI['Peticion_transferencia_' + str(get_count())]

    graph = Graph()
    subject = ECSDI.Peticion
    graph.add((subject, RDF.type, ECSDI.Peticion_transferencia))

    bank = get_agent_info(agn.BankAgent, DirectoryAgent, FinancialAgent, get_count())

    message = build_message(gmess=graph,
                            perf=ACL.request,
                            sender=FinancialAgent,
                            receiver=bank,
                            content=content,
                            msgcnt=get_count())

    gr = send_message(message, bank.address)
    return gr


def registerSells():
    # TODO Record the purchase.
    global lista_productos
    writeSells(1, 15.30, lista_productos, 'Ciudad_1')


def readSell(id):

    URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    URISell = URI
    ontologyFile = open('../data/productes')

    return 0


def confirmTransfer():
    # TODO Confirm the transfer, deliver receipt and communicate with Products Agent.
    # Necessito id de la compra
    content = readSell(id)

    graph = Graph()
    subject = ECSDI.Envio

    graph.add((subject, RDF.type, ECSDI.Envio))

    productManeger = get_agent_info(agn.ProductsAgent, DirectoryAgent, FinancialAgent, get_count())

    message = build_message(gmess=graph,
                            perf=ACL.request,
                            sender=FinancialAgent,
                            receiver=productManeger,
                            content=content,
                            msgcnt=get_count())

    gr = send_message(message, productManeger.address)
    return gr

    print('todo')


def writeSells(paid, totalPrice, productsList, sendTo):
    # TODO Cambiar el data a almacenar. Tiene que ser data/compras
    URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    millis = int(round(time.time() * 1000))
    URISell = URI + "Compra_" + str(millis)

    ontologyFile = open('../data/productes')

    g = Graph()
    g.parse(ontologyFile, format='turtle')
    g.add((URIRef(URISell), RDF.type, ECSDI.Compra))
    g.add((URIRef(URISell), ECSDI.Pagat, Literal(paid)))
    g.add((URIRef(URISell), ECSDI.Precio_total, Literal(totalPrice)))
    g.add((URIRef(URISell), ECSDI.Enviar_a, URIRef(URI + sendTo)))
    for p in productsList:
        g.add((URIRef(URISell), ECSDI.Productos, URIRef(URI + p)))

    g.serialize(destination='../productes/productes', format='turtle')


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
