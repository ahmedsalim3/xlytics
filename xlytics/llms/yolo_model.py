import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from ultralytics import YOLO

from ..commons.logger import Logger
from ..config.config import ModelConfig

logger = Logger()


class YoloModel:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.yolo_base_model_path = Path(config.get("YOLO_MODEL"))
        self.model = self._load_yolo()
        self.last_results = None

    def _load_yolo(self) -> Optional[YOLO]:
        try:
            if not self.yolo_base_model_path.exists():
                self.yolo_base_model_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Downloading YOLO model to: {self.yolo_base_model_path}...")
            model = YOLO(str(self.yolo_base_model_path))
            logger.info("YOLO model loaded successfully.")
            return model
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return None

    def detect(self, image: np.ndarray, conf: float = 0.5) -> List[Dict[str, Any]]:
        if self.model is None:
            logger.error("YOLO model not loaded.")
            return []

        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.model(image_rgb, conf=conf)
            self.last_results = results

            detections = []
            for result in results:
                detections.append(self._parse_result(result))
            return detections
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return []

    def _parse_result(self, result) -> Dict[str, Any]:
        parsed = {
            "boxes": [],
            "masks": [],
            "keypoints": [],
            "probs": [],
            "speed": result.speed,
            "image_shape": result.orig_img.shape,
        }

        # bounding boxes
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names.get(cls_id, str(cls_id))
                center = [(x1 + x2) // 2, (y1 + y2) // 2]
                area = (x2 - x1) * (y2 - y1)

                parsed["boxes"].append(
                    {
                        "bbox": [x1, y1, x2, y2],
                        "center": center,
                        "area": area,
                        "confidence": conf,
                        "class": class_name,
                        "class_id": cls_id,
                    }
                )

        # segmentation
        if result.masks is not None and hasattr(result.masks, "xy"):
            parsed["masks"] = [polygon.tolist() for polygon in result.masks.xy]

        # pose estimation
        if result.keypoints is not None:
            parsed["keypoints"] = result.keypoints.data.cpu().numpy().tolist()

        # classification
        if result.probs is not None:
            parsed["probs"] = result.probs.data.cpu().numpy().tolist()

        return parsed
