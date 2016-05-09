# -*- coding: utf-8 -*-

from rdflib import Graph
import requests
from rdflib.namespace import RDF
from utils.OntologyNamespaces import ACL

__author__ = 'amazadonde'


def build_message(graphMessage, perf, sender=None, receiver=None, content=None, msgcnt=0):

    """
    Construye un mensaje como una performativa FIPA acl
    Asume que en el grafo que se recibe esta ya el contenido y esta ligado al
    URI en el parametro contenido

    :param graphMessage: grafo RDF sobre el que se deja el mensaje
    :param perf: performativa del mensaje
    :param sender: URI del sender
    :param receiver: URI del receiver
    :param content: URI que liga el contenido del mensaje
    :param msgcnt: numero de mensaje
    :return:
    """

    # Add the speech act elements into message graph.
    mssid = 'message-' + str(sender.__hash__()) + '-{:{fill}4d}'.format(msgcnt, fill='0')
    ms = ACL[mssid]
    graphMessage.bind('acl', ACL)
    graphMessage.add((ms, RDF.type, ACL.FipaAclMessage))
    graphMessage.add((ms, ACL.performative, perf))
    graphMessage.add((ms, ACL.sender, sender))

    if receiver is not None:
        graphMessage.add((ms, ACL.receiver, receiver))
    if content is not None:
        graphMessage.add((ms, ACL.content, content))

    return graphMessage


def send_message(graphMessage, address):

    """
    Envia un mensaje usando un request y retorna la respuesta como
    un grafo RDF
    :param address: la dirección del mensaje
    :param graphMessage: el mensaje
    """

    message = graphMessage.serialize(format='xml')
    request = requests.get(address, params={'content': message})

    print request.status_code

    # Process the answer and return the result as a graph.
    gr = Graph()
    gr.parse(data=request.text)

    return gr


def get_message_properties(message):

    """
    Extrae las propiedades de un mensaje ACL como un diccionario.
    Del contenido solo saca el primer objeto al que apunta la propiedad

    Los elementos que no estan, no aparecen en el diccionario
    :param message: el mensaje
    """

    props = {'performative': ACL.performative, 'sender': ACL.sender,
             'receiver': ACL.receiver, 'ontology': ACL.ontology,
             'conversation-id': ACL['conversation-id'],
             'in-reply-to': ACL['in-reply-to'], 'content': ACL.content}
    # Dictionary where saves the message elements.
    messageDictionary = {}

    # We extract the FipaAclMessage message part.
    valid = message.value(predicate=RDF.type, object=ACL.FipaAclMessage)

    # We extract the message properties.
    if valid is not None:
        for key in props:
            val = message.value(subject=valid, predicate=props[key])
            if val is not None:
                messageDictionary[key] = val
    return messageDictionary
