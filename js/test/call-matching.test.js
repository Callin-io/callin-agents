// The call result must never carry another user's transcript (agent shared by many users).
import { test } from "node:test";
import assert from "node:assert/strict";
import { Callin, CallinError } from "../src/index.js";

const LAUNCH = "2026-10-26T10:00:00Z";
const T0 = Date.parse(LAUNCH) / 1000;

class Fake extends Callin {
  constructor(routes) { super({ apiKey: "test", agentId: "agent-1" }); this.routes = routes; }
  async request(method, path) {
    const v = this.routes[path];
    if (v === undefined) throw new CallinError("not found", 404);
    return v;
  }
}
const camp = (to = "+390111234567") => ({ agentId: "agent-1", status: "completed", contacts: [{ phoneNumber: to }], metadata: { createdAt: LAUNCH } });
const conv = (id, number, start, summary) => ({ conversationId: id, direction: "outbound", startTimeUnix: start, contactNumber: number, summary, transcript: summary + " (testo)" });
const listItem = c => { const { contactNumber, ...rest } = c; return rest; };
const calls = (to = "+390111234567", extra = {}) => [{ status: "completed", contactNumber: to, startedAt: LAUNCH, ...extra }];

test("call id is used when present", async () => {
  const r = await new Fake({ "/public/v1/campaigns/c1": camp(), "/public/v1/campaigns/c1/calls": calls(undefined, { callId: "k1" }),
    "/public/v1/conversations/k1": conv("k1", "+390111234567", T0, "mia") }).getCallResult("c1");
  assert.equal(r.match, "call_id"); assert.equal(r.summary, "mia");
});

test("another user's call after the launch is never returned", async () => {
  const other = conv("x9", "+34911000000", T0 + 5, "di un altro utente"), mine = conv("m1", "+39 011 123 4567", T0 + 30, "mia");
  const r = await new Fake({ "/public/v1/campaigns/c1": camp(), "/public/v1/campaigns/c1/calls": calls(),
    "/public/v1/conversations": [listItem(other), listItem(mine)], "/public/v1/conversations/x9": other, "/public/v1/conversations/m1": mine }).getCallResult("c1");
  assert.equal(r.match, "contact_number"); assert.equal(r.summary, "mia");
});

test("no number match returns no transcript", async () => {
  const other = conv("x9", "+34911000000", T0 + 5, "di un altro utente");
  const r = await new Fake({ "/public/v1/campaigns/c1": camp(), "/public/v1/campaigns/c1/calls": calls(),
    "/public/v1/conversations": [listItem(other)], "/public/v1/conversations/x9": other }).getCallResult("c1");
  assert.equal(r.finished, true); assert.equal(r.match, null); assert.equal(r.summary, undefined); assert.equal(r.transcript, undefined);
});

test("two calls to the same number are ambiguous", async () => {
  const a = conv("a1", "+390111234567", T0 + 5, "utente A"), b = conv("b1", "+390111234567", T0 + 20, "utente B");
  const r = await new Fake({ "/public/v1/campaigns/c1": camp(), "/public/v1/campaigns/c1/calls": calls(),
    "/public/v1/conversations": [listItem(a), listItem(b)], "/public/v1/conversations/a1": a, "/public/v1/conversations/b1": b }).getCallResult("c1");
  assert.equal(r.match, null); assert.equal(r.summary, undefined);
});

test("a partial number is not a match", async () => {
  const longer = conv("l1", "+39011123456789", T0 + 5, "numero diverso");
  const r = await new Fake({ "/public/v1/campaigns/c1": camp("+3901112345"), "/public/v1/campaigns/c1/calls": calls("+3901112345"),
    "/public/v1/conversations": [listItem(longer)], "/public/v1/conversations/l1": longer }).getCallResult("c1");
  assert.equal(r.summary, undefined);
});
