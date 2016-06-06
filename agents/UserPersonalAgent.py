# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: casassg
"""
import random

import sys
from utils.ACLMessages import get_agent_info, send_message, build_message, get_message_properties
from utils.OntologyNamespaces import ECSDI, ACL
import argparse
import socket
from multiprocessing import Process
from flask import Flask, render_template, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal, XSD
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

# Productos enconctrados
product_list = []

# Compras enconctrados
compres = []


def get_count():
    global mss_cnt
    if not mss_cnt:
        mss_cnt = 0
    mss_cnt += 1
    return mss_cnt


@app.route("/")
def browser_root():
    return render_template('rootUserPersonalAgent.html')


@app.route("/cerca", methods=['GET', 'POST'])
def browser_cerca():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """

    global product_list
    if request.method == 'GET':
        return render_template('cerca.html', products=None)
    elif request.method == 'POST':
        # Peticio de cerca
        if request.form['submit'] == 'Cerca':
            logger.info("Enviando peticion de busqueda")

            # Content of the message
            contentResult = ECSDI['Cerca_productes_' + str(get_count())]

            # Graph creation
            gr = Graph()
            gr.add((contentResult, RDF.type, ECSDI.Cerca_productes))

            # Add restriccio nom
            nom = request.form['nom']
            if nom:
                # Subject nom
                subject_nom = ECSDI['RestriccioNom' + str(get_count())]
                gr.add((subject_nom, RDF.type, ECSDI.RestriccioNom))
                gr.add((subject_nom, ECSDI.Nom, Literal(nom, datatype=XSD.string)))
                # Add restriccio to content
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_nom)))
            marca = request.form['marca']
            if marca:
                subject_marca = ECSDI['Restriccion_Marca_' + str(get_count())]
                gr.add((subject_marca, RDF.type, ECSDI.Restriccion_Marca))
                gr.add((subject_marca, ECSDI.Marca, Literal(marca, datatype=XSD.string)))
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_marca)))
            min_price = request.form['min_price']
            max_price = request.form['max_price']

            if min_price or max_price:
                subject_preus = ECSDI['Restriccion_Preus_' + str(get_count())]
                gr.add((subject_preus, RDF.type, ECSDI.Rango_precio))
                if min_price:
                    gr.add((subject_preus, ECSDI.Precio_min, Literal(min_price)))
                if max_price:
                    gr.add((subject_preus, ECSDI.Precio_max, Literal(max_price)))
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_preus)))

            seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

            gr2 = send_message(
                build_message(gr, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri,
                              msgcnt=get_count(),
                              content=contentResult), seller.address)

            index = 0
            subject_pos = {}
            product_list = []
            for s, p, o in gr2:
                if s not in subject_pos:
                    subject_pos[s] = index
                    product_list.append({})
                    index += 1
                if s in subject_pos:
                    subject_dict = product_list[subject_pos[s]]
                    if p == RDF.type:
                        subject_dict['url'] = s
                    elif p == ECSDI.Marca:
                        subject_dict['marca'] = o
                    elif p == ECSDI.Modelo:
                        subject_dict['modelo'] = o
                    elif p == ECSDI.Precio:
                        subject_dict['precio'] = o
                    elif p == ECSDI.Nombre:
                        subject_dict['nombre'] = o
                    elif p == ECSDI.Peso:
                        subject_dict['peso'] = o
                    product_list[subject_pos[s]] = subject_dict

            return render_template('cerca.html', products=product_list)

        # --------------------------------------------------------------------------------------------------------------

        # Peticio de compra
        elif request.form['submit'] == 'Comprar':
            products_checked = []
            for item in request.form.getlist("checkbox"):
                item_checked = []
                item_map = product_list[int(item)]
                item_checked.append(item_map['marca'])
                item_checked.append(item_map['modelo'])
                item_checked.append(item_map['nombre'])
                item_checked.append(item_map['precio'])
                item_checked.append(item_map['url'])
                item_checked.append(item_map['peso'])
                products_checked.append(item_checked)

            logger.info("Creando la peticion de compra")

            # Content of the message
            content = ECSDI['Peticion_compra_' + str(get_count())]

            # Graph creation
            gr = Graph()
            gr.add((content, RDF.type, ECSDI.Peticion_compra))

            # Asignar prioridad a la peticion (asignamos el contador de mensaje)
            gr.add((content, ECSDI.Prioridad, Literal(get_count(), datatype=XSD.integer)))

            # Creacion de la ciudad (por ahora Barcelona) --------------------------------------------------------------
            subject_ciudad = ECSDI['Ciudad_' + str(random.randint(1, sys.float_info.max))]

            gr.add((subject_ciudad, RDF.type, ECSDI.Ciudad))
            gr.add((subject_ciudad, ECSDI.Nombre, Literal(41.398373, datatype=XSD.float)))
            gr.add((subject_ciudad, ECSDI.Latitud, Literal(2.188247, datatype=XSD.float)))
            gr.add((subject_ciudad, ECSDI.Longitud, Literal('Barcelona', datatype=XSD.string)))

            # Creacion del sobre (Compra) ------------------------------------------------------------------------------
            subject_sobre = ECSDI['Compra_' + str(random.randint(1, sys.float_info.max))]
            gr.add((subject_sobre, RDF.type, ECSDI.Compra))

            gr.add((subject_sobre, ECSDI.Pagat, Literal(0, datatype=XSD.integer)))
            gr.add((subject_sobre, ECSDI.Enviar_a, URIRef(subject_ciudad)))

            total_price = 0.0

            for item in products_checked:
                total_price += float(item[3])
                # Creacion del producto --------------------------------------------------------------------------------
                subject_producto = item[4]
                gr.add((subject_producto, RDF.type, ECSDI.Producto))
                gr.add((subject_producto, ECSDI.Marca, Literal(item[0], datatype=XSD.string)))
                gr.add((subject_producto, ECSDI.Modelo, Literal(item[1], datatype=XSD.string)))
                gr.add((subject_producto, ECSDI.Nombre, Literal(item[2], datatype=XSD.string)))
                gr.add((subject_producto, ECSDI.Precio, Literal(item[3], datatype=XSD.float)))
                gr.add((subject_producto, ECSDI.Peso, Literal(item[5], datatype=XSD.float)))
                gr.add((subject_sobre, ECSDI.Productos, URIRef(subject_producto)))

            gr.add((subject_sobre, ECSDI.Precio_total, Literal(total_price, datatype=XSD.float)))

            gr.add((content, ECSDI.Sobre, URIRef(subject_sobre)))

            seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

            answer = send_message(
                build_message(gr, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri,
                              msgcnt=get_count(),
                              content=content), seller.address)

            products_matrix = []
            for item in answer.subjects(RDF.type, ECSDI.Producto):
                product = [answer.value(subject=item, predicate=ECSDI.Marca),
                           answer.value(subject=item, predicate=ECSDI.Modelo),
                           answer.value(subject=item, predicate=ECSDI.Nombre),
                           answer.value(subject=item, predicate=ECSDI.Precio)]
                products_matrix.append(product)

            return render_template('endSell.html', products=products_matrix)


@app.route("/retorna", methods=['GET', 'POST'])
def browser_retorna():
    global compres
    if request.method == 'GET':
        logger.info('Mostramos las compras realizadas')
        count, counts = get_all_sells()
        return render_template('retorna.html', compres=compres, count=count, sizes=counts)
    else:
        logger.info('Empezamos el proceso de devolucion')
        sells_checked = []
        for item in request.form.getlist("checkbox"):
            sells_checked.append(compres[int(item)][0])

        logger.info("Creando la peticion de compra")
        g = Graph()
        content = ECSDI['Peticion_retorno_' + str(get_count())]
        g.add((content, RDF.type, ECSDI.Peticion_retorno))
        for item in sells_checked:
            g.add((content, ECSDI.CompraRetornada, URIRef(item)))

        seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

        send_message(
            build_message(g, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri,
                          msgcnt=get_count(),
                          content=content), seller.address)

        return render_template('endRetorna.html')


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


def get_all_sells():
    # [0] = url / [1] = [{producte}] / [2] = precio_total
    global compres
    compres = []

    biggest_sell = 0
    counts = []

    graph_compres = Graph()
    graph_compres.parse(open('../data/compres'), format='turtle')

    for compraUrl in graph_compres.subjects(RDF.type, ECSDI.Compra):
        sell_count = 0
        single_sell = [compraUrl]
        products = []
        for productUrl in graph_compres.objects(subject=compraUrl, predicate=ECSDI.Productos):
            sell_count += 1
            products.append(graph_compres.value(subject=productUrl, predicate=ECSDI.Nombre))
        single_sell.append(products)
        for precio_total in graph_compres.objects(subject=compraUrl, predicate=ECSDI.Precio_total):
            single_sell.append(precio_total)
        compres.append(single_sell)
        counts.append(sell_count)
        if sell_count > biggest_sell:
            biggest_sell = sell_count

    return biggest_sell, counts


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1)
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port, debug=True)

    # Esperamos a que acaben los behaviors
    ab1.join()
    logger.info('The End')
