from odp_platform.run_config.schema import (
    ConfigField, ConfigBundle, ConfigSnapshot,
    TraceReport, TraceRecord, ValidationError, ValidationWarning,
)


class TestConfigField:
    def test_basic_field(self):
        f = ConfigField(
            name="epochs",
            type=int,
            default=100,
            description="训练轮数",
            group="训练",
        )
        assert f.name == "epochs"
        assert f.default == 100
        assert not f.sensitive

    def test_sensitive_field(self):
        f = ConfigField(
            name="api_key",
            type=str,
            default="",
            description="API 密钥",
            group="安全",
            sensitive=True,
        )
        assert f.sensitive

    def test_field_with_choices(self):
        f = ConfigField(
            name="device",
            type=str,
            default="cpu",
            description="设备",
            group="模型",
            choices=("cpu", "0", "0,1"),
        )
        assert f.choices == ("cpu", "0", "0,1")


class TestTraceRecord:
    def test_basic_trace(self):
        r = TraceRecord(
            field="epochs",
            final_value=100,
            sources=(("代码默认值", 100), ("YAML 配置", 200)),
        )
        assert r.field == "epochs"
        assert r.final_value == 100
        assert len(r.sources) == 2

    def test_human_readable(self):
        r = TraceRecord(
            field="device",
            final_value="0",
            sources=(("代码默认值", "cpu"), ("YAML 配置", "0")),
        )
        text = r.human_readable()
        assert "[device]" in text
        assert "最终值 = '0'" in text
        assert "代码默认值" in text

    def test_to_dict(self):
        r = TraceRecord(
            field="epochs",
            final_value=100,
            sources=(("代码默认值", 50),),
        )
        d = r.to_dict()
        assert d["field"] == "epochs"
        assert d["final_value"] == 100
        assert d["sources"][0]["source"] == "代码默认值"


class TestTraceReport:
    def test_empty(self):
        r = TraceReport(records=())
        assert r.human_readable() == ""

    def test_multiple_records(self):
        r1 = TraceRecord(field="a", final_value=1, sources=(("src", 1),))
        r2 = TraceRecord(field="b", final_value=2, sources=(("src", 2),))
        report = TraceReport(records=(r1, r2))
        assert "a" in report.human_readable()
        assert "b" in report.human_readable()

    def test_to_dict(self):
        r = TraceRecord(field="x", final_value=3, sources=(("src", 3),))
        report = TraceReport(records=(r,))
        d = report.to_dict()
        assert len(d["records"]) == 1


class TestConfigBundle:
    def test_valid_property(self):
        bundle = ConfigBundle(
            task="train",
            config={"epochs": 100},
            trace=TraceReport(records=()),
            errors=[],
            warnings=[],
        )
        assert bundle.valid

    def test_invalid_property(self):
        bundle = ConfigBundle(
            task="train",
            config={"epochs": -1},
            trace=TraceReport(records=()),
            errors=[ValidationError(field="epochs", message="必须为正数", current_value=-1)],
            warnings=[],
        )
        assert not bundle.valid

    def test_to_ultralytics_args_excludes_internal(self):
        bundle = ConfigBundle(
            task="train",
            config={"task": "train", "experiment_name": "exp1", "epochs": 100},
            trace=TraceReport(records=()),
            errors=[],
            warnings=[],
        )
        args = bundle.to_ultralytics_args()
        assert "task" not in args
        assert "experiment_name" not in args
        assert args["epochs"] == 100

    def test_to_report_dict_masks_sensitive(self):
        from odp_platform.run_config.registry import register_field
        register_field(ConfigField(
            name="api_key",
            type=str,
            default="",
            description="key",
            group="安全",
            sensitive=True,
        ))
        bundle = ConfigBundle(
            task="train",
            config={"api_key": "sk-12345", "epochs": 100},
            trace=TraceReport(records=(
                TraceRecord(field="api_key", final_value="sk-12345", sources=(("默认值", ""),)),
            )),
            errors=[],
            warnings=[],
        )
        report = bundle.to_report_dict(mask_sensitive=True)
        assert report["config"]["api_key"] == "***"
        assert report["config"]["epochs"] == 100
        assert report["trace"]["records"][0]["final_value"] == "***"


class TestConfigSnapshot:
    def test_from_bundle(self):
        bundle = ConfigBundle(
            task="train",
            config={"epochs": 100, "lr": 0.01},
            trace=TraceReport(records=()),
            errors=[],
            warnings=[],
        )
        snapshot = ConfigSnapshot.from_bundle(bundle)
        assert snapshot.task == "train"
        assert snapshot.config["epochs"] == 100
        assert snapshot.created_at != ""

    def test_roundtrip_dict(self):
        snapshot = ConfigSnapshot(
            task="val",
            config={"batch": 16},
            created_at="2026-01-01T00:00:00+00:00",
        )
        d = snapshot.to_dict()
        restored = ConfigSnapshot.from_dict(d)
        assert restored.task == "val"
        assert restored.config["batch"] == 16
        assert restored.version == 1

    def test_snapshot_frozen(self):
        import pytest
        snapshot = ConfigSnapshot(task="train", config={"a": 1})
        with pytest.raises(AttributeError):
            snapshot.task = "val"