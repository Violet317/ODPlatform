from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr

from odp_platform.webui.utils import list_model_files


def _model_choices() -> list[str]:
    return list_model_files()


def _model_dropdown_choices() -> list[tuple[str, str]]:
    return [(Path(model_path).name, model_path) for model_path in _model_choices()]


def _refresh_models() -> gr.update:
    models = _model_choices()
    return gr.update(
        choices=[(Path(model_path).name, model_path) for model_path in models],
        value=models[0] if models else None,
    )


def _run_detection(
    image: Any,
    model_path: str,
    conf: float,
    iou: float,
) -> tuple[Any | None, list[dict[str, Any]], str]:
    if image is None:
        return None, [], "未选择图片"
    if not model_path:
        return None, [], "未选择模型"

    try:
        import numpy as np

        from odp_platform.inference.engine import Detector
        from odp_platform.inference.visualizer import draw_detections
    except ImportError as exc:
        return None, [], f"推理依赖未就绪: {exc}"

    try:
        detector = Detector(model_path)
        detector.conf = float(conf)
        detector.iou = float(iou)
        image_np = np.array(image)
        result = detector.detect(image_np)
        rendered = draw_detections(image_np, result.detections)
        rows = [
            {
                "class": detection.class_name,
                "conf": round(detection.confidence, 4),
                "bbox": list(detection.bbox),
            }
            for detection in result.detections
        ]
        status = f"{Path(model_path).name} | 检测数: {len(rows)} | {result.inference_ms:.1f} ms"
        return rendered, rows, status
    except Exception as exc:
        return None, [], f"检测失败: {exc}"


def _select_model(model_path: str) -> str:
    if not model_path:
        return "未选择模型"
    return f"当前模型: {Path(model_path).name}"


def _chat(message: str, history: list[dict[str, str]] | None) -> tuple[list[dict[str, str]], str]:
    text = (message or "").strip()
    history = list(history or [])
    if not text:
        return history, ""

    history.append({"role": "user", "content": text})
    history.append(
        {
            "role": "assistant",
            "content": "LLM 接口待接入，前端入口已预留。",
        }
    )
    return history, ""


def _clear_chat() -> tuple[list[dict[str, str]], str]:
    return [], ""


def create_image_detection_ui() -> None:
    models = _model_choices()
    model_options = _model_dropdown_choices()
    with gr.Row(elem_classes=["odp-row", "odp-row-four"]):
        model_dd = gr.Dropdown(
            choices=model_options,
            value=models[0] if models else None,
            label="模型",
            filterable=False,
            interactive=True,
        )
        refresh_btn = gr.Button("刷新")
        conf_slider = gr.Slider(0.01, 0.99, 0.25, step=0.01, label="Confidence")
        iou_slider = gr.Slider(0.01, 0.99, 0.45, step=0.01, label="IoU")
    with gr.Row(elem_classes=["odp-row", "odp-row-two"]):
        image_in = gr.Image(type="pil", label="输入")
        image_out = gr.Image(type="numpy", label="结果")
    detect_btn = gr.Button("开始检测", variant="primary")
    status = gr.Textbox(label="状态", value="等待检测", interactive=False, max_lines=1)
    result_json = gr.JSON(label="检测列表")

    refresh_btn.click(fn=_refresh_models, outputs=[model_dd])
    detect_btn.click(
        fn=_run_detection,
        inputs=[image_in, model_dd, conf_slider, iou_slider],
        outputs=[image_out, result_json, status],
    )


def create_detection_results_ui() -> None:
    with gr.Row(elem_classes=["odp-row", "odp-row-action"]):
        refresh_btn = gr.Button("刷新")
        status = gr.Textbox(label="状态", value="暂无检测结果", interactive=False, max_lines=1)
    results = gr.Dataframe(
        label="检测历史",
        headers=["ID", "模型", "状态", "目标数", "时间"],
        value=[],
        interactive=False,
        wrap=True,
    )
    details = gr.JSON(label="结果详情", value=[])

    refresh_btn.click(
        fn=lambda: ("暂无检测结果", [], []),
        outputs=[status, results, details],
    )


def create_model_selection_ui() -> None:
    models = _model_choices()
    model_options = _model_dropdown_choices()
    with gr.Row(elem_classes=["odp-row", "odp-row-action"]):
        refresh_btn = gr.Button("刷新")
        model_dd = gr.Dropdown(
            choices=model_options,
            value=models[0] if models else None,
            label="可用模型",
            filterable=False,
            interactive=True,
            scale=3,
        )
    with gr.Row(elem_classes=["odp-row", "odp-row-action"]):
        select_btn = gr.Button("设为当前模型", variant="primary")
        status = gr.Textbox(
            label="状态",
            value=_select_model(models[0]) if models else "未发现模型",
            interactive=False,
            max_lines=1,
            scale=3,
        )

    refresh_btn.click(fn=_refresh_models, outputs=[model_dd])
    select_btn.click(fn=_select_model, inputs=[model_dd], outputs=[status])


def create_llm_chat_ui() -> None:
    chatbot = gr.Chatbot(label="对话", type="messages", height=360)
    message = gr.Textbox(label="输入", placeholder="输入问题", max_lines=1)
    with gr.Row(elem_classes=["odp-row", "odp-row-two"]):
        send_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.Button("清空")

    send_btn.click(fn=_chat, inputs=[message, chatbot], outputs=[chatbot, message])
    message.submit(fn=_chat, inputs=[message, chatbot], outputs=[chatbot, message])
    clear_btn.click(fn=_clear_chat, outputs=[chatbot, message])


def create_user_info_ui() -> None:
    with gr.Row(elem_classes=["odp-row", "odp-row-three"]):
        gr.Textbox(label="用户名", value="guest", interactive=False, max_lines=1)
        gr.Textbox(label="角色", value="user", interactive=False, max_lines=1)
        gr.Textbox(label="状态", value="未登录", interactive=False, max_lines=1)
    gr.Dataframe(
        label="检测概览",
        headers=["指标", "值"],
        value=[
            ["检测任务", "0"],
            ["已完成", "0"],
            ["最近模型", ""],
        ],
        interactive=False,
        wrap=True,
    )
