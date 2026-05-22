from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from odp_platform.data_pipeline import list_capabilities
from odp_platform.data_pipeline.registry import ConvertOptions, get_converter


class TestE2ESmoke:
    def test_list_capabilities_has_all_formats(self):
        caps = list_capabilities()
        for fmt in ("pascal_voc", "coco", "yolo"):
            assert fmt in caps, f"缺少 {fmt}"

    def test_each_converter_is_callable(self):
        for fmt in ("pascal_voc", "coco", "yolo"):
            entry = get_converter(fmt)
            assert callable(entry.func), f"{fmt} 的 func 不可调用"

    def test_pascal_voc_conversion(self):
        tmpdir = Path(tempfile.mkdtemp())
        ann_dir = tmpdir / "annotations"
        ann_dir.mkdir()
        out_dir = tmpdir / "out"

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<annotation>
  <size><width>800</width><height>600</height></size>
  <object>
    <name>cat</name>
    <bndbox><xmin>100</xmin><ymin>100</ymin><xmax>300</xmax><ymax>300</ymax></bndbox>
  </object>
</annotation>"""
        (ann_dir / "test.xml").write_text(xml, encoding="utf-8")

        entry = get_converter("pascal_voc")
        classes = entry.func(ann_dir, out_dir, ConvertOptions())
        assert classes == ["cat"]
        txt = out_dir / "test.txt"
        assert txt.exists()
        assert txt.read_text(encoding="utf-8").strip() != ""