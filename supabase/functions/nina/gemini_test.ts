import { fromGeminiParts, geminiTurn, toGeminiContents, toGeminiTools } from "./gemini.ts";
const eq = (a: unknown, b: unknown, m: string) => { if (JSON.stringify(a) !== JSON.stringify(b)) { console.error("FAIL", m, JSON.stringify(a), JSON.stringify(b)); Deno.exit(1); } };

const hist = [
  { role: "user", content: [{ type: "text", text: "build" }] },
  { role: "assistant", content: [{ type: "text", text: "ok" }, { type: "tool_use", id: "g1", name: "write_file", input: { name: "a.hum", content: "x" }, sig: "SIG" },
    { type: "server_tool_use", id: "s", name: "web_search", input: { query: "q" } }] },
  { role: "user", content: [{ type: "tool_result", tool_use_id: "g1", content: "Saved", is_error: false }] },
];
const c = toGeminiContents(hist);
eq(c[1].role, "model", "role"); eq(c[1].parts[1].thoughtSignature, "SIG", "sig echoed");
eq(c[2].parts[0].functionResponse, { name: "write_file", response: { result: "Saved" } }, "response paired with name");
eq(c[1].parts.length, 2, "server search blocks dropped");
eq(toGeminiTools([{ name: "t", description: "d", input_schema: { type: "object" } }, { type: "web_search_20250305", name: "web_search" }])[0].functionDeclarations.map((d: any) => d.name), ["t", "web_search"], "tools");
eq(fromGeminiParts([{ text: "hi" }, { functionCall: { name: "x", args: { a: 1 } }, thoughtSignature: "S" }], () => "id1").content[1], { type: "tool_use", id: "id1", name: "x", input: { a: 1 }, sig: "S" }, "from parts");

// a whole turn with a fake Gemini: first asks for a search, then (after the search result) for a browser tool
let call = 0;
globalThis.fetch = (async (_u: string, init: any) => {
  const body = JSON.parse(init.body); call++;
  const reply = (parts: unknown[], extra = {}) => new Response(JSON.stringify({ candidates: [{ content: { role: "model", parts }, ...extra }] }), { status: 200 });
  if (body.tools?.[0]?.google_search) return reply([{ text: "Version 9 is current." }], { groundingMetadata: { groundingChunks: [{ web: { uri: "https://example.org/r", title: "Release notes" } }] } });
  const last = body.contents[body.contents.length - 1];
  if (last.parts[0].functionResponse?.name === "web_search") return reply([{ functionCall: { name: "write_file", args: { name: "a.hum", content: "say 1" } } }]);
  return reply([{ functionCall: { name: "web_search", args: { query: "latest version" } } }]);
}) as any;
const r = await geminiTurn("k", "m", "sys", [{ role: "user", content: "go" }], [{ name: "write_file", description: "w", input_schema: { type: "object" } }]);
eq(r.stop_reason, "tool_use", "stop");
eq(r.content.map((b: any) => b.type), ["server_tool_use", "web_search_tool_result", "tool_use"], "blocks");
eq(r.content[1].content[0].url, "https://example.org/r", "source");
eq(call, 3, "three calls");
console.log("gemini ok");
