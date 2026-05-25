from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from ultralytics import YOLO


@dataclass
class Detection:
    """单条检测结果。"""

    class_name: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2]


@dataclass
class DetectionResult:
    """一次推理的完整结果。"""

    detections: list[Detection] = field(default_factory=list)
    inference_ms: float = 0.0


class Detector:
    """YOLO 推理器，封装 Ultralytics YOLO 模型。"""

    def __init__(self, model_path: str) -> None:
        self._model = YOLO(model_path)
        self._conf: float = 0.25
        self._iou: float = 0.45

    @property
    def conf(self) -> float:
        return self._conf

    @conf.setter
    def conf(self, value: float) -> None:
        self._conf = float(value)

    @property
    def iou(self) -> float:
        return self._iou

    @iou.setter
    def iou(self, value: float) -> None:
        self._iou = float(value)

    @property
    def names(self) -> dict[int, str]:
        return self._model.names

    def detect(self, image: np.ndarray) -> DetectionResult:
        """在单张图像上运行目标检测。

        Args:
            image: numpy 图像数组 (H, W, C) RGB 或 BGR

        Returns:
            DetectionResult 包含检测列表和推理耗时 (ms)
        """
        t0 = time.perf_counter()
        results = self._model.predict(
            image,
            conf=self._conf,
            iou=self._iou,
            verbose=False,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0

        detections: list[Detection] = []
        names = self._model.names

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls.item())
                cls_name = names.get(cls_id, str(cls_id))
                conf_val = float(box.conf.item())
                xyxy = box.xyxy[0].tolist()
                detections.append(
                    Detection(
                        class_name=cls_name,
                        confidence=conf_val,
                        bbox=[round(v, 1) for v in xyxy],
                    )
                )

        return DetectionResult(detections=detections, inference_ms=round(elapsed, 1))