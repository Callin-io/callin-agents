export class CallinError extends Error { status?: number; details?: unknown; }
export interface CallResult { campaignId: string; status: string; finished: boolean; to: string; callId?: string | null; conversationId?: string; durationSeconds?: number | null; summary?: string; transcript?: string; voicemail?: boolean; /** "call_id" or "contact_number" when summary and transcript are linked with certainty; null otherwise. */ match?: "call_id" | "contact_number" | null; }
export class Callin {
  constructor(opts?: { apiKey?: string; agentId?: string; baseUrl?: string });
  me(): Promise<{ userId: string; email: string }>;
  listAgents(opts?: { search?: string; pageSize?: number }): Promise<any[]>;
  listConversations(opts?: { agentId?: string; pageSize?: number; startAfterUnix?: number }): Promise<any[]>;
  getConversation(id: string): Promise<any>;
  placeCall(opts: { to: string; objective: string; context?: string; language?: string; agentId?: string; contactName?: string; variables?: Record<string, unknown> }): Promise<CallResult>;
  getCallResult(campaignId: string): Promise<CallResult>;
  waitForCall(campaignId: string, opts?: { timeoutSeconds?: number; pollSeconds?: number; summaryGraceSeconds?: number }): Promise<CallResult>;
}
export default Callin;
