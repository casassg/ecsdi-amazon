import time
from rdflib import Graph, RDF, Literal, URIRef

from utils.OntologyNamespaces import ECSDI
from agents.SellerAgent import findProducts


def create_message_restriccions_cerca():
    # Creamos el grafo
    graph = Graph()
    # Le asignamos nuestra ontologia
    graph.bind('ECSDI', ECSDI)

    # Creacion del array de restricciones de busqueda
    subject = ECSDI.Test
    graph.add((subject, RDF.type, ECSDI.Cerca_productes))

    # Creacion de la restriccion de modelo
    subjectRest = ECSDI.Test2
    graph.add((subjectRest, RDF.type, ECSDI.Restriccion_modelo))
    graph.add((subjectRest, ECSDI.Modelo, Literal('Garmin')))

    # Creacion de la restriccion de marca
    subjectRest2 = ECSDI.Test3
    graph.add((subjectRest2, RDF.type, ECSDI.Restriccion_Marca))
    graph.add((subjectRest2, ECSDI.Marca, Literal('Nintendo')))

    # Creacion de la restriccion de precio
    subjectRest3 = ECSDI.Test4
    graph.add((subjectRest3, RDF.type, ECSDI.Rango_Precio))
    graph.add((subjectRest3, ECSDI.Precio_max, Literal(2)))
    graph.add((subjectRest3, ECSDI.Precio_min, Literal(300)))

    # Anadir las dos restricciones
    graph.add((subject, ECSDI.Restringe, URIRef(subjectRest)))
    graph.add((subject, ECSDI.Restringe, URIRef(subjectRest2)))
    graph.add((subject, ECSDI.Restringe, URIRef(subjectRest3)))

    graph.serialize()

    # Guardar todas las restricciones en un solo objeto
    restriccions = graph.objects(subject, ECSDI.Restringe)
    for restriccio in restriccions:
        if graph.value(subject=restriccio, predicate=RDF.type) == ECSDI.Restriccion_Marca:
            print 'MARCA: ' + graph.value(subject=restriccio, predicate=ECSDI.Marca)
        elif graph.value(subject=restriccio, predicate=RDF.type) == ECSDI.Restriccion_modelo:
            print 'MODELO: ' + graph.value(subject=restriccio, predicate=ECSDI.Modelo)
        elif graph.value(subject=restriccio, predicate=RDF.type) == ECSDI.Rango_Precio:
            print 'PRECIO: ' + graph.value(subject=restriccio, predicate=ECSDI.Precio_max) + ' - ' + graph.value(
                subject=restriccio, predicate=ECSDI.Precio_min)


def create_message_product_list():
    # Creamos el grafo
    graph = Graph()
    # Le asignamos nuestra ontologia
    graph.bind('ECSDI', ECSDI)

    # Creacion del array de respuesta de la busqueda
    subject = ECSDI.Test
    graph.add((subject, RDF.type, ECSDI.Respuesta_busqueda))

    for product in findProducts():
        producto = ECSDI.Producto
        graph.add((producto, RDF.type, ECSDI.Producto))
        graph.add((producto, ECSDI.Marca, product['marca']))
        graph.add((producto, ECSDI.Nombre, product['nombre']))
        graph.add((producto, ECSDI.Modelo, product['marca']))
        graph.add((producto, ECSDI.Precio, product['precio']))
        graph.add((subject, ECSDI.lista_de_productos, Literal(producto)))

    graph.serialize()


create_message_product_list()
