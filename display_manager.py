import sys
import cv2
from log_code import Logger

logger = Logger.get_logs('display_manager')


class Display:

    @staticmethod
    def show_frame(win_name, frame, detections=None, cam_name=None):
        try:
            # Log each detection if available
            if detections and cam_name:
                for det in detections:
                    cls_name, score, (x, y, w, h) = det

                    logger.info(f"Camera: {cam_name}, Detected: {cls_name}, Box: {x, y, w, h}")

            logger.info(f"Showing window: {win_name}")
            # cv2.imshow(win_name, frame)
            # cv2.waitKey(1)
        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    @staticmethod
    def close_win(win_name):
        try:
            if cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) >= 1:
                logger.info(f"Closing window: {win_name}")
                cv2.destroyWindow(win_name)
            else:
                logger.warning(f"Window does not exist: {win_name}")
        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")