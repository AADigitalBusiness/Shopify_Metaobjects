from shopify_metaobjects.errors import ValidationError
from shopify_metaobjects.validation import validate_fields_against_definition


def test_validate_allowed_keys():
    validate_fields_against_definition(
        [{"key": "title", "value": "x"}],
        allowed_keys=["title", "body"],
    )
    try:
        validate_fields_against_definition(
            [{"key": "nope", "value": "x"}],
            allowed_keys=["title"],
        )
        assert False, "expected ValidationError"
    except ValidationError:
        pass
