from __future__ import annotations

import cv2
import numpy as np

from odp_platform.inference.engine import Detection

# 每种类别对应的 BGR 颜色（循环使用）
_COLORS: list[tuple[int, int, int]] = [
    (56, 56, 255),   # 红
    (28, 230, 255),  # 黄
    (56, 156, 255),  # 橙
    (87, 223, 134),  # 绿
    (255, 140, 73),  # 青
    (214, 112, 218), # 紫
    (127, 127, 255), # 粉
    (0, 219, 255),   # 金
    (255, 108, 76),  # 天蓝
    (171, 77, 79),   # 棕
]


def _get_color(idx: int) -> tuple[int, int, int]:
    return _COLORS[idx % len(_COLORS)]


def draw_detections(
    image: np.ndarray,
    detections: list[Detection],
    thickness: int = 2,
    font_scale: float = 0.5,
) -> np.ndarray:
    """在图像上绘制检测框和标签。

    Args:
        image: 输入图像 (H, W, 3) numpy 数组
        detections: Detection 对象列表
        thickness: 边框线宽
        font_scale: 文字大小

    Returns:
        带标注的可视化图像 (H, W, 3) BGR
    """
    vis = image.copy()

    # 按类别首字母排序以保持颜色一致性
    class_set: dict[str, int] = {}
    for d in detections:
        if d.class_name not in class_set:
            class_set[d.class_name] = len(class_set)

    for d in detections:
        color_idx = class_set[d.class_name]
        color = _get_color(color_idx)

        x1, y1, x2, y2 = [int(v) for v in d.bbox]

        # 边框
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, thickness)

        # 标签
        label = f"{d.class_name} {d.confidence:.2f}"
        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        text_y = y1 - 4 if y1 - text_h - 4 > 0 else y1 + text_h + 4

        cv2.rectangle(
            vis,
            (x1, text_y - text_h - 4),
            (x1 + text_w + 4, text_y + 2),
            color,
            -1,
        )
        cv2.putText(
            vis,
            label,
            (x1 + 2, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    return vis