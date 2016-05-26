# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask
/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente
Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import argparse
import socket
import sys
from multiprocessing import Queue, Process

from flask import Flask, request
from prettytable import PrettyTable

from agents.FinancialAgent import FinancialAgent
from agents.ProductsAgent import mss_cnt
from utils.ACLMessages import *
from utils.Agent import Agent
from utils.FlaskServer import shutdown_server
# Author
from utils.Logging import config_logger
from utils.OntologyNamespaces import ECSDI

__author__ = 'amazadonde'

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor est abierto al exterior o no", action='store_true',
                    default=False)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', default=socket.gethostname(), help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

# Logging
logger = config_logger(level=1)

# parsing de los parametros de la linea de comandos
args = parser.parse_args()

# Configuration stuff
if args.port is None:
    port = 9002
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()
    print(hostname)

if args.dport is None:
    dport = 9000
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
    print(dhostname)
else:
    dhostname = args.dhost

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Agent Namespace
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Data Agent
# Datos del Agente
SellerAgent = Agent('SellerAgent',
                    agn.SellerAgent,
                    'http://%s:%d/comm' % (hostname, port),
                    'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:%d/Register' % (dhostname, dport),
                       'http://%s:%d/Stop' % (dhostname, dport))

# Global triplestore graph
dsGraph = Graph()

# Queue
queue = Queue()

# Flask app
app = Flask(__name__)


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

    global mss_cnt

    gr = register_agent(SellerAgent, DirectoryAgent, SellerAgent.uri, messageCount)
    messageCount += 1

    return gr


@app.route("/comm")
def communication():
    """
    Communication Entrypoint
    """

    logger.info('Peticion de informacion recibida')
    global dsGraph
    global mss_cnt

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=SellerAgent.uri, msgcnt=messageCount)
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

            # Accion de busqueda
            if accion == ECSDI.Cerca_productes:
                restriccions = gm.objects(content, ECSDI.Restringe)
                restriccions_dict = {}
                for restriccio in restriccions:
                    if gm.value(subject=restriccio, predicate=RDF.type) == ECSDI.Restriccion_Marca:
                        marca = gm.value(subject=restriccio, predicate=ECSDI.Marca)
                        logger.info('MARCA: ' + marca)
                        restriccions_dict['brand'] = marca
                    elif gm.value(subject=restriccio, predicate=RDF.type) == ECSDI.Restriccion_modelo:
                        modelo = gm.value(subject=restriccio, predicate=ECSDI.Modelo)
                        logger.info('MODELO: ' + modelo)
                        restriccions_dict['model'] = modelo
                    elif gm.value(subject=restriccio, predicate=RDF.type) == ECSDI.Rango_Precio:
                        preu_max = gm.value(subject=restriccio, predicate=ECSDI.Precio_max)
                        preu_min = gm.value(subject=restriccio, predicate=ECSDI.Precio_min)
                        logger.info('PRECIO: ' + preu_max + ' - ' + preu_min)
                        restriccions_dict['max_price'] = preu_max
                        restriccions_dict['min_price'] = preu_min

                gr = findProducts(**restriccions_dict)

            # Accion de comprar
            elif accion == ECSDI.Peticion_compra:
                list = gm.value(subject=content, predicate=ECSDI.Lote_producto)

                gr = sell_products()
            # No habia ninguna accion en el mensaje
            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=mss_cnt)
    messageCount += 1

    logger.info('Respondemos a la peticion')

    serialize = gr.serialize(format='xml')
    return serialize, 200


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
    queue.put(0)

    pass


def agent_behaviour(queue):
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()


# DETERMINATE AGENT FUNCTIONS ------------------------------------------------------------------------------

ontologyFile = open('../data/productes')


def printProducts(queryResult):
    data = PrettyTable(['Nombre', 'Modelo', 'Marca', 'Precio'])
    for res in queryResult:
        data.add_row([res['nombre'],
                      res['modelo'],
                      res['marca'],
                      res['precio']])
    print(data)


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

    graph_query = graph.query(query)
    result = Graph()
    result.bind('ECSDI', ECSDI)
    product_count = 0
    for row in graph_query:
        nom = row.nombre
        model=row.modelo
        marca=row.marca
        preu=row.precio
        logger.debug(nom, marca, model, preu)
        subject = ECSDI['ProducteResultatCerca' + str(product_count)]
        product_count += 1
        result.add((subject, RDF.type, ECSDI.Producte))
        result.add((subject, ECSDI.Marca, Literal(marca)))
        result.add((subject, ECSDI.Modelo, Literal(model)))
        result.add((subject, ECSDI.Precio, Literal(preu)))
        result.add((subject, ECSDI.Nombre, Literal(nom)))
    return result


def sell_products(urlProductsList):
    global mss_cnt
    productList = []
    baseURL = 'http://www.owl-ontologies.com/ECSDIAmazon.owl#'
    for f in urlProductsList:
        productList.append(baseURL + f)

    rsp_obj = agn['Productos']

    # TODO Insert into message the product list
    message = build_message(gmess=Graph(),
                            perf=ACL.request,
                            sender=SellerAgent.uri,
                            receiver=FinancialAgent.uri,
                            content=rsp_obj,
                            msgcnt=messageCount)
    print(get_message_properties(message))
    gr = send_message(message, FinancialAgent.address)
    messageCount += 1
    return gr


# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # --------------------------------------- TEST ---------------------------------------------------------
    # printProducts(findProducts())
    sell_products(['Producto_1', 'Producto_2'])

    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
