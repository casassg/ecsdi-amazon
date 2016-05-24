from rdflib import Graph, RDF, Literal

from utils.OntologyNamespaces import ECSDI


def create_message():
    graph = Graph()
    subject = ECSDI.Test
    graph.add((subject, RDF.type, ECSDI.Cerca_productes))

    restriccions = Graph()
    subjectRest = ECSDI.Test2
    restriccions.add((subjectRest, RDF.type, ECSDI.Restriccion_Marca))
    restriccions.add((subjectRest, ECSDI.Marca, Literal('Garmin')))

    graph.add((subject, ECSDI.Restringe, restriccions))
    graph.serialize()

create_message()