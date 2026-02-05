from log_code import Logger
logger = Logger.get_logs('threads_creation')

import multiprocessing
import threading
import os
import sys
import time
from frame import Frame

class THREADS:

    def __init__(self):
        pass

    def thread_worker(self, cam, data):
        # Log unique thread ID inside the thread
        self.fra = Frame()
        th_id=threading.get_ident()
        logger.info(f" started thread with ThreadID: {th_id} | PID: {os.getpid()}] Running thread for: {cam}")
        self.fra.video_path_gather(cam,data,th_id)
        time.sleep(2)



    def creating_threads(self, cam_group, data):
        #logger.info(f"[MainThreadID in Process: {threading.get_ident()} | PID: {os.getpid()}] Starting threads for group: {cam_group}")

        threads = []
        for cam in cam_group:
            t = threading.Thread(target=self.thread_worker, args=(cam,data))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def creating_processors(self, data, cams):
        try:
            logger.info('creating_processors started')
            processes = []

            for i in range(0, len(cams), 2):
                cam_group = cams[i:i + 2]

                p = multiprocessing.Process(
                    target=self.creating_threads,
                    args=(cam_group,data)
                )
                p.start()
                logger.info(f"[PID: {p.pid}] Started process for cam_group: {cam_group}")
                processes.append(p)
            for p in processes:
                p.join()
        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
