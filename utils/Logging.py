import logging

__author__ = 'amazadonde'


def config_logger(level=0, fileLogger=None):

    """
    Configure the logging of a program
    Log is written in stdio, alternatively also in a file

    :param level: If level is 0 only errors are logged, else all is logged
    :param fileLogger: Log is written in a file,
    :return:
    """

    if fileLogger is not None:
        logging.basicConfig(filename=fileLogger + '.log', filemode='w')

    # Logging configuration
    logger = logging.getLogger('log')
    if level == 0:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    if level == 0:
        console.setLevel(logging.ERROR)
    else:
        console.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)-15s] - %(filename)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('log').addHandler(console)
    return logger
