// Callin.io client for AI agents (Node 18+, no dependencies).
const DEFAULT_BASE_URL = "https://api.callin.io/api";
const FINAL = new Set(["completed", "done", "ended", "failed", "no-answer", "no_answer", "busy", "voicemail", "canceled", "cancelled", "error"]);

export class CallinError extends Error {
  constructor(message, status, details) { super(message); this.status = status; this.details = details; }
}

export class Callin {
  constructor({ apiKey = process.env.CALLIN_API_KEY, agentId = process.env.CALLIN_AGENT_ID, baseUrl = DEFAULT_BASE_URL } = {}) {
    if (!apiKey) throw new CallinError("Missing API key: pass apiKey or set CALLIN_API_KEY");
    this.apiKey = apiKey; this.agentId = agentId; this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async request(method, path, { query, body } = {}) {
    const url = new URL(this.baseUrl + path);
    for (const [k, v] of Object.entries(query || {})) if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    const res = await fetch(url, {
      method,
      headers: { "x-api-key": this.apiKey, "content-type": "application/json", "user-agent": "callin-js/0.1.0" },
      body: body ? JSON.stringify(body) : undefined,
    });
    let data; try { data = await res.json(); } catch { throw new CallinError(`HTTP ${res.status}`, res.status); }
    if (!res.ok || data.success === false) throw new CallinError(data?.error?.message || `HTTP ${res.status}`, res.status, data);
    return data.data ?? data;
  }

  me() { return this.request("GET", "/public/v1/me"); }
  listAgents({ search, pageSize = 20 } = {}) { return this.request("GET", "/public/v1/agents", { query: { search, pageSize } }); }
  listConversations({ agentId, pageSize = 20, startAfterUnix } = {}) {
    return this.request("GET", "/public/v1/conversations", { query: { agentId, pageSize, startAfterUnix } });
  }
  getConversation(id) { return this.request("GET", `/public/v1/conversations/${id}`); }

  /** Place a call: { to: "+39...", objective, context?, language?, agentId?, variables? } → { campaignId, status } */
  async placeCall({ to, objective, context = "", language = "", agentId, contactName = "", variables = {} }) {
    const agent = agentId || this.agentId;
    if (!agent) throw new CallinError("Missing agent: pass agentId or set CALLIN_AGENT_ID");
    if (!to?.startsWith("+")) throw new CallinError("Phone number must be in E.164 format, e.g. +390111234567");
    const contact = { phoneNumber: to, objective, ...variables };
    if (contactName) contact.name = contactName;
    if (context) contact.context = context;
    if (language) contact.language = language;
    const name = `agent-call ${new Date().toISOString()}`;
    const camp = await this.request("POST", "/public/v1/campaigns", { body: { name, agentId: agent, contacts: [contact], launch: true } });
    return { campaignId: camp.campaignId, status: camp.status || "queued", finished: false, to };
  }

  /** Status of a call and, when finished, summary and transcript. */
  async getCallResult(campaignId) {
    const camp = await this.request("GET", `/public/v1/campaigns/${campaignId}`);
    const calls = await this.request("GET", `/public/v1/campaigns/${campaignId}/calls`, { query: { pageSize: 5 } });
    const to = camp.contacts?.[0]?.phoneNumber || "";
    const call = calls?.[0];
    const status = ((call?.status || camp.status || "queued") + "").toLowerCase();
    const out = { campaignId, status, finished: FINAL.has(status), to, callId: call?.callId ?? null, durationSeconds: call?.durationSeconds ?? null };
    if (!out.finished) return out;
    const startedAt = call?.startedAt || camp.metadata?.createdAt;
    const after = startedAt ? Math.floor(Date.parse(startedAt) / 1000) - 120 : undefined;
    let conv = null;
    if (call?.callId) { try { conv = { conversationId: call.callId, ...(await this.getConversation(call.callId)) }; } catch {} }
    if (!conv) {
      const list = await this.listConversations({ agentId: camp.agentId, pageSize: 20, startAfterUnix: after });
      const num = (call?.contactNumber || to).replace(/\s/g, "");
      let m = list.find(c => num && ((c.contactNumber || "").includes(num) || (c.callerNumber || "").includes(num)));
      if (!m && after) m = list.filter(c => (c.direction || "outbound") === "outbound" && (c.startTimeUnix || 0) >= after).sort((a, b) => a.startTimeUnix - b.startTimeUnix)[0];
      if (m) { try { conv = { conversationId: m.conversationId, ...(await this.getConversation(m.conversationId)) }; } catch { conv = m; } }
    }
    if (conv) Object.assign(out, { conversationId: conv.conversationId, summary: conv.summary, transcript: conv.transcript, voicemail: conv.voiceMailDetected, durationSeconds: out.durationSeconds ?? conv.conversationDuration });
    return out;
  }

  async waitForCall(campaignId, { timeoutSeconds = 600, pollSeconds = 10 } = {}) {
    const end = Date.now() + timeoutSeconds * 1000;
    let r = await this.getCallResult(campaignId);
    while (!r.finished && Date.now() < end) { await new Promise(s => setTimeout(s, pollSeconds * 1000)); r = await this.getCallResult(campaignId); }
    return r;
  }
}

export default Callin;
