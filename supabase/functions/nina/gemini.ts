// The free way to run Nina: Google's Gemini API (it has a free tier). The browser keeps the conversation in the same shape
// for both providers; this file turns it into Gemini's shape and back. Pure functions + one fetch, so it can be tested.

type Block = Record<string, any>;
type Msg = { role: string; content: Block[] | string };

export const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/";

// Conversation (Anthropic-shaped, kept by the browser) -> Gemini "contents".
export function toGeminiContents(messages: Msg[]): Block[] {
  const names = new Map<string, string>();                       // tool call id -> tool name
  const out: Block[] = [];
  for (const m of messages) {
    const blocks: Block[] = typeof m.content === "string" ? [{ type: "text", text: m.content }] : m.content;
    const parts: Block[] = [];
    for (const b of blocks) {
      if (b.type === "text" && b.text) parts.push({ text: String(b.text) });
      else if (b.type === "tool_use") {
        names.set(b.id, b.name);
        const part: Block = { functionCall: { name: b.name, args: b.input ?? {} } };
        if (b.sig) part.thoughtSignature = b.sig;                // Gemini 3 wants its own note echoed back
        parts.push(part);
      } else if (b.type === "tool_result") {
        const result = typeof b.content === "string" ? b.content : JSON.stringify(b.content);
        parts.push({ functionResponse: { name: names.get(b.tool_use_id) ?? "tool", response: b.is_error ? { error: result } : { result } } });
      }                                                           // search blocks from this server are only for show: dropped
    }
    if (parts.length) out.push({ role: m.role === "assistant" ? "model" : "user", parts });
  }
  return out;
}

// Anthropic-style tool list -> Gemini function declarations (web search is handled by the server, as `web_search`).
export function toGeminiTools(tools: Block[]): Block[] {
  const decls = tools.filter((t) => t.input_schema).map((t) => ({ name: t.name, description: t.description, parameters: t.input_schema }));
  decls.push({
    name: "web_search",
    description: "Search the web for current facts (news, versions, standards, documentation). Returns a summary with sources. Use only when the work needs outside facts.",
    parameters: { type: "object", properties: { query: { type: "string" } }, required: ["query"] },
  });
  return [{ functionDeclarations: decls }];
}

// Gemini answer -> Anthropic-shaped content blocks (what the browser already understands).
export function fromGeminiParts(parts: Block[], newId: () => string): { content: Block[]; calls: Block[] } {
  const content: Block[] = [], calls: Block[] = [];
  for (const p of parts ?? []) {
    if (p.thought) continue;
    if (typeof p.text === "string" && p.text) content.push({ type: "text", text: p.text });
    else if (p.functionCall) {
      const block: Block = { type: "tool_use", id: newId(), name: p.functionCall.name, input: p.functionCall.args ?? {} };
      if (p.thoughtSignature) block.sig = p.thoughtSignature;
      content.push(block); calls.push(block);
    }
  }
  return { content, calls };
}

export class GeminiError extends Error { constructor(public status: number, message: string) { super(message); } }

async function post(key: string, model: string, body: unknown): Promise<Block> {
  const r = await fetch(`${GEMINI_URL}${encodeURIComponent(model)}:generateContent`, {
    method: "POST", headers: { "content-type": "application/json", "x-goog-api-key": key }, body: JSON.stringify(body),
    signal: AbortSignal.timeout(110_000),
  });
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new GeminiError(r.status, data?.error?.message ?? "Gemini had a problem.");
  return data;
}

// A search = one extra call to Gemini with Google Search switched on. Returns the findings and where they came from.
export async function googleSearch(key: string, model: string, query: string): Promise<{ text: string; sources: { title: string; url: string }[] }> {
  const data = await post(key, model, {
    systemInstruction: { parts: [{ text: "Answer the question with verified facts only, from official or primary sources. Say plainly when something could not be confirmed. Be brief." }] },
    contents: [{ role: "user", parts: [{ text: query }] }],
    tools: [{ google_search: {} }],
    generationConfig: { maxOutputTokens: 1200 },
  });
  const cand = data.candidates?.[0];
  const text = (cand?.content?.parts ?? []).map((p: Block) => p.text ?? "").join("").trim();
  const seen = new Set<string>(), sources: { title: string; url: string }[] = [];
  for (const c of cand?.groundingMetadata?.groundingChunks ?? []) {
    const url = c.web?.uri;
    if (url && /^https?:\/\//.test(url) && !seen.has(url)) { seen.add(url); sources.push({ title: String(c.web?.title ?? url), url }); }
  }
  return { text: text || "No result.", sources };
}

// One Nina turn on Gemini. Searches are done here (up to 3); the browser's own tools come back to the browser.
export async function geminiTurn(key: string, model: string, system: string, messages: Msg[], tools: Block[]) {
  const contents = toGeminiContents(messages);
  const extra: Block[] = [];                                      // what the search steps looked like (for the screen)
  let n = 0;
  const newId = () => "g" + Date.now().toString(36) + (n++).toString(36);
  for (let round = 0; round < 4; round++) {
    const data = await post(key, model, {
      systemInstruction: { parts: [{ text: system }] }, contents, tools: toGeminiTools(tools), generationConfig: { maxOutputTokens: 4096 },
    });
    const cand = data.candidates?.[0];
    if (!cand?.content?.parts?.length) {
      const why = data.promptFeedback?.blockReason ?? cand?.finishReason ?? "empty";
      return { content: [...extra, { type: "text", text: "I could not answer that (" + why + ")." }], stop_reason: "end_turn" };
    }
    const { content, calls } = fromGeminiParts(cand.content.parts, newId);
    const searches = calls.filter((c) => c.name === "web_search");
    const mine = calls.filter((c) => c.name !== "web_search");
    if (searches.length && !mine.length && round < 3) {
      contents.push({ role: "model", parts: cand.content.parts });
      const replies: Block[] = [];
      for (let i = 0; i < searches.length; i++) {
        const q = String(searches[i].input?.query ?? "").slice(0, 300);
        let result = "Search failed.";
        try {
          const s = await googleSearch(key, model, q);
          result = s.text + (s.sources.length ? "\nSources:\n" + s.sources.map((x) => "- " + x.title + " " + x.url).join("\n") : "\n(no sources given: treat as unverified)");
          extra.push({ type: "server_tool_use", id: searches[i].id, name: "web_search", input: { query: q } });
          extra.push({ type: "web_search_tool_result", tool_use_id: searches[i].id, content: s.sources.map((x) => ({ type: "web_search_result", title: x.title, url: x.url })) });
        } catch (_) { /* the model is told the search failed */ }
        replies.push({ functionResponse: { name: "web_search", response: { result } } });
      }
      contents.push({ role: "user", parts: replies });
      continue;
    }
    const keep = content.filter((b) => !(b.type === "tool_use" && b.name === "web_search"));
    return { content: [...extra, ...keep], stop_reason: mine.length ? "tool_use" : "end_turn" };
  }
  return { content: [...extra, { type: "text", text: "I searched but could not finish. Ask again." }], stop_reason: "end_turn" };
}
