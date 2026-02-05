import sys
import os
from log_code import Logger
logger = Logger.get_logs('frame')
import cv2
import numpy as np
from rabbitMq import MQ_SERVER


class Frame:

    def __init__(self):
        self.video_path=None
        self.cam_id=None
        self.rab_obj = MQ_SERVER()


    def video_path_gather(self,cam,data,th_id):
        try:
            self.video_path=data[cam]['video_path']
            self.cam_id=data[cam]['camera_id']
            logger.info(f"Video path is {self.video_path}")
            self.frame_capture(self.video_path,th_id,cam)


        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def frame_capture(self, video_path,th_id,cam_name):
        try:

            if os.path.exists(video_path):
                cap = cv2.VideoCapture(video_path)
                while True:
                    ret, frame = cap.read()
                    route_key = str(th_id) + "/" + str(self.cam_id) + "/" + cam_name
                    if ret:
                        _,encode=cv2.imencode('.jpg', frame)
                        frame_byte=np.array(encode).tobytes()
                        logger.info(f'routing key {route_key}')
                    else:
                        frame_byte= b""
                        break
                    self.rab_obj.sent_frame(route_key, frame_byte)
                cap.release()
                cv2.destroyAllWindows()

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
