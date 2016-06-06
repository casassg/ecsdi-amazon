# -*- coding: utf-8 -*-

"""
Agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente
Asume que el agente de registro esta en el puerto 9000
"""
import socket
from multiprocessing import Process, Queue

import datetime
from flask import Flask, request
from rdflib import Namespace, Graph, RDF, Literal

from utils.ACLMessages import register_agent, get_message_properties, build_message, get_bag_agent_info, send_message
from utils.Agent import Agent
from utils.FlaskServer import shutdown_server
from utils.Logging import config_logger
from utils.OntologyNamespaces import ACL, ECSDI

__author__ = 'amazadonde'

logger = config_logger(level=1)

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9030

# Agent Namespace
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Data Agent
TransportDealerAgent = Agent('TransportDealerAgent',
                             agn.TransportDealerAgent,
                             'http://%s:%d/comm' % (hostname, port),
                             'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)
ExternalTransportDirectory = Agent('ExternalTransportDirectory',
                                   agn.Directory,
                                   'http://%s:8000/Register' % hostname,
                                   'http://%s:8000/Stop' % hostname)

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


def dateToMillis(date):
    return (date - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000.0


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

    gr = register_agent(TransportDealerAgent, DirectoryAgent, TransportDealerAgent.uri, get_count())
    return gr


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
        gr = build_message(Graph(), ACL['not-understood'], sender=TransportDealerAgent.uri, msgcnt=get_count())
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

            # Accion de busqueda
            if accion == ECSDI.Peticiona_transport:
                responPeticio(gm, content)
                gr = Graph()

            # No habia ninguna accion en el mensaje
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


def requestOffer(agent, peso, fecha, destino):
    gr = Graph()
    subject = ECSDI['peticion-oferta']
    gr.add((subject, RDF.type, ECSDI.Pedir_oferta_transporte))
    gr.add((subject, ECSDI.Destino, Literal(destino)))
    gr.add((subject, ECSDI.Plazo_maximo_entrega, Literal(fecha)))
    gr.add((subject, ECSDI.Peso_envio, Literal(peso)))
    resp = send_message(build_message(gr, ACL['call-for-proposal'], content=subject, receiver=agent.uri,
                                      sender=TransportDealerAgent.uri), agent.address)
    msg = get_message_properties(resp)
    if 'performative' not in msg or msg['performative'] == ACL.refuse:
        logger.warn('An agent rejected us :(')
        return None
    elif msg['performative'] == ACL.propose:
        precio = resp.value(msg['content'], ECSDI.Precio_envio)
        return Offer(address=agent.address, price=precio.toPython())
    logger.error('I can\'t understand:(')
    return None


def acceptOffer(offer):
    resp = send_message(build_message(Graph(), ACL['accept-proposal'], sender=TransportDealerAgent.uri),
                        offer.address)
    msg = get_message_properties(resp)
    return msg['performative'] == ACL.inform


def counter_offer(offer):
    logger.info('Asking counter-offer to ' + offer.address)
    gr = Graph()
    subject = ECSDI['contra-oferta']
    gr.add((subject, RDF.type, ECSDI.Contraoferta))
    new_price = offer.price - 2
    gr.add((subject, ECSDI.Precio_envio, Literal(new_price)))
    resp = send_message(build_message(gr, ACL['counter-proposal'], content=subject, sender=TransportDealerAgent.uri),
                        offer.address)
    msg = get_message_properties(resp)
    if 'performative' not in msg or msg['performative'] == ACL.refuse:
        logger.warn('An agent rejected us :(')
        return None
    elif msg['performative'] == ACL.agree:
        return Offer(address=offer.address, price=new_price)
    else:
        logger.error('I can\'t understand:(')
        return None


def rejectOffer(offer):
    resp = send_message(build_message(Graph(), ACL['reject-proposal'], sender=TransportDealerAgent.uri),
                        offer.address)
    msg = get_message_properties(resp)


def requestTransports(peso, fecha, destino):
    agents = get_bag_agent_info(agn.ExternalTransportAgent, ExternalTransportDirectory, TransportDealerAgent, 192310291)
    offers = []
    for agent in agents:
        offer = requestOffer(agent, peso, fecha, destino)
        logger.info('Offer received of ' + str(offer.price))
        if offer:
            offers += [offer]
    offers2 = []
    for i, offer in enumerate(offers):
        offer2 = counter_offer(offer)
        if offer2:
            logger.info('Counter offer accepted at ' + str(offer2.price))
            offers2 += [offer2]
        else:
            logger.info('Counter offer rejected by ' + str(offer.address))
            offers2 += [offer]
    best_offer = min(offers2, key=lambda a: a.price)
    logger.info('Best offer is at ' + str(best_offer.price) + '€')
    end = False
    for offer in offers2:
        if offer == best_offer:
            end = acceptOffer(best_offer)
        else:
            rejectOffer(offer)
    if end:
        logger.info('YAY! The conversation is succesfull!')
        return best_offer
    else:
        return None


class Offer(object):
    def __init__(self, price, address):
        self.price = price
        self.address = address


def responPeticio(gm, content):
    peso = gm.value(subject=content, predicate=ECSDI.Peso_envio)
    fecha = gm.value(subject=content, predicate=ECSDI.Fecha)

    offer = requestTransports(peso, datetime.datetime.fromtimestamp(float(fecha) / 1000.0), 'Barcelona')


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
