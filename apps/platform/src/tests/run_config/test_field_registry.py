from odp_platform.run_config.registry import register_field, get_field, list_fields, field_names
from odp_platform.run_config.schema import ConfigField


# Use unique names with test_ prefix + uuid to avoid conflicts with production fields
# NOTE: These tests share a global registry, so field names must be globally unique
_UNIQUE = "_test_reg_"

class TestFieldRegistration:

    def test_register_and_roundtrip(self):
        name = _UNIQUE + "001"
        field = ConfigField(
            name=name,
            type=str,
            default="hello",
            description="测试字段",
            group="测试",
        )
        registered = register_field(field)
        assert registered.name == name
        # get_field triggers lazy_init which registers production fields
        fetched = get_field(name)
        assert fetched.default == "hello"

    def test_duplicate_returns_original(self):
        name = _UNIQUE + "002"
        field = ConfigField(
            name=name,
            type=int,
            default=0,
            description="重复测试",
            group="测试",
        )
        first = register_field(field)
        second = register_field(field)
        assert first is second
        assert second.default == 0

    def test_get_nonexistent_raises(self):
        try:
            get_field(_UNIQUE + "nonexistent")
            assert False, "应抛出 KeyError"
        except (KeyError, ValueError):
            pass

    def test_list_fields_contains_test_entries(self):
        name = _UNIQUE + "003"
        field = ConfigField(
            name=name,
            type=str,
            default="a",
            description="列表测试",
            group="测试",
        )
        register_field(field)
        fields = list_fields()
        assert name in fields

    def test_field_names_contains_test_entries(self):
        name = _UNIQUE + "004"
        field = ConfigField(
            name=name,
            type=str,
            default="b",
            description="名称测试",
            group="测试",
        )
        register_field(field)
        names = field_names()
        assert name in names

    def test_list_fields_all_contains_production_fields(self):
        fields = list_fields()
        # Production fields should be present after lazy_init
        assert "model" in fields
        assert "device" in fields
        assert "task" in fields