# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: casassg
"""
from utils.ACLMessages import get_agent_info, send_message, build_message
from utils.OntologyNamespaces import ECSDI, ACL

__author__ = 'casassg'

import argparse
import socket
from multiprocessing import Process

from flask import Flask, render_template, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal

from utils.Agent import Agent
from utils.FlaskServer import shutdown_server
from utils.Logging import config_logger

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
    mss_cnt += 1
    return mss_cnt


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
        subject = ECSDI['Cerca_productes_' + str(get_count())]

        gr = Graph()
        gr.add((subject, RDF.type, ECSDI.Cerca_productes))

        nom = request.form['nom']
        if nom:
            subject_nom = ECSDI['RestriccioNom' + str(get_count())]
            gr.add((subject_nom, RDF.type, ECSDI.RestriccioNom))
            gr.add((subject_nom, ECSDI.Nom, Literal(nom)))
            gr.add((subject, ECSDI.Restringe, URIRef(subject_nom)))
        marca = request.form['marca']
        if marca:
            subject_marca = ECSDI['Restriccion_Marca_' + str(get_count())]
            gr.add((subject_marca, RDF.type, ECSDI.Restriccion_Marca))
            gr.add((subject_marca, ECSDI.Marca, Literal(marca)))
            gr.add((subject, ECSDI.Restringe, URIRef(subject_marca)))
        min_price = request.form['min_price']
        max_price = request.form['max_price']

        if min_price or max_price:
            subject_preus = ECSDI['Restriccion_Preus_' + str(get_count())]
            gr.add((subject_preus, RDF.type, ECSDI.Rango_precio))
            if min_price:
                gr.add((subject_preus, ECSDI.Precio_min, Literal(min_price)))
            if max_price:
                gr.add((subject_preus, ECSDI.Precio_max, Literal(max_price)))
            gr.add((subject, ECSDI.Restringe, URIRef(subject_preus)))

        seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

        gr = send_message(
            build_message(gr, perf=ACL.request, sender=UserPersonalAgent, receiver=seller, msgcnt=get_count(),
                          content=subject), seller.address)

        return gr.serialize()


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
