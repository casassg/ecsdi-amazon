# -*- coding: utf-8 -*-

from flask import request

__author__ = 'amazadonde'


def shutdown_server():

    """
    Funcion que para el servidor web
    :raise RuntimeError:
    """

    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


