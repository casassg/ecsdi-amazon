# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: casassg
"""
from utils.ACLMessages import get_agent_info, send_message, build_message
from utils.OntologyNamespaces import ECSDI, ACL
import argparse
import socket
from multiprocessing import Process
from flask import Flask, render_template, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal
from utils.Agent import Agent
from utils.FlaskServer import shutdown_server
from utils.Logging import config_logger

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
    port = 9081
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 9000
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
else:
    dhostname = args.dhost

# Flask stuff
app = Flask(__name__, template_folder='../templates')

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
UserPersonalAgent = Agent('UserPersonalAgent',
                          agn.UserPersonalAgent,
                          'http://%s:%d/comm' % (hostname, port),
                          'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:%d/Register' % (dhostname, dport),
                       'http://%s:%d/Stop' % (dhostname, dport))

# Global dsgraph triplestore
dsgraph = Graph()


def get_count():
    global mss_cnt
    if not mss_cnt:
        mss_cnt = 0
    mss_cnt += 1
    return mss_cnt


def send_peticio_compra():

    content = None

    def create_sell_product(gr, marca, modelo, nombre, precio):
        # Creacion del producto
        subject_producto = ECSDI['Producto_' + str(get_count())]
        gr.add((subject_producto, RDF.type, ECSDI.Producto))
        gr.add((subject_producto, ECSDI.Marca, Literal(marca)))
        gr.add((subject_producto, ECSDI.Modelo, Literal(modelo)))
        gr.add((subject_producto, ECSDI.Nombre, Literal(nombre)))
        gr.add((subject_producto, ECSDI.Precio, Literal(precio)))
        return subject_producto

    def create_peticio_compra():
        logger.info("Creando la peticion de compra")

        # Content of the message
        global content
        content = ECSDI['Peticion_compra_' + str(get_count())]

        # Graph creation
        gr = Graph()
        gr.add((content, RDF.type, ECSDI.Peticion_compra))

        # Asignar prioridad a la peticion (asignamos el contador de mensaje)
        gr.add((content, ECSDI.Prioridad, Literal(get_count())))

        # Creacion de la ciudad (por ahora Barcelona) ----------------------------------------------------------------------
        subject_ciudad = ECSDI['Ciudad_' + str(get_count())]

        latitud_Barcelona = 41.398373
        longitud_Barcelona = 2.188247
        nombre_Barcelona = 'Barcelona'

        gr.add((subject_ciudad, RDF.type, ECSDI.Ciudad))
        gr.add((subject_ciudad, ECSDI.Nombre, Literal(nombre_Barcelona)))
        gr.add((subject_ciudad, ECSDI.Latitud, Literal(latitud_Barcelona)))
        gr.add((subject_ciudad, ECSDI.Longitud, Literal(longitud_Barcelona)))

        # Creacion del sobre (Compra) --------------------------------------------------------------------------------------
        subject_sobre = ECSDI['Compra_' + str(get_count())]
        gr.add((subject_sobre, RDF.type, ECSDI.Compra))

        gr.add((subject_sobre, ECSDI.Pagat, Literal(0)))
        gr.add((subject_sobre, ECSDI.Enviar_a, URIRef(subject_ciudad)))

        # TODO Get attributes product list by interface
        products = [['Nintendo', 'Choripan 3DS', 'Nintendo Choripan', 100.0],
                    ['Garmin', '325', 'Garmin 325', 308.0],
                    ['Elephone', 'P700', 'Pioneer', 200.0],
                    ['Google', 'Nexus 5', 'Google Nexus 5', 350.0]]

        total_price = 0.0

        for item in products:
            total_price += item[3]
            subject_product = create_sell_product(gr, item[0], item[1], item[2], item[3])
            gr.add((subject_sobre, ECSDI.Productos, URIRef(subject_product)))

        gr.add((subject_sobre, ECSDI.Precio_total, Literal(total_price)))

        # ------------------------------------------------------------------------------------------------------------------

        gr.add((content, ECSDI.Sobre, URIRef(subject_sobre)))

        return gr

    message = create_peticio_compra()
    seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

    gr2 = send_message(
        build_message(message, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri, msgcnt=get_count(),
                      content=content), seller.address)

    return gr2.serialize()


@app.route("/cerca", methods=['GET', 'POST'])
def browser_cerca():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """
    global mss_cnt
    if request.method == 'GET':
        return render_template('cerca.html')
    else:
        logger.info("Enviando peticion de busqueda")

        # Content of the message
        content = ECSDI['Cerca_productes_' + str(get_count())]

        # Graph creation
        gr = Graph()
        gr.add((content, RDF.type, ECSDI.Cerca_productes))

        # Add restriccio nom
        nom = request.form['nom']
        if nom:
            # Subject nom
            subject_nom = ECSDI['RestriccioNom' + str(get_count())]
            gr.add((subject_nom, RDF.type, ECSDI.RestriccioNom))
            gr.add((subject_nom, ECSDI.Nom, Literal(nom)))
            # Add restriccio to content
            gr.add((content, ECSDI.Restringe, URIRef(subject_nom)))
        marca = request.form['marca']
        if marca:
            subject_marca = ECSDI['Restriccion_Marca_' + str(get_count())]
            gr.add((subject_marca, RDF.type, ECSDI.Restriccion_Marca))
            gr.add((subject_marca, ECSDI.Marca, Literal(marca)))
            gr.add((content, ECSDI.Restringe, URIRef(subject_marca)))
        min_price = request.form['min_price']
        max_price = request.form['max_price']

        if min_price or max_price:
            subject_preus = ECSDI['Restriccion_Preus_' + str(get_count())]
            gr.add((subject_preus, RDF.type, ECSDI.Rango_precio))
            if min_price:
                gr.add((subject_preus, ECSDI.Precio_min, Literal(float(min_price))))
            if max_price:
                gr.add((subject_preus, ECSDI.Precio_max, Literal(float(max_price))))
            gr.add((content, ECSDI.Restringe, URIRef(subject_preus)))

        seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

        gr2 = send_message(
            build_message(gr, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri, msgcnt=get_count(),
                          content=content), seller.address)

        return gr2.serialize()


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion del agente
    """
    return "Hola"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agentbehavior1():
    """
    Un comportamiento del agente

    :return:
    """


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1)
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    logger.info('The End')
