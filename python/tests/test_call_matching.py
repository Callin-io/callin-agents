"""The call result must never carry another user's transcript (agent shared by many users)."""
from datetime import datetime

from callin.client import Callin

LAUNCH = "2026-10-26T10:00:00Z"
T0 = int(datetime.fromisoformat("2026-10-26T10:00:00+00:00").timestamp())


class FakeCallin(Callin):
    def __init__(self, routes):
        super().__init__(api_key="test", agent_id="agent-1")
        self.routes = routes
        self.seen = []

    def _request(self, method, path, **kw):
        self.seen.append(path)
        value = self.routes.get(path)
        if isinstance(value, Exception):
            raise value
        if value is None:
            from callin.client import CallinError
            raise CallinError("not found", 404)
        return value


def campaign(to="+390111234567"):
    return {"agentId": "agent-1", "status": "completed", "contacts": [{"phoneNumber": to}],
            "metadata": {"createdAt": LAUNCH}}


def conv(cid, number, start, summary):
    return {"conversationId": cid, "direction": "outbound", "startTimeUnix": start,
            "contactNumber": number, "summary": summary, "transcript": summary + " (testo)"}


def test_call_id_is_used_when_present():
    c = FakeCallin({
        "/public/v1/campaigns/c1": campaign(),
        "/public/v1/campaigns/c1/calls": [{"callId": "k1", "status": "completed", "contactNumber": "+390111234567",
                                            "startedAt": LAUNCH}],
        "/public/v1/conversations/k1": conv("k1", "+390111234567", T0, "mia"),
    })
    r = c.get_call_result("c1")
    assert r.match == "call_id" and r.summary == "mia"


def test_other_users_call_after_launch_is_never_returned():
    # Old behaviour took "the first outbound call after the launch": here that is another user's call.
    other = conv("x9", "+34911000000", T0 + 5, "di un altro utente")
    mine = conv("m1", "+39 011 123 4567", T0 + 30, "mia")
    c = FakeCallin({
        "/public/v1/campaigns/c1": campaign(),
        "/public/v1/campaigns/c1/calls": [{"status": "completed", "contactNumber": "+390111234567", "startedAt": LAUNCH}],
        "/public/v1/conversations": [{k: v for k, v in other.items() if k != "contactNumber"},
                                     {k: v for k, v in mine.items() if k != "contactNumber"}],
        "/public/v1/conversations/x9": other,
        "/public/v1/conversations/m1": mine,
    })
    r = c.get_call_result("c1")
    assert r.match == "contact_number" and r.summary == "mia"


def test_no_number_match_returns_no_transcript():
    other = conv("x9", "+34911000000", T0 + 5, "di un altro utente")
    c = FakeCallin({
        "/public/v1/campaigns/c1": campaign(),
        "/public/v1/campaigns/c1/calls": [{"status": "completed", "contactNumber": "+390111234567", "startedAt": LAUNCH}],
        "/public/v1/conversations": [other],
        "/public/v1/conversations/x9": other,
    })
    r = c.get_call_result("c1")
    assert r.finished and r.match is None and r.summary is None and r.transcript is None


def test_two_calls_to_same_number_are_ambiguous():
    # Two users of the same agent calling the same pizzeria in the same minutes.
    a = conv("a1", "+390111234567", T0 + 5, "utente A")
    b = conv("b1", "+390111234567", T0 + 20, "utente B")
    c = FakeCallin({
        "/public/v1/campaigns/c1": campaign(),
        "/public/v1/campaigns/c1/calls": [{"status": "completed", "contactNumber": "+390111234567", "startedAt": LAUNCH}],
        "/public/v1/conversations": [a, b],
        "/public/v1/conversations/a1": a,
        "/public/v1/conversations/b1": b,
    })
    r = c.get_call_result("c1")
    assert r.match is None and r.summary is None


def test_partial_number_is_not_a_match():
    # The old substring check accepted "+3901112345" inside "+39011123456789".
    longer = conv("l1", "+39011123456789", T0 + 5, "numero diverso")
    c = FakeCallin({
        "/public/v1/campaigns/c1": campaign(to="+3901112345"),
        "/public/v1/campaigns/c1/calls": [{"status": "completed", "contactNumber": "+3901112345", "startedAt": LAUNCH}],
        "/public/v1/conversations": [longer],
        "/public/v1/conversations/l1": longer,
    })
    assert c.get_call_result("c1").summary is None
