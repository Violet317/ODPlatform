from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from odp_platform.data_validation.checks.yaml_schema import validate_yaml_schema
from odp_platform.data_validation.registry import CheckContext, CheckSeverity


def _make_yaml(tmp_path: Path, content: dict) -> Path:
    p = tmp_path / "test.yaml"
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(content, f)
    return p


class TestYamlSchemaCheck:
    def test_file_not_found(self, tmp_path):
        ctx = CheckContext(yaml_path=tmp_path / "nonexistent.yaml")
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "不存在" in result.summary

    def test_not_a_dict(self, tmp_path):
        p = tmp_path / "test.yaml"
        p.write_text("123", encoding="utf-8")
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "不是 dict" in result.summary

    def test_missing_nc(self, tmp_path):
        p = _make_yaml(tmp_path, {"names": ["cat"]})
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "缺少 nc" in result.summary

    def test_missing_names(self, tmp_path):
        p = _make_yaml(tmp_path, {"nc": 1})
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "缺少 names" in result.summary

    def test_nc_mismatch(self, tmp_path):
        p = _make_yaml(tmp_path, {"nc": 2, "names": ["cat"]})
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "!= nc" in result.summary

    def test_valid_yaml(self, tmp_path):
        p = _make_yaml(tmp_path, {"nc": 2, "names": ["cat", "dog"]})
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.PASS
        assert "校验通过" in result.summary

    def test_valid_yaml_dict_names(self, tmp_path):
        p = _make_yaml(tmp_path, {"nc": 2, "names": {0: "cat", 1: "dog"}})
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.PASS

    def test_yaml_parse_error(self, tmp_path):
        p = tmp_path / "test.yaml"
        p.write_text("{invalid: yaml: :", encoding="utf-8")
        ctx = CheckContext(yaml_path=p)
        result = validate_yaml_schema(ctx)
        assert result.severity == CheckSeverity.ERROR
        assert "解析失败" in result.summary