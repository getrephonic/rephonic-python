import pytest

from rephonic.filters import encode_filters


class TestDict:
    def test_numeric_gte(self):
        assert encode_filters({"listeners": {"gte": 5000}}) == "listeners:gte:5000"

    def test_numeric_lte(self):
        assert encode_filters({"listeners": {"lte": 250000}}) == "listeners:lte:250000"

    def test_numeric_range(self):
        out = encode_filters({"founded": {"gte": 1517270400, "lte": 1589932800}})
        assert out == "founded:gte:1517270400,founded:lte:1589932800"

    def test_bool_plain_true(self):
        assert encode_filters({"active": True}) == "active:is:true"

    def test_bool_plain_false(self):
        assert encode_filters({"sponsored": False}) == "sponsored:is:false"

    def test_bool_explicit_is(self):
        assert encode_filters({"active": {"is": True}}) == "active:is:true"

    def test_enum_any(self):
        out = encode_filters({"categories": {"any": [1482, 1406]}})
        assert out == "categories:any:1482-1406"

    def test_enum_in(self):
        out = encode_filters({"categories": {"in": [1482, 1406]}})
        assert out == "categories:in:1482-1406"

    def test_string_enum(self):
        out = encode_filters({"locations": {"any": ["us", "gb"]}})
        assert out == "locations:any:us-gb"

    def test_single_value_list(self):
        assert encode_filters({"locations": {"any": ["us"]}}) == "locations:any:us"

    def test_combined_fields(self):
        out = encode_filters(
            {
                "listeners": {"gte": 5000},
                "active": True,
                "categories": {"any": [1482, 1406]},
                "locations": {"any": ["us"]},
            }
        )
        assert out == (
            "listeners:gte:5000,active:is:true,categories:any:1482-1406,locations:any:us"
        )

    def test_empty_dict(self):
        assert encode_filters({}) is None


class TestEscaping:
    def test_dash_in_sponsor_name(self):
        out = encode_filters({"sponsors": {"any": ["Harley-Davidson"]}})
        assert out == "sponsors:any:Harley\\-Davidson"

    def test_multiple_dashes(self):
        out = encode_filters({"sponsors": {"any": ["Harley-Davidson", "Apple"]}})
        assert out == "sponsors:any:Harley\\-Davidson-Apple"

    def test_comma_escaped(self):
        out = encode_filters({"sponsors": {"any": ["Foo, Inc"]}})
        assert "Foo\\, Inc" in out

    def test_colon_escaped(self):
        out = encode_filters({"sponsors": {"any": ["Foo:Bar"]}})
        assert "Foo\\:Bar" in out

    def test_backslash_escaped(self):
        out = encode_filters({"sponsors": {"any": ["Foo\\Bar"]}})
        assert "Foo\\\\Bar" in out


class TestInputTypes:
    def test_none(self):
        assert encode_filters(None) is None

    def test_string_pass_through(self):
        s = "listeners:gte:5000,active:is:true"
        assert encode_filters(s) == s

    def test_empty_string(self):
        assert encode_filters("") is None

    def test_list_of_clauses(self):
        out = encode_filters(["listeners:gte:5000", "active:is:true"])
        assert out == "listeners:gte:5000,active:is:true"

    def test_empty_list(self):
        assert encode_filters([]) is None


class TestErrors:
    def test_rejects_int_filter_value(self):
        with pytest.raises(TypeError, match="must be bool or dict"):
            encode_filters({"listeners": 5000})

    def test_rejects_string_filter_value(self):
        with pytest.raises(TypeError, match="must be bool or dict"):
            encode_filters({"active": "true"})

    def test_rejects_is_with_non_bool(self):
        with pytest.raises(TypeError, match="expects bool"):
            encode_filters({"active": {"is": "yes"}})

    def test_rejects_any_with_non_list(self):
        with pytest.raises(TypeError, match="expects a list"):
            encode_filters({"categories": {"any": 1482}})

    def test_rejects_any_with_empty_list(self):
        with pytest.raises(ValueError, match="non-empty list"):
            encode_filters({"categories": {"any": []}})

    def test_rejects_unknown_operator(self):
        with pytest.raises(ValueError, match="unknown operator"):
            encode_filters({"listeners": {"eq": 5000}})

    def test_rejects_empty_operator_dict(self):
        with pytest.raises(ValueError, match="is empty"):
            encode_filters({"listeners": {}})

    def test_rejects_wrong_top_level_type(self):
        with pytest.raises(TypeError, match="must be str, list, dict"):
            encode_filters(42)

    def test_rejects_non_string_list_item(self):
        with pytest.raises(TypeError, match="items must be str"):
            encode_filters(["listeners:gte:5000", 42])
