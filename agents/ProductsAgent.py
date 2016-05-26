# -*- coding: utf-8 -*-
from flask import Flask, request
from multiprocessing import Process, Queue
import socket
from rdflib import Namespace, Graph, logger, RDF
from utils.ACLMessages import get_message_properties, build_message
from utils.FlaskServer import shutdown_server
from utils.Agent import Agent
from utils.OntologyNamespaces import ACL

# Author
__author__ = 'amazadonde'

# AGENT ATTRIBUTES ----------------------------------------------------------------------------------------

# Configuration stuff
hostname = socket.gethostname()
port = 9010

# Agent Namespace
agn = Namespace("http://www.agentes.org#")

# Message Count
mss_cnt = 0

# Data Agent
ProductsAgent = Agent('AgenteProductos',
                      agn.AgenteProductos,
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

# Contador de mensajes
mss_cnt = 0


# AGENT FUNCTIONS ------------------------------------------------------------------------------------------

@app.route("/comm")
def communication():

    """
    Communication Entrypoint
    global dsGraph
    global messageCount
    pass
    """

    """
    Entrypoint de comunicacion del agente
    Simplemente retorna un objeto fijo que representa una
    respuesta a una busqueda de producto
    """

    global dsgraph
    global mss_cnt

    logger.info('Peticion de informacion recibida')

    # Extraemos el mensaje y creamos un grafo con el
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL
    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=PersonalAgent.uri, msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=PersonalAgent.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)

            # Aqui realizariamos lo que pide la accion
            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(Graph(),
                ACL['inform-done'],
                sender=PersonalAgent.uri,
                msgcnt=mss_cnt,
                receiver=msgdic['sender'], )
    mss_cnt += 1

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


def agentBehaviour(queue):

    """
    Agent Behaviour in a concurrent thread.

    :param queue: the queue
    :return: something
    """

    # TODO Behaviour

    pass


# DETERMINATE AGENT FUNCTIONS ------------------------------------------------------------------------------

def distributeDelivery():

    # TODO Get products availability and send them.
    print("Distribute Delivery")


def recordExternalProduct():

    # TODO Record product of an external seller.
    print("RecordExternalProduct")
    
    ontologyFile = open('../data/data')
    
    g = Graph()
    g.parse(ontologyFile, format='turtle')
    #Aquí afegim el producte al graf
    
    
    #guardem el graf
    g.serialize(destination='../data/data', format='turtle')



# MAIN METHOD ----------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # Run behaviors
    ab1 = Process(target=agentBehaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port)

    # Wait behaviors
    ab1.join()
    print('The End')
