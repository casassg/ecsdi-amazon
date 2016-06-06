import logging
import random

import datetime
from rdflib import Graph, Literal

from ACLMessages import build_message
from OntologyNamespaces import ECSDI, ACL
from utils.Agent import Agent


def dateToMillis(date):
    return (date - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000.0


class ExternalTransportAgent(Agent):
    def __init__(self, name, uri, address, stop, random_seed=1):
        Agent.__init__(self, name, uri, address, stop)
        self.last_price = None
        self.random_seed = abs(random_seed) + 1

    def proposal(self, due_date, weight, city):
        delivery_date = datetime.datetime.now() + datetime.timedelta(days=5)
        if due_date < delivery_date:
            self.reset()
            return build_message(Graph(), ACL.refuse, sender=self.uri)
        gr = Graph()
        gr.bind('ecsdi', ECSDI)
        oferta = ECSDI.Oferta_transporte
        preu = weight * self.random_seed
        self.last_price = preu
        gr.add((oferta, ECSDI.Precio_envio, Literal(preu)))
        gr.add((oferta, ECSDI.Entrega, Literal(dateToMillis(delivery_date))))
        gr = build_message(gr, ACL.propose, sender=self.uri, content=oferta)
        logging.info('Sending proposal for ' + str(preu))
        return gr

    def accept_couterproposal(self, new_price):
        if self.last_price and new_price >= 1.0:
            return new_price >= self.last_price - 5
        else:
            return False

    def answer_couter_proposal(self, new_price):
        gr = Graph()
        if self.accept_couterproposal(new_price.toPython()):
            gr = build_message(gr, ACL.agree, sender=self.uri)
            logging.info('Sending counter-proposal for ' + str(new_price))
            return gr
        else:
            logging.info('Rejecting counter-proposal for ' + str(new_price))
            gr = build_message(Graph(), ACL.reject, sender=self.uri)
            return gr

    def proposal_accepted(self):
        self.last_price = None

    def reset(self):
        self.last_price = None
        self.random_seed = random.randrange(1, 10)
