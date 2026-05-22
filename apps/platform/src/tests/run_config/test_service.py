import json
from pathlib import Path

from odp_platform.run_config.service import build_config, restore_from_snapshot, save_snapshot_to_file, load_snapshot_from_file
from odp_platform.run_config.schema import ConfigSnapshot


class TestBuildConfig:
    def test_build_with_defaults_only(self):
        bundle = build_config(task="train")
        assert bundle.task == "train"
        assert "model" in bundle.config
        assert bundle.valid
        assert len(bundle.trace.records) > 0

    def test_build_with_preview_only(self):
        bundle = build_config(task="train", preview_only=True)
        assert bundle.valid
        assert len(bundle.errors) == 0

    def test_build_with_yaml(self, tmp_path):
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("model: yolo11x.pt\ndevice: '0'\n", encoding="utf-8")
        bundle = build_config(task="train", yaml_path=yaml_path)
        assert bundle.config["model"] == "yolo11x.pt"
        assert bundle.config["device"] == "0"

    def test_build_with_missing_yaml(self):
        bundle = build_config(task="train", yaml_path=Path("/nonexistent/config.yaml"))
        assert not bundle.valid
        assert any("文件不存在" in e.message for e in bundle.errors)

    def test_build_with_cli_args(self):
        bundle = build_config(task="train", cli_args={"model": "yolo11n.pt", "epochs": 50})
        assert bundle.config["model"] == "yolo11n.pt"
        assert bundle.config["epochs"] == 50

    def test_build_cli_overrides_yaml(self, tmp_path):
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("model: yolo11x.pt\nepochs: 100\n", encoding="utf-8")
        bundle = build_config(task="train", yaml_path=yaml_path, cli_args={"epochs": 200})
        assert bundle.config["model"] == "yolo11x.pt"
        assert bundle.config["epochs"] == 200


class TestSnapshotRoundtrip:
    def test_export_and_restore(self, tmp_path):
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("model: yolo11x.pt\ndevice: '0'\nepochs: 300\n", encoding="utf-8")

        bundle = build_config(task="train", yaml_path=yaml_path, preview_only=True)
        assert bundle.valid

        snapshot = ConfigSnapshot.from_bundle(bundle)
        snap_path = tmp_path / "snapshot.json"
        save_snapshot_to_file(snapshot, snap_path)

        assert snap_path.exists()
        loaded = load_snapshot_from_file(snap_path)
        assert loaded.task == "train"
        assert loaded.config["epochs"] == 300

        restored = restore_from_snapshot(loaded)
        assert restored.valid
        assert restored.config["model"] == "yolo11x.pt"
        assert restored.config["device"] == "0"

    def test_snapshot_file_format(self, tmp_path):
        snapshot = ConfigSnapshot(
            task="val",
            config={"batch": 32, "imgsz": 640},
            created_at="2026-05-22T00:00:00",
        )
        path = save_snapshot_to_file(snapshot, tmp_path / "snap.json")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["task"] == "val"
        assert data["config"]["batch"] == 32
        assert data["version"] == 1