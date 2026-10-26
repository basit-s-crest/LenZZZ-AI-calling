"""The SDK wrapper: SDK exceptions must become TwilioAPIError (and never leak secrets)."""
import asyncio

import pytest
from twilio.base.exceptions import TwilioRestException

from twilio_provider.clients.twilio_client import TwilioClient
from twilio_provider.core.errors import TwilioAPIError


class _Call:
    sid, status = "CA1", "queued"


def _client(create):
    c = TwilioClient("ACtest", "SECRET-TOKEN")
    c._client.calls.create = create          # replace the SDK call; no network
    return c


def run(coro):
    return asyncio.run(coro)


def test_success_maps_sid_and_status():
    c = _client(lambda **kw: _Call())
    r = run(c.create_call(to="+1", from_="+2", twiml="<Response/>", timeout=30))
    assert (r.sid, r.status) == ("CA1", "queued")


def test_rest_exception_mapped():
    def boom(**kw):
        raise TwilioRestException(status=400, uri="/Calls", msg="bad number", code=21211)

    with pytest.raises(TwilioAPIError) as e:
        run(_client(boom).create_call(to="+1", from_="+2", twiml="x", timeout=30))
    assert e.value.http_status == 400 and e.value.twilio_code == 21211


def test_network_error_mapped_without_leaking_details():
    def boom(**kw):
        raise ConnectionError("https://SECRET-TOKEN@api.twilio.com failed")

    with pytest.raises(TwilioAPIError) as e:
        run(_client(boom).create_call(to="+1", from_="+2", twiml="x", timeout=30))
    assert "SECRET-TOKEN" not in str(e.value) and e.value.http_status is None
