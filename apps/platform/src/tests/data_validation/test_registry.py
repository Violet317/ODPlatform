from __future__ import annotations

from pathlib import Path

import pytest

from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    get_check,
    list_checks,
)
from odp_platform.data_validation import check


class TestCheckSeverity:
    def test_rank_order(self):
        assert CheckSeverity.rank("ERROR") > CheckSeverity.rank("WARNING")
        assert CheckSeverity.rank("WARNING") > CheckSeverity.rank("INFO")
        assert CheckSeverity.rank("INFO") > CheckSeverity.rank("PASS")

    def test_rank_unknown(self):
        assert CheckSeverity.rank("UNKNOWN") == 0


class TestCheckResult:
    def test_passed_edge(self):
        assert CheckResult("t", CheckSeverity.PASS, "", {}).passed
        assert CheckResult("t", CheckSeverity.INFO, "", {}).passed
        assert not CheckResult("t", CheckSeverity.WARNING, "", {}).passed
        assert not CheckResult("t", CheckSeverity.ERROR, "", {}).passed


class TestCheckDecorator:
    def test_registered_check_is_callable(self):
        entry = get_check("yaml_schema")
        assert entry.name == "yaml_schema"
        assert callable(entry.func)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="未注册"):
            get_check("not_a_check")

    def test_list_checks_auto_discover(self):
        checks = list_checks()
        assert "yaml_schema" in checks
        assert "pair_existence" in checks
        assert "label_format" in checks
        assert "split_uniqueness" in checks

    def test_duplicate_registration_raises(self):
        from odp_platform.data_validation.registry import _REGISTRY, _lazy_init
        _lazy_init()
        with pytest.raises(ValueError, match="重复注册"):
            @check("yaml_schema")
            def dup(ctx):
                return CheckResult("yaml_schema", CheckSeverity.PASS, "", {})


class TestCheckContext:
    def test_yaml_path_conversion(self):
        ctx = CheckContext(yaml_path="some/path.yaml")
        assert isinstance(ctx.yaml_path, Path)