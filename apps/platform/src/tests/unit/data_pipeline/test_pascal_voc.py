from pathlib import Path

import pytest

from odp_platform.data_pipeline.core.pascal_voc import convert_voc
from odp_platform.data_pipeline.registry import ConvertOptions


class TestPascalVOCConverter:
    def _create_voc_xml(self, tmp_path: Path) -> tuple[Path, Path]:
        ann_dir = tmp_path / "annotations"
        out_dir = tmp_path / "yolo"
        ann_dir.mkdir(parents=True)

        xml_content = """<?xml version="1.0"?>
<annotation>
    <filename>img001.jpg</filename>
    <size>
        <width>640</width>
        <height>480</height>
        <depth>3</depth>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>150</ymin>
            <xmax>300</xmax>
            <ymax>400</ymax>
        </bndbox>
    </object>
</annotation>"""
        (ann_dir / "img001.xml").write_text(xml_content, encoding="utf-8")
        return ann_dir, out_dir

    def test_convert_basic(self, tmp_path):
        ann_dir, out_dir = self._create_voc_xml(tmp_path)
        classes = convert_voc(ann_dir, out_dir, ConvertOptions())
        assert classes == ["person"]
        txt = out_dir / "img001.txt"
        assert txt.exists()
        content = txt.read_text(encoding="utf-8").strip()
        assert len(content) > 0

    def test_no_xml_raises(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="未找到任何 XML"):
            convert_voc(empty_dir, tmp_path / "out", ConvertOptions())