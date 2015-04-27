'''
Created on Jun 14, 2010

@author: nick
'''
from logging import Handler
import logging
import pymysqlpool

class LogHandler(Handler):
    def __init__(self, level=pymysqlpool.log_level):
        Handler.__init__(self, level)
        self.formatter = logging.Formatter("%(asctime)s - %(name)s:%(threadName)s - %(levelname)s - %(message)s")
        
    def flush(self):
        if pymysqlpool.logger is not None:
            pymysqlpool.logger.flush()
    
    def close(self):
        if pymysqlpool.logger is not None:
            pymysqlpool.logger.close()
    
    def emit(self, record):
        if pymysqlpool.logger is not None:
            pymysqlpool.logger.write(record)
            
logger = logging.getLogger('pysqlpool')
logger.setLevel(pymysqlpool.log_level)
logger.addHandler(LogHandler())