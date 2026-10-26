// Callin.io client for AI agents (Node 18+, no dependencies).
const DEFAULT_BASE_URL = "https://api.callin.io/api";
/** Seconds before the campaign launch from which a conversation may belong to it. */
const MATCH_WINDOW_BEFORE = 120;
/** Max conversations whose details are fetched when the call id is unknown. */
const MAX_CANDIDATES = 10;
/** Phone number reduced to its digits, for exact comparison. */
const digits = n => (n || "").replace(/\D/g, "");
const FINAL = new Set(["completed", "done", "ended", "failed", "no-answer", "no_answer", "busy", "voicemail", "canceled", "cancelled", "error"]);

/** First sentence of the call per language, sent as the `greeting` variable. */
export const GREETINGS = {
  "it": "Buongiorno, sono un assistente virtuale basato su intelligenza artificiale e chiamo per conto di un cliente. Ha un momento?",
  "es": "Hola, buenos días. Soy un asistente virtual de inteligencia artificial y llamo en nombre de un cliente. ¿Tiene un momento?",
  "pt": "Olá, bom dia. Sou um assistente virtual de inteligência artificial e estou ligando em nome de um cliente. Tem um momento?",
  "en": "Hello, I'm an AI assistant calling on behalf of a customer. Is now a good moment for a quick question?",
  "fr": "Bonjour, je suis un assistant virtuel basé sur l'intelligence artificielle et j'appelle de la part d'un client. Avez-vous un instant ?",
  "de": "Guten Tag, ich bin ein KI-Assistent und rufe im Auftrag eines Kunden an. Haben Sie einen Moment Zeit?",
  "nl": "Goedendag, ik ben een AI-assistent en ik bel namens een klant. Heeft u even een moment?"
};

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
    const greeting = GREETINGS[(language || "").toLowerCase().slice(0, 2)];
    if (greeting && !("greeting" in variables)) contact.greeting = greeting;
    const name = `agent-call ${new Date().toISOString()}`;
    const camp = await this.request("POST", "/public/v1/campaigns", { body: { name, agentId: agent, contacts: [contact], launch: true } });
    return { campaignId: camp.campaignId, status: camp.status || "queued", finished: false, to };
  }

  /**
   * Status of a call and, when finished, summary and transcript.
   * Summary and transcript are attached only when linked to this call with certainty:
   * by call id, or by exactly one outbound conversation of the same agent to the same
   * number after the launch (`match` = "call_id" | "contact_number"). Otherwise they stay
   * empty (`match` = null): an agent shared by several users must never return one
   * user's transcript to another.
   */
  async getCallResult(campaignId) {
    const camp = await this.request("GET", `/public/v1/campaigns/${campaignId}`);
    const calls = await this.request("GET", `/public/v1/campaigns/${campaignId}/calls`, { query: { pageSize: 5 } });
    const call = calls?.[0];
    const to = call?.contactNumber || camp.contacts?.[0]?.phoneNumber || "";
    const status = ((call?.status || camp.status || "queued") + "").toLowerCase();
    const out = { campaignId, status, finished: FINAL.has(status), to, callId: call?.callId ?? null,
      durationSeconds: call?.durationSeconds ?? null, match: null };
    if (!out.finished) return out;
    const found = await this.#findConversation(camp.agentId, call?.callId, to, call?.startedAt || camp.metadata?.createdAt);
    if (found) {
      const [conv, how] = found;
      Object.assign(out, { conversationId: conv.conversationId, summary: conv.summary, transcript: conv.transcript,
        voicemail: conv.voiceMailDetected, durationSeconds: out.durationSeconds ?? conv.conversationDuration, match: how });
    }
    return out;
  }

  async #findConversation(agentId, callId, to, startedAt) {
    if (callId) {
      try { return [{ conversationId: callId, ...(await this.getConversation(callId)) }, "call_id"]; } catch {}
    }
    const target = digits(to);
    const after = startedAt ? Math.floor(Date.parse(startedAt) / 1000) - MATCH_WINDOW_BEFORE : NaN;
    // Without a number, an agent or a start time there is nothing safe to match on.
    if (!target || !agentId || !Number.isFinite(after)) return null;
    const list = await this.listConversations({ agentId, pageSize: 20, startAfterUnix: after });
    const candidates = list.filter(c => (c.direction || "outbound") === "outbound" && (c.startTimeUnix || 0) >= after)
      .slice(0, MAX_CANDIDATES);
    const matches = [];
    for (const c of candidates) {
      let detail;
      try { detail = { conversationId: c.conversationId, ...(await this.getConversation(c.conversationId)) }; } catch { continue; }
      // The list does not carry the number: compare on the detail, digits only, exactly.
      if (digits(detail.contactNumber) === target) matches.push(detail);
    }
    // Two calls of this agent to the same number in the window: ambiguous, return nothing.
    return matches.length === 1 ? [matches[0], "contact_number"] : null;
  }

  /** Waits for the end of the call, then up to `summaryGraceSeconds` more for the summary. */
  async waitForCall(campaignId, { timeoutSeconds = 600, pollSeconds = 10, summaryGraceSeconds = 90 } = {}) {
    const end = Date.now() + timeoutSeconds * 1000;
    const sleep = () => new Promise(s => setTimeout(s, pollSeconds * 1000));
    let r = await this.getCallResult(campaignId);
    while (!r.finished && Date.now() < end) { await sleep(); r = await this.getCallResult(campaignId); }
    const grace = r.finished ? Math.min(end, Date.now() + summaryGraceSeconds * 1000) : 0;
    while (r.finished && r.match === null && r.callId && Date.now() < grace) { await sleep(); r = await this.getCallResult(campaignId); }
    return r;
  }
}

export default Callin;
