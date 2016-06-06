# -*- coding: utf-8 -*-
import random

import sys
from flask import Flask, request
from multiprocessing import Process, Queue
import socket

from rdflib import Namespace, Graph, logger, RDF, XSD, Literal, URIRef
from utils.ACLMessages import get_message_properties, build_message, register_agent, get_agent_info, send_message
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.Logging import config_logger
from utils.OntologyNamespaces import ACL, ECSDI

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9010

logger = config_logger(level=1)

# Agent Namespace
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Data Agent
ProductsAgent = Agent('ProductsAgent',
                      agn.ProductsAgent,
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

def get_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt


def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio

    :param gmess:
    :return:
    """

    logger.info('Nos registramos')

    gr = register_agent(ProductsAgent, DirectoryAgent, ProductsAgent.uri, get_count())
    return gr


@app.route("/comm")
def communication():
    global dsgraph
    gr = None

    logger.info('Peticion de informacion recibida')

    # Extraemos el mensaje y creamos un grafo con el
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL
    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=ProductsAgent.uri, msgcnt=get_count())
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=ProductsAgent.uri, msgcnt=get_count())
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            content = msgdic['content']
            accion = gm.value(subject=content, predicate=RDF.type)

            # Aqui realizariamos lo que pide la accion

            if accion == ECSDI.Registra_productes:
                gr = recordExternalProduct(gm)

            elif accion == ECSDI.Enviar_venta:
                logger.info("Recibe comunicación del FinancialAgent")

                products = obtainProducts(gm)
                requestAvailability(products)

                products = obtainProducts(gm)
                gr = sendProducts(products)

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

def obtainProducts(gm):
    logger.info("Obtenemos los productos")

    products = Graph()

    sell = None
    for item in gm.subjects(RDF.type, ECSDI.Compra):
        sell = item

    sellsGraph = Graph()
    sellsGraph.parse(open('../data/compres'), format='turtle')

    for item in sellsGraph.objects(sell, ECSDI.Productos):
        marca = sellsGraph.value(subject=item, predicate=ECSDI.Marca)
        nombre = sellsGraph.value(subject=item, predicate=ECSDI.Nombre)
        modelo = sellsGraph.value(subject=item, predicate=ECSDI.Modelo)
        precio = sellsGraph.value(subject=item, predicate=ECSDI.Precio)
        peso = sellsGraph.value(subject=item, predicate=ECSDI.Peso)
        products.add((item, RDF.type, ECSDI.Producto))
        products.add((item, ECSDI.Marca, Literal(marca, datatype=XSD.string)))
        products.add((item, ECSDI.Nombre, Literal(nombre, datatype=XSD.string)))
        products.add((item, ECSDI.Modelo, Literal(modelo, datatype=XSD.string)))
        products.add((item, ECSDI.Precio, Literal(precio, datatype=XSD.float)))
        products.add((item, ECSDI.Peso, Literal(peso, datatype=XSD.float)))

    return products


def requestAvailability(graph):
    logger.info('Comprobamos disponibilidad')
    content = ECSDI['Pedir_disponibilidad' + str(get_count())]

    graph.add((content, RDF.type, ECSDI.Pedir_disponibilidad))

    subjectExiste = ECSDI['Existencia_' + str(get_count())]
    graph.add((subjectExiste, RDF.type, ECSDI.Existencia))
    graph.add((subjectExiste, ECSDI.Cantidad, Literal(1, datatype=XSD.integer)))

    for item in graph.subjects(RDF.type, ECSDI.Producto):
        graph.add((subjectExiste, ECSDI.Tiene, URIRef(item)))

    graph.add((content, ECSDI.Existe, URIRef(subjectExiste)))

    logistic = get_agent_info(agn.LogisticHubAgent, DirectoryAgent, ProductsAgent, get_count())

    send_message(
        build_message(graph, perf=ACL.request, sender=ProductsAgent.uri, receiver=logistic.uri,
                      msgcnt=get_count(),
                      content=content), logistic.address)


def sendProducts(gr):
    logger.info('Enviamos los productos')

    content = ECSDI['Enviar_lot' + str(get_count())]
    gr.add((content, RDF.type, ECSDI.Enviar_lot))

    subjectLoteProducto = ECSDI['Lote_producto' + str(random.randint(1, sys.float_info.max))]
    gr.add((subjectLoteProducto, RDF.type, ECSDI.Lote_producto))
    gr.add((subjectLoteProducto, ECSDI.Prioridad, Literal(1, datatype=XSD.integer)))

    for item in gr.subjects(RDF.type, ECSDI.Producto):
        gr.add((subjectLoteProducto, ECSDI.productos, URIRef(item)))

    gr.add((content, ECSDI.a_enviar, URIRef(subjectLoteProducto)))

    logistic = get_agent_info(agn.LogisticHubAgent, DirectoryAgent, ProductsAgent, get_count())

    gr = send_message(
        build_message(gr, perf=ACL.request, sender=ProductsAgent.uri, receiver=logistic.uri,
                      msgcnt=get_count(),
                      content=content), logistic.address)

    return gr


def recordExternalProduct(gm):
    ontologyFile = open('../data/productes')

    g = Graph()
    g.parse(ontologyFile, format='turtle')

    # Aquí afegim el producte al graf
    producte = gm.subjects(RDF.type, ECSDI.Producto_externo)
    producte = producte.next()

    for s, p, o in gm:
        if s == producte:
            g.add((s, p, o))

    # Guardem el graf
    g.serialize(destination='../data/productes', format='turtle')
    return gm


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port, debug=True)

    # Wait behaviors
    ab1.join()
    print('The End')
