from twilio_provider.core.errors import TwilioAPIError

BODY = {"to_number": "+919876543210"}


def test_create_call_success_uses_defaults(make_client):
    client, fake = make_client()
    r = client.post("/twilio/calls", json=BODY)
    assert r.status_code == 202
    assert r.json() == {
        "call_sid": "CA" + "0" * 32, "status": "queued",
        "to_number": "+919876543210", "from_number": "+14155550100",
    }
    sent = fake.calls[0]
    assert sent["to"] == "+919876543210" and sent["from_"] == "+14155550100" and sent["timeout"] == 25
    assert "<Say>default hello</Say>" in sent["twiml"]


def test_custom_message_and_from_number(make_client):
    client, fake = make_client()
    r = client.post("/twilio/calls", json={**BODY, "from_number": "+14155550199", "message": "Hi Rahul"})
    assert r.status_code == 202
    assert fake.calls[0]["from_"] == "+14155550199"
    assert "<Say>Hi Rahul</Say>" in fake.calls[0]["twiml"]


def test_message_is_xml_escaped(make_client):
    client, fake = make_client()
    client.post("/twilio/calls", json={**BODY, "message": "2 < 3 & <Dial>x</Dial>"})
    twiml = fake.calls[0]["twiml"]
    assert "<Dial>" not in twiml and "&lt;" in twiml


def test_invalid_number_rejected_before_calling_twilio(make_client):
    client, fake = make_client()
    for bad in ("9876543210", "+0123456", "abc", ""):
        assert client.post("/twilio/calls", json={"to_number": bad}).status_code == 422
    assert fake.calls == []


def test_message_length_limit(make_client):
    client, _ = make_client()
    assert client.post("/twilio/calls", json={**BODY, "message": "x" * 501}).status_code == 422
    assert client.post("/twilio/calls", json={**BODY, "message": ""}).status_code == 422


def test_cannot_call_the_caller_id(make_client):
    client, fake = make_client()
    r = client.post("/twilio/calls", json={"to_number": "+14155550100"})
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_call_request"
    assert fake.calls == []


def test_twilio_rejection_surfaces_hint(make_client):
    err = TwilioAPIError("unverified", http_status=400, twilio_code=21219)
    client, _ = make_client(err)
    r = client.post("/twilio/calls", json=BODY)
    d = r.json()["detail"]
    assert r.status_code == 422 and d["twilio_code"] == 21219 and "verified" in d["hint"]


def test_twilio_auth_or_outage_is_502(make_client):
    for err in (TwilioAPIError("auth", http_status=401, twilio_code=20003),
                TwilioAPIError("down", http_status=503),
                TwilioAPIError("network")):
        client, _ = make_client(err)
        assert client.post("/twilio/calls", json=BODY).status_code == 502


def test_rate_limit_passthrough(make_client):
    client, _ = make_client(TwilioAPIError("slow down", http_status=429))
    assert client.post("/twilio/calls", json=BODY).status_code == 429
