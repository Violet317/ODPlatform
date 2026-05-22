from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from odp_platform.data_validation import validate_dataset
from odp_platform.data_validation.render import render_to_logger


@pytest.fixture
def healthy_yaml(tmp_path):
    """Create a minimal healthy dataset yaml for e2e testing."""
    data_root = tmp_path / "data"
    for split in ("train", "val"):
        img_dir = data_root / split / "images"
        lbl_dir = data_root / split / "labels"
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)

        # Use unique stems across splits to avoid split_uniqueness violation
        stem = "img_000" if split == "train" else "img_001"
        (img_dir / f"{stem}.jpg").write_text("fake image content", encoding="utf-8")
        (lbl_dir / f"{stem}.txt").write_text("0 0.5 0.5 0.2 0.2", encoding="utf-8")

    yaml_path = tmp_path / "dataset.yaml"
    doc = {
        "path": str(data_root),
        "train": "train",
        "val": "val",
        "nc": 1,
        "names": ["person"],
        "task": "detect",
    }
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f)
    return yaml_path


@pytest.fixture
def broken_label_yaml(tmp_path):
    """Create dataset with broken label for e2e error testing."""
    data_root = tmp_path / "data_broken"
    for split in ("train", "val"):
        img_dir = data_root / split / "images"
        lbl_dir = data_root / split / "labels"
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)

        # Valid image-label pair
        (img_dir / "img_001.jpg").write_text("fake", encoding="utf-8")
        (lbl_dir / "img_001.txt").write_text("0 0.5 0.5 0.2 0.2", encoding="utf-8")

        # Image with broken label (class id out of range)
        (img_dir / "img_002.jpg").write_text("fake", encoding="utf-8")
        (lbl_dir / "img_002.txt").write_text("5 0.5 0.5 0.2 0.2", encoding="utf-8")

        # Image with missing label
        (img_dir / "img_003.jpg").write_text("fake", encoding="utf-8")

    yaml_path = tmp_path / "dataset_broken.yaml"
    doc = {
        "path": str(data_root),
        "train": "train",
        "val": "val",
        "nc": 3,
        "names": ["cat", "dog", "bird"],
        "task": "detect",
    }
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f)
    return yaml_path


class TestE2E:
    def test_healthy_dataset_exit_zero(self, healthy_yaml):
        report = validate_dataset(yaml_path=healthy_yaml, task_type="detect", write_report=False)
        assert report.exit_code == 0
        assert report.overall_severity == "PASS"
        assert report.report_path is None  # write_report=False

    def test_healthy_dataset_has_all_checks(self, healthy_yaml):
        report = validate_dataset(yaml_path=healthy_yaml, task_type="detect", write_report=False)
        names = {r.name for r in report.results}
        assert names == {"yaml_schema", "pair_existence", "label_format", "split_uniqueness"}

    def test_healthy_dataset_report_json(self, healthy_yaml, tmp_path):
        report = validate_dataset(yaml_path=healthy_yaml, task_type="detect", write_report=True)
        assert report.report_path is not None
        assert report.report_path.exists()
        import json
        data = json.loads(report.report_path.read_text(encoding="utf-8"))
        assert "meta" in data
        assert "run_id" in data["meta"]
        assert "validation_result" in data
        assert data["validation_result"]["exit_code"] == 0

    def test_broken_label_detects_errors(self, broken_label_yaml):
        report = validate_dataset(yaml_path=broken_label_yaml, task_type="detect", write_report=False)
        assert report.exit_code == 2
        label_result = [r for r in report.results if r.name == "label_format"][0]
        assert label_result.severity == "ERROR"

    def test_broken_label_pair_existence_error(self, broken_label_yaml):
        """Broken dataset has 1 missing label out of 4 images = 25% > 5% warn threshold"""
        report = validate_dataset(yaml_path=broken_label_yaml, task_type="detect", write_report=False)
        pair_result = [r for r in report.results if r.name == "pair_existence"][0]
        assert pair_result.severity != "PASS"  # WARN or higher

    def test_render_does_not_crash(self, healthy_yaml):
        report = validate_dataset(yaml_path=healthy_yaml, task_type="detect", write_report=False)
        # render should not raise
        render_to_logger(report)