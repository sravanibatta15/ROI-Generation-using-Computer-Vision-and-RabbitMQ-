from log_code import Logger
logger = Logger.get_logs('main')
import os
import sys
from thread_processor import THREADS
from connection import CONNECTION

class VEDANATA:
    try:
        def __init__(self):
            try:
                self.reg = CONNECTION()
                self.thred=THREADS()

                logger.info(f'started main file')
            except Exception:
                exc_type, exc_msg, exc_line = sys.exc_info()
                logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
        def connectiong_database(self):
            try:
                logger.info(f'started connecting database')
                self.data=self.reg.connecting_to_redis()
                logger.info(f'connected to redis data:{self.data}')
                self.cams=[]
                for i in self.data:
                    self.cams.append(i)
                logger.info(f'connected to redis cam:{self.cams}')
            except Exception:
                exc_type, exc_msg, exc_line = sys.exc_info()
                logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
        def threads_and_processors(self):
            try:
                logger.info(f'started threads and procesors creating started data')
                self.thred.creating_processors(self.data,self.cams)

                logger.info(f'threds and procesors created successfully')
            except Exception:
                exc_type, exc_msg, exc_line = sys.exc_info()
                logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
    except Exception:
        exc_type, exc_msg, exc_line = sys.exc_info()
        logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")


if __name__ == '__main__':
    try:
        obj=VEDANATA()
        obj.connectiong_database()
        obj.threads_and_processors()
    except Exception:
        exc_type, exc_msg, exc_line = sys.exc_info()
        logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
