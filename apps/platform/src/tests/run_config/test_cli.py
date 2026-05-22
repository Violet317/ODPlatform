import subprocess
import sys
from pathlib import Path


def _run_odp_config(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "odp_platform.cli.config_cli", *args],
        capture_output=True, text=True,
    )


class TestCliGenerate:
    def test_generate_help(self):
        result = _run_odp_config("generate", "--help")
        assert result.returncode == 0
        assert "--task" in result.stdout or "--task" in result.stderr

    def test_generate_train_config(self, tmp_path):
        output = tmp_path / "train_config.yaml"
        result = _run_odp_config("generate", "--task", "train", "--output", str(output))
        assert result.returncode == 0
        assert output.exists()

    def test_generate_val_config(self, tmp_path):
        output = tmp_path / "val_config.yaml"
        result = _run_odp_config("generate", "--task", "val", "--output", str(output))
        assert result.returncode == 0
        assert output.exists()

    def test_generate_predict_config(self, tmp_path):
        output = tmp_path / "predict_config.yaml"
        result = _run_odp_config("generate", "--task", "predict", "--output", str(output))
        assert result.returncode == 0
        assert output.exists()


class TestCliValidate:
    def test_validate_valid_config(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("model: yolo11n.pt\nepochs: 10\n", encoding="utf-8")
        result = _run_odp_config("validate", "--config", str(config), "--task", "train")
        assert "验证通过" in result.stdout or "验证通过" in result.stderr

    def test_validate_invalid_config(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("epochs: -1\n", encoding="utf-8")
        result = _run_odp_config("validate", "--config", str(config), "--task", "train")
        assert result.returncode != 0


class TestCliSnapshot:
    def test_snapshot_export_restore(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("model: yolo11x.pt\ndevice: '0'\nepochs: 300\n", encoding="utf-8")

        snap_path = tmp_path / "snapshot.json"
        result = _run_odp_config("snapshot", "export", "--yaml", str(config),
                                 "--task", "train", "--output", str(snap_path))
        assert result.returncode == 0
        assert snap_path.exists()

        result2 = _run_odp_config("snapshot", "restore", "--input", str(snap_path))
        assert "快照恢复验证通过" in result2.stdout or "快照恢复验证通过" in result2.stderr