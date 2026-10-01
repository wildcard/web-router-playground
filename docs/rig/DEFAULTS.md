# Rig — Sensible default harness (playground-ready)

Concrete defaults for a **web_search + web_extract** chat agent demo.  
Validates and extends Play P0 (`96ae833` / playground-p0 pack): full `messages[]`, hide `max_results` with floor **5**, short re-search system prompt.  
Host/harness only. Principles: [`STANDING.md`](STANDING.md). Sources: [`research/BIBLIOGRAPHY.md`](research/BIBLIOGRAPHY.md).

---

## Checklist map (Router)

| # | Topic | Section |
|---|--------|---------|
| 1 | Default system prompt (search + extract) | §4 |
| 2 | Tool schema floors / hide-vs-host-pin | §2 |
| 3 | History policy | §1 |
| 4 | Re-search-on-pushback | §3 |
| 5 | Query formulation | §5 (also baked into §4) |
| 6 | Extract vs search | §6 |
| 7 | Optional UI: editable vs fixed | §7 |

---

## 1. History policy

### What to send each turn

| Include | Role | Policy |
|---------|------|--------|
| System | `system` | Always prepend **host** system prompt (§4). Ignore client-supplied system turns (Play P0 already does this). |
| User | `user` | All user turns in the session. |
| Assistant | `assistant` | All assistant **text** replies. |
| Tool calls / results | `assistant` tool_calls + `tool` | **Recommended when context allows:** include for the current session so follow-ups see prior SERP/extracts. **Play P0 MVP:** UI stores user+assistant text; tool cards are UI-only — acceptable for short demos *if* assistant text cites URLs; upgrade path is to persist tool messages in `messages[]`. |

### How many turns

- **Playground default:** full session history (no truncation). Sessions are short; amnesia is worse than mild token growth.
- **If you must truncate later:** keep the latest user correction + the prior assistant answer that was challenged; summarize older tool payloads to `{title, url}` lists before dropping user wording.
- **Never:** send only the latest user message (Exe Origin B failure).

### Why

Without history, pushback is a cold start → model asks the user for context instead of re-searching ([STANDING](STANDING.md) P3/P4; ReAct needs observations in context). LangGraph-style agents accumulate messages for this reason.

### Wire shape (conceptual)

```json
{
  "messages": [
    {"role": "user", "content": "…"},
    {"role": "assistant", "content": "…"},
    {"role": "user", "content": "Are you sure? What about the initial surge?"}
  ],
  "provider": "auto"
}
```

Host prepends system. Prefer `messages` over a lone `message` field (Play ChatRequest pattern).

---

## 2. `max_results`: hide from model; host floor + default

### Play P0 (keep)

- Model-facing `web_search(query: str)` — **no** `max_results` arg.
- Closure always calls router with `max_results=5`.
- Tool docstring states the floor and “don’t ask the user to fetch.”

### Recommended numbers

| Knob | Value | Rationale |
|------|-------|-----------|
| **Floor = default (demo)** | **5** | Matches Play P0, Tavily/LangChain default `maxResults: 5`, and product memos (5–8 for news/factual). Enough SERP width for snippet triage without dump. |
| **Broad research / timeline / compare** | **8–10** | Host preset or advanced UI — *not* a model freestyle dial. MindSearch-style recall before page select. |
| **Single-link only** | 1 | Only if **user** explicitly asked for one link/top result — still host policy, not model whim. |
| **Library `WebRouter.search`** | `None` (omit) | Correct library semantics: don’t invent cross-provider defaults. Host tools supply the product number. |

### If schema must expose `max_results` (non-preferred)

```text
Server: n = max(model_n or DEFAULT, FLOOR) with FLOOR=5, DEFAULT=5
Description: "Omit to use 5. Raise for broad research. Use 1 only if the user asked for a single result."
```

Do **not** rely on JSON-schema `"default": 5` alone — Exe proved gpt-4o-mini emits explicit `1` ([origin memo](/workspace/web-router-strategy/plans/2026-09-30-MAX-RESULTS-ONE-ORIGIN.md)).

### Why hide

Anthropic: pagination/size knobs that agents freestyle cause redundant or starved calls; fix by rightsizing host defaults and descriptions ([Writing effective tools](https://www.anthropic.com/engineering/writing-tools-for-agents)). Hosted Anthropic/OpenAI search similarly keeps **budgets** host-side while the model owns the **query**.

---

## 3. Re-search-on-pushback (short text)

### Minimal (≈ Play P0 — keep as kernel)

```text
When the user asks about the live web, prices, news, timelines, or challenges
your answer, call the tools again — do not ask them to go fetch sources.
Prefer web_search then web_extract on 2–3 promising URLs for multi-part or
timeline questions. Keep answers concise and cite URLs.
```

### Extended kernel (drop into system prompt or tool description)

```text
On user pushback (“that’s wrong”, “not what I meant”, “before that”, “look deeper”):
re-search and/or extract with a revised query. Never ask the user to open links
or paste sources. If results are empty or weak, reformulate the query once or
twice (add entities, time window, or split into sub-queries) before answering.
```

---

## 4. Default system prompt (copy-pasteable)

Honest, non-sleight-of-hand. Use as host `SYSTEM_PROMPT` when the UI has not overridden it.

```text
You are a web-research chat agent with two tools: web_search and web_extract.

When to use tools
- Use web_search for live facts: prices, news, events, “what happened”, people/orgs that change, or anything beyond stable textbook knowledge.
- After a useful hit list, use web_extract on 2–3 promising URLs when snippets are too thin for a timeline, quote, number, or multi-part answer.
- If the user challenges your answer or clarifies intent, call the tools again with a better query. Do not ask them to fetch links or paste articles.

How to search (query formulation)
- Preserve the user’s entities, tickers, product names, and time cues (e.g. “before the surge”, dates). Do not over-compact into a 3-word telegram.
- Multi-part questions → one careful compound query or two focused searches covering each part.
- If results are empty or off-topic, reformulate (synonyms, fuller name, time window); do not stop at one weak hit list.

How to answer
- Ground claims in tool results; cite URLs.
- Be concise. If evidence conflicts, say so and cite both sides.
- If tools fail or still lack evidence after re-search, say what you tried — do not invent sources.
```

This extends Play P0’s shorter prompt with explicit query-formulation and weak-result recovery (Self-Ask / ReAct lessons) without claiming provider magic.

---

## 5. Query formulation (harness guidance)

Bake into system prompt (§4) and optionally a one-liner on the tool:

```text
query: Natural-language search string. Keep proper nouns and constraints from
the user message; prefer clarity over minimal tokens.
```

### Anti-patterns → fixes

| Bad | Better |
|-----|--------|
| `Quant crypto price` | `Quant (QNT) cryptocurrency price USD` + separate `Quant QNT cryptocurrency news catalyst` or timeline query |
| Dropping “initial surge” on follow-up | Include prior topic + `initial price surge OR launch rally` using history |
| Appending random years every time | Only add a year when the user or task needs it (Anthropic web-search year-bias lesson) |

---

## 6. Extract vs search

| Situation | Action |
|-----------|--------|
| Need candidates / freshness | `web_search` |
| Snippet enough + URL cite | Answer |
| Need body, timeline, table, quote | `web_extract` on 2–3 URLs from the hit list |
| User pastes or names a URL | `web_extract` |
| Weak/empty SERP | Reformulate → `web_search` again (not extract on junk) |
| Login / JS app / form | Out of default demo scope (browser tier) |

**Default demo tool set:** `web_search` + `web_extract` only (Play). Aligns with WebGPT search-vs-browse and Anthropic search+fetch split.

---

## 7. Optional UI: editable vs fixed

| Element | Demo UI | If user clears / empties |
|---------|---------|---------------------------|
| System prompt | Editable textarea (optional Advanced) | Fall back to built-in §4 default — **do not** run with empty system |
| Provider | Dropdown (auto/nimble/…) | Host/router default |
| `max_results` | **Not shown** as model param; optional Advanced host preset 5 / 8 / 10 | Always ≥ floor 5 |
| History | Client `messages[]` | Required for multi-turn; single-box cold start only for explicit “new chat” |
| Tool schemas | Fixed in code | Partners edit `demo/tools.py` (clone), not freestyle from chat |

**Note for Play:** “Clear system prompt” must mean “reset to built-in default,” not “no instructions,” or you recreate the bare-Agent failure mode.

---

## 8. Tool schema sketch

### `web_search` (model-facing)

```json
{
  "name": "web_search",
  "description": "Search the live web. Always returns several results (host floor of 5). On user pushback or weak results, call again with a revised query; do not ask the user to fetch links. Prefer follow-up web_extract on 2–3 promising URLs for timelines or multi-part questions.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query. Keep entities and constraints from the user; do not over-compact."
      }
    },
    "required": ["query"]
  }
}
```

**Host-pin (not in schema):** `max_results=5` (or 8–10 via host preset).

### `web_extract` (model-facing)

```json
{
  "name": "web_extract",
  "description": "Fetch a URL and return cleaned text/markdown (preview may be truncated). Use after web_search when snippets are insufficient, or when the user names a page.",
  "parameters": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "Absolute http(s) URL to extract."
      }
    },
    "required": ["url"]
  }
}
```

**Host-pin:** extract preview length / truncation (benign compaction). Model should not own raw HTML dumps.

### Pseudo-implementation (matches Play P0)

```python
@ai.tool
async def web_search(query: str) -> dict:
    """Search the web… (see description above)."""
    outcome = await asyncio.to_thread(run_search, router, query, provider, 5)
    return serialize_search(outcome)

@ai.tool
async def web_extract(url: str) -> dict:
    """Extract a URL as markdown…"""
    outcome = await asyncio.to_thread(run_extract, router, url, provider)
    return serialize_extract(outcome)
```

---

## 9. Alignment with Play P0

| Play shipped | Rig stance |
|--------------|------------|
| Full `messages[]` | **Validate** — required (§1) |
| Hide `max_results`; always 5 | **Validate** — preferred (§2); document 8–10 host preset as extension |
| Short re-search system prompt | **Validate** — keep as kernel; **extend** with query formulation + weak-result reformulation (§3–§5) |
| Tool docstring: don’t ask user to fetch | **Validate** |
| Client system turns ignored | **Validate** — host owns default; UI edit → override or reset to built-in (§7) |

No contradiction with Play without rationale: the only extension is stronger prompt text and optional higher host presets, not re-exposing `max_results` to the model.

---

## 10. Open questions (Router vs Play ownership)

1. **Tool-result messages in playground history** — Play owns UI/SSE; should P1 persist tool_call/tool_result into `messages[]`, or keep text-only + UI cards? Rig recommends tool messages when budget allows.
2. **Host preset 5 vs 8** — Play owns demo default (5). Router docs should not set library default to a number (`None` omit stays correct). Who documents the 8–10 “research” preset — Play Advanced UI vs partner README?
3. **Editable system prompt UI** — Play feature; Rig defines fallback-to-built-in behavior when cleared.
4. **Clamping if a partner re-exposes `max_results`** — example code in PARTNER_TWEAK still shows `max_results: int = 5` as a model arg; Play/docs should warn that this recreates Exe failure unless clamped or hidden.
5. **Cross-provider floor** — out of library scope; host-only. Confirm Router messaging stays “hosts pin product defaults.”
