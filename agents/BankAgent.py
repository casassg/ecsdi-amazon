# -*- coding: utf-8 -*-
"""
filename: BankAgent

Agent que implementa la interacció amb el banc
per tal de gestionar la transferència de diners

@author: AlbertSuarez
"""

from utils.ACLMessages import get_agent_info, send_message, build_message, get_message_properties, register_agent
from utils.OntologyNamespaces import ECSDI, ACL
import argparse
import socket
from multiprocessing import Process, Queue
from flask import Flask, request
from rdflib import Graph, Namespace, RDF
from utils.Agent import Agent
from utils.FlaskServer import shutdown_server
from utils.Logging import config_logger

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
    port = 9040
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
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
BankAgent = Agent('BankAgent',
                  agn.BankAgent,
                  'http://%s:%d/comm' % (hostname, port),
                  'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:%d/Register' % (dhostname, dport),
                       'http://%s:%d/Stop' % (dhostname, dport))

# Global dsgraph triplestore
dsgraph = Graph()

# Queue
queue = Queue()


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

    gr = register_agent(BankAgent, DirectoryAgent, BankAgent.uri, get_count())
    return gr


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
def communication():
    """
    Communication Entrypoint
    """

    logger.info('Peticion de informacion recibida')
    global dsGraph

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=BankAgent.uri, msgcnt=get_count())
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())
        else:
            # Obtenemos la performativa
            perf = msgdic['performative']

            if perf != ACL.request:
                # Si no es un request, respondemos que no hemos entendido el mensaje
                gr = build_message(Graph(), ACL['not-understood'], sender=BankAgent.uri, msgcnt=get_count())
            else:
                # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
                # de registro
                content = msgdic['content']
                # Averiguamos el tipo de la accion
                accion = gm.value(subject=content, predicate=RDF.type)

                # Accion de transferencia
                if accion == ECSDI.Peticion_transferencia:
                    # Content of the message
                    for item in gm.subjects(RDF.type, ACL.FipaAclMessage):
                        gm.remove((item, None, None))
                    gr = gm
                    logger.info('Se acepta la transferencia')

                # No habia ninguna accion en el mensaje
                else:
                    gr = build_message(Graph(),
                                       ACL['not-understood'],
                                       sender=DirectoryAgent.uri,
                                       msgcnt=get_count())

    logger.info('Respondemos a la peticion')

    return gr.serialize(format='xml'), 200


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agent_behaviour(queue):
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()


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