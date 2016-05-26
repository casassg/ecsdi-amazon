# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


"""
from utils.OntologyNamespaces import ECSDI

__author__ = ''

import time
import argparse
import socket
from multiprocessing import Process

from flask import Flask, render_template, request
from rdflib import Graph, Namespace, URIRef, RDF, Literal

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
    port = 9005
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
ExternalSellerPersonalAgent = Agent('ExternalSellerPersonalAgent',
                                    agn.ExternalSellerPersonalAgent,
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


def writeGraph(marca,nom,model,preu):
    URI = "http://www.owl-ontologies.com/ECSDIAmazon.owl#"
    n = int(round(time.time() * 1000))
    data = URI + "Producto_" + str(n)

    gm = Graph()
    gm.add((URIRef(data), RDF.type, ECSDI.Producto))
    gm.add((URIRef(data), ECSDI.Nombre, Literal(nom)))
    gm.add((URIRef(data), ECSDI.Marca, Literal(marca)))
    gm.add((URIRef(data), ECSDI.Modelo, Literal(model)))
    gm.add((URIRef(data), ECSDI.Precio, Literal(preu)))
    
    return gm


@app.route("/registrarProducto", methods=['GET', 'POST'])
def browser_registrarProducto():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """
    global mss_cnt
    if request.method == 'GET':
        return render_template('registerProduct.html')
    else:
        marca = request.form['marca']
        nom = request.form['nom']
        model = request.form['model']
        preu = request.form['preu']
        
         # Content of the message
        content = ECSDI['Registra_productes_' + str(get_count())]

        gr = writeGraph(marca,nom,model,preu)
        
        productsAg = get_agent_info(agn.AgenteProductos, DirectoryAgent,ExternalSellerPersonalAgent, get_count())
        
        gr = send_message(
            build_message(gr, perf=ACL.request, sender=ExternalSellerPersonalAgent, receiver=productsAg, msgcnt=get_count(),
                          content=content), productsAg.address)
        
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
