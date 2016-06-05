# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent
Agent que implementa la interacció amb l'usuari
"""
import argparse
import socket
from multiprocessing import Process

import datetime
from flask import Flask, request
from rdflib import Graph, Namespace, RDF

from utils.ACLMessages import register_agent, get_message_properties, build_message
from utils.Agent import Agent
from utils.ExternalTransportAgent import ExternalTransportAgent
from utils.FlaskServer import shutdown_server
from utils.Logging import config_logger
from utils.OntologyNamespaces import ACL, ECSDI

__author__ = 'amazdonde'

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
    port = 9005
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 8000
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
ExternalTransportAgent1 = ExternalTransportAgent('ExternalTransportAgent1',
                                                 agn.ExternalTransportAgent,
                                                 'http://%s:%d/comm' % (hostname, port),
                                                 'http://%s:%d/Stop' % (hostname, port), 5)

# Directory agent address
ExternalTransportDirectory = Agent('ExternalTransportDirectory',
                                   agn.ExternalTransportDirectory,
                                   'http://%s:%d/Register' % (dhostname, dport),
                                   'http://%s:%d/Stop' % (dhostname, dport))

# Global dsgraph triplestore
dsgraph = Graph()


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

    gr = register_agent(ExternalTransportAgent1, ExternalTransportDirectory, ExternalTransportAgent1.uri, get_count())
    return gr


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    shutdown_server()
    return "Parando Servidor"


def proposal(graph, content):
    peso = graph.value(subject=content, predicate=ECSDI.Peso_envio)
    data = graph.value(subject=content, predicate=ECSDI.Plazo_maximo_entrega)
    data = datetime.datetime.fromtimestamp(data / 1000.0)
    city = graph.value(subject=content, predicate=ECSDI.Destino)
    return ExternalTransportAgent1.proposal(data, peso, city)


def counterproposal(gm, content):
    precio = gm.value(subject=content, predicate=ECSDI.Precio_envio)
    return ExternalTransportAgent1.answer_couter_proposal(precio)


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion del agente
    """

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL
    if not msgdic:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=ExternalTransportAgent1.uri,
                           msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        if msgdic['performative'] == ACL['accept-proposal']:
            return build_message(Graph(), perf=ACL.inform, sender=ExternalTransportAgent1.uri).serialize()

        if msgdic['performative'] == ACL['reject-proposal']:
            ExternalTransportAgent1.reset()

        if msgdic['performative'] == ACL['counterproposal']:
            return counterproposal(gm, msgdic.content).serialize()

        if msgdic['performative'] == ACL['call-for-proposal']:
            return proposal(gm, msgdic.content).serialize()


        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia
            # de registro
            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)
    return


def agent_behaviour():
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()


if __name__ == '__main__':
    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=())
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
