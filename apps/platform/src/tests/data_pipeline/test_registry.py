from __future__ import annotations

import pytest

from odp_platform.data_pipeline.registry import (
    ConvertOptions,
    get_converter,
    get_supported_formats,
    list_capabilities,
)


class TestConvertOptions:
    def test_default_values(self):
        opts = ConvertOptions()
        assert opts.task == "detect"
        assert opts.classes is None
        assert opts.coco_cls91to80 is False

    def test_custom_values(self):
        opts = ConvertOptions(task="segment", classes=["cat", "dog"], coco_cls91to80=True)
        assert opts.task == "segment"
        assert opts.classes == ["cat", "dog"]
        assert opts.coco_cls91to80 is True


class TestRegistry:
    def test_supported_formats(self):
        fmts = get_supported_formats()
        assert "pascal_voc" in fmts
        assert "coco" in fmts
        assert "yolo" in fmts

    def test_capabilities(self):
        caps = list_capabilities()
        assert caps["pascal_voc"] == ("detect",)
        assert caps["coco"] == ("detect", "segment")
        assert caps["yolo"] == ("detect", "segment")

    def test_get_converter_unknown_raises(self):
        with pytest.raises(ValueError, match="未注册的格式"):
            get_converter("unknown_format")

    def test_get_converter_returns_entry(self):
        entry = get_converter("pascal_voc")
        assert callable(entry.func)
        assert entry.supported_tasks == ("detect",)

        entry = get_converter("coco")
        assert callable(entry.func)
        assert "segment" in entry.supported_tasks

        entry = get_converter("yolo")
        assert callable(entry.func)
        assert "detect" in entry.supported_tasks
        assert "segment" in entry.supported_tasks