import pytest
from pydantic import ValidationError

from twilio_provider.app.config import TwilioSettings


def test_valid_settings():
    s = TwilioSettings(account_sid="ACabc", auth_token="t", from_number="+14155550100")
    assert s.ring_timeout_seconds == 30
    assert s.auth_token.get_secret_value() == "t"


@pytest.mark.parametrize("field,value", [("account_sid", "XXabc"), ("from_number", "4155550100")])
def test_invalid_settings(field, value):
    data = dict(account_sid="ACabc", auth_token="t", from_number="+14155550100") | {field: value}
    with pytest.raises(ValidationError):
        TwilioSettings(**data)


def test_secret_not_in_repr():
    s = TwilioSettings(account_sid="ACabc", auth_token="TOPSECRET", from_number="+14155550100")
    assert "TOPSECRET" not in repr(s) and "TOPSECRET" not in str(s)
