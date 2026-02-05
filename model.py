import sys
import cv2
import numpy as np
import torch
import torchvision
from log_code import Logger

logger = Logger.get_logs('model')

# model.py
# model.py
import sys

# Remove segmentation paths
sys.path = [p for p in sys.path if "yolov7_seg" not in p.lower()]

DET_PATH = r"C:\Users\sravs\Downloads\vedanta\yolov7"
sys.path.insert(0, DET_PATH)


from numpy import random
from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import non_max_suppression
from utils.torch_utils import select_device, TracedModel

class YoloV7:
    def __init__(self, weights):
        try:
            logger.info("Initializing YOLOv7 model...")
            self.weights = weights
            self.imgsz = 608
            self.device = select_device("")
            self.half = self.device.type != 'cpu'

            # Torch load patch
            import torch.serialization
            torch.serialization.add_safe_globals([np.core.multiarray._reconstruct])
            _real_torch_load = torch.load

            def torch_load_patch(*args, **kwargs):
                kwargs["weights_only"] = False
                return _real_torch_load(*args, **kwargs)

            torch.load = torch_load_patch

            # Load model
            self.model = attempt_load(self.weights, map_location=self.device)
            self.model = TracedModel(self.model, self.device, self.imgsz)

            self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
            self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

            # Warm-up
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device))
            logger.info("YOLOv7 model initialized successfully")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Model initialization failed: {e}, line {exc_tb.tb_lineno}")

    def clip_coords(self, boxes, img_shape):
        boxes[0].clamp_(0, img_shape[1])
        boxes[1].clamp_(0, img_shape[0])
        boxes[2].clamp_(0, img_shape[1])
        boxes[3].clamp_(0, img_shape[0])

    def scale_coords(self, img1_shape, coords, img0_shape, ratio_pad=None):
        coords = np.array(coords)
        if ratio_pad is None:
            gain = min(img1_shape[0]/img0_shape[0], img1_shape[1]/img0_shape[1])
            pad = ((img1_shape[1]-img0_shape[1]*gain)/2, (img1_shape[0]-img0_shape[0]*gain)/2)
        else:
            gain = ratio_pad[0][0]
            pad = ratio_pad[1]

        coords[[0,2]] -= pad[0]
        coords[[1,3]] -= pad[1]
        coords[:4] /= gain
        coords = torch.tensor(coords)
        self.clip_coords(coords, img0_shape)
        return coords

    def inference(self, frame):
        try:
            img = letterbox(frame, self.imgsz, stride=32)[0]
            img = img[:, :, ::-1].transpose(2,0,1)
            img = np.ascontiguousarray(img)

            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()
            img /= 255.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            with torch.no_grad():
                pred = self.model(img, augment=False)[0]

            pred = non_max_suppression(pred, 0.25, 0.45)
            detections = []

            for det in pred:
                if len(det):
                    for *xyxy, conf, cls in reversed(det):
                        prediction = [self.names[int(cls)], round(conf.item(),2)]
                        coords = [c.item() for c in xyxy]
                        coords = self.scale_coords(img.shape[2:], coords, frame.shape[:2]).round()
                        coords = [int(c) for c in coords]
                        prediction.append(coords)
                        detections.append(prediction)

            # Convert image back for display
            img_disp = img.squeeze(0)
            img_disp = torchvision.transforms.ToPILImage()(img_disp)
            img_disp = np.array(img_disp).transpose(1,0,2)
            img_disp = cv2.cvtColor(img_disp, cv2.COLOR_RGB2BGR)

            return detections, img_disp

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Inference error: {e}, line {exc_tb.tb_lineno}")
            return [], frame

