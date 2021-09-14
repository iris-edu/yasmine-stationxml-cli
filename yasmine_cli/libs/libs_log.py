import os

import logging
logger = logging.getLogger()

from logging.handlers import TimedRotatingFileHandler

def string_to_logLevel(levelString):
    '''
        levelString = 'INFO' or 'WARN' or 'WARNING', etc
    '''
    loglevels = {"ERROR": logging.ERROR, "WARN": logging.WARNING,
                 "WARNING": logging.WARNING, "INFO": logging.INFO,
                 "DEBUG": logging.DEBUG, "CRITICAL": logging.CRITICAL,
                }
    msg = " ".join(list(loglevels.keys()))

    if levelString in loglevels:
        #logger.setLevel(loglevels[levelString])
        return loglevels[levelString]
    else:
        logger.error("Unknown --loglevel=%s (not in:{%s})" % (levelString, msg))
        return None
        # exit(2)

def configure_logger(config, logfile, levelString=None):
    '''
        levelString = 'INFO' or 'WARN' or 'WARNING', etc
    '''
    # DEFAULTS
    DEFAULT_LOG_DIR = os.getcwd()
    DEFAULT_LOG_LEVEL = 'INFO'

    if config:
        LOGDIR = config['LOG_DIR'] if 'LOG_DIR' in config else DEFAULT_LOG_DIR
        log_level = config['LOG_LEVEL'] if 'LOG_LEVEL' in config else DEFAULT_LOG_LEVEL
    else:
        LOGDIR = DEFAULT_LOG_DIR
        log_level = DEFAULT_LOG_LEVEL

    if levelString:
        log_level = levelString

    logger.level = string_to_logLevel(log_level)

    logfile = os.path.join(LOGDIR, logfile)
    if not os.path.exists(LOGDIR):
        try:
            os.makedirs(LOGDIR)
        except:
            raise
    #print("configure_logger: log_file=[%s] level=[%s]" % (logfile, log_level))
    # create file handler 
    fh = TimedRotatingFileHandler(logfile, when="midnight")
    # create console handler 
    ch = logging.StreamHandler()

    #fh.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s [%(levelname)5s] %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return
