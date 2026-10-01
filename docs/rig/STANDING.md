# Rig — Standing expertise (web-search harness)

Living principles for **host/harness** design of LLM agents that use web search (+ optional extract/fetch).  
Scope: system prompts, tool schemas, history, result floors, query formulation, re-search policy.  
**Out of scope:** inventing backend APIs, pricing, or product capabilities.

Citations: see [`research/BIBLIOGRAPHY.md`](research/BIBLIOGRAPHY.md). Internal failure evidence:  
[`2026-09-30-PLAYGROUND-MAX-RESULTS-AND-HISTORY.md`](/workspace/web-router-strategy/plans/2026-09-30-PLAYGROUND-MAX-RESULTS-AND-HISTORY.md),  
[`2026-09-30-MAX-RESULTS-ONE-ORIGIN.md`](/workspace/web-router-strategy/plans/2026-09-30-MAX-RESULTS-ONE-ORIGIN.md).

---

## 1. Core model of the harness

A web-search agent is a **closed loop**:

```
user turn → (history + system) → model → tool call(s) → observations → model → …
```

ReAct ([Yao et al. 2022](https://arxiv.org/abs/2210.03629)) showed that interleaving **thoughts** with **actions** and **observations** reduces hallucination vs chain-of-thought alone, *when* retrieval is informative. WebGPT ([Nakano et al. 2021](https://arxiv.org/abs/2112.09332)) separated **search** from **page browse/quote** and required citations.

**Harness responsibility:** make that loop possible and default to informative retrieval.  
**Model responsibility:** formulate queries, decide when to search vs answer, pick URLs to extract, synthesize with citations.

Do **not** push retrieval-budget knobs (result count, truncation limits) onto the model as free parameters. Anthropic’s tool-design guidance: agents freestyle those knobs poorly; host-side defaults + clear descriptions outperform “schema default and hope” ([Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)).

---

## 2. The three Play / Exe anti-patterns (canonical)

| # | Failure | Root cause | Standing rule |
|---|---------|------------|---------------|
| **A** | Thin SERP (`max_results: 1`) | Model *filled* optional int with `1` despite JSON-schema `default: 5`. Library/Nimble did not coerce to 1. | **Never let the model own result count.** Hide the param; host-pin a floor (default **5**). Schema defaults do not bind when the model emits an explicit value. |
| **B** | Over-compacted queries (`"Quant crypto price"`) | Model minimized query tokens; dropped entities/constraints from the user turn. | **Query formulation is prompt + tool-description work.** Preserve proper nouns, tickers, time cues, and multi-part intent; prefer 1–2 full queries over one telegram. |
| **C** | Follow-up amnesia (“go fetch it yourself”) | Host sent only the latest user message — no prior Q/A or tool context. | **Always send multi-turn history** (`messages[]` with roles). Corrections without history look like cold starts; tools “vanish” from working memory of the topic. |
| **+** | No system prompt | Bare `Agent(tools=…)` | **Ship a short standing system prompt** (re-search on pushback, search→extract, cite URLs). |

Play’s P0 pack (`96ae833` / playground-p0) already addresses A/C/+ by hiding `max_results`, flooring at 5, full history, and a short system prompt. Rig’s [`DEFAULTS.md`](DEFAULTS.md) validates those choices and extends B + history/tool-result policy + extract rules + optional UI.

---

## 3. Principles

### P1 — Host pins budgets; model owns queries
- Model-controlled: `query`, optional `url` for extract, maybe domain hints if you expose them.
- Host-controlled: `max_results` (floor + default), extract preview length, provider selection for demos, max tool rounds (if any).
- Evidence: Anthropic web_search exposes `query` to the model and `max_uses` / filters to the host ([docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool)); Tavily/LangChain default `maxResults: 5` and pin some response-size flags at construction ([docs](https://docs.langchain.com/oss/javascript/integrations/tools/tavily_search)).

### P2 — Result count is a decision-surface width, not a token-savings dial
- Pre-fetch SERP titles/snippets are the evidence the agent uses to **answer**, **re-search**, or **fetch**.
- `max_results: 1` collapses that surface → brittle answers and premature stop (Exe Quant transcript).
- **Floor ≥ 5** for general Q&A / news / price+event questions. Raise to **8–10** for broad research, comparisons, or “what happened / timeline” (MindSearch-style coarse recall then page select — [MindSearch](https://arxiv.org/pdf/2407.20183)).
- Token savings belong in **result text shaping** (short descriptions, extract previews), not in starving hit count. Yogev FRAMES lesson (internal memo): compact *page text*, not `max_results=1`.

### P3 — Multi-turn history is mandatory for search agents
- LangGraph-style agents accumulate user / assistant / tool messages via reducers; follow-ups depend on that state.
- Minimum viable: prior **user + assistant text** turns. Better: also include prior **tool call + tool result** messages for the current session (or a compact summary of URLs/titles already seen).
- Without history, pushback (“before that / initial surge”) cannot trigger grounded re-search — the model correctly feels context-starved and asks the user.

### P4 — Re-search on pushback / weak results (do not offload to the user)
- User challenges, “that’s not what I meant”, empty SERP, or contradictory snippets → **new search and/or extract**, not “please paste a link.”
- ReAct: non-informative search is a major failure mode; recovery requires **reformulation**, not giving up ([Yao et al.](https://arxiv.org/abs/2210.03629) Table 2).
- System prompt steers tool triggering ([Anthropic tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)): light instruction increases search-on-challenge behavior.

### P5 — Query formulation: specificity over compaction
- Self-Ask ([Press et al.](https://arxiv.org/abs/2210.03350)): decompose multi-hop into follow-ups; plug search into sub-questions.
- Keep: entity names, tickers, dates, “before/after”, comparison axes.
- Avoid: dropping half the user sentence into 3–4 tokens; stuffing calendar years into every query unless the user asked for a year (Anthropic observed harmful year-append bias — fix in tool description).
- Multi-part user questions → multiple queries or one clearly compound query — never one underspecified stub.

### P6 — Search vs extract (two tools, two jobs)
| Stage | Tool | When |
|-------|------|------|
| Discover | `web_search` | Need candidates, freshness, “what sources exist” |
| Deepen | `web_extract` / fetch | Snippets lack the fact, timeline, quota, or quote; user named a page; multi-event synthesis |
| Escalate | browser (optional, out of demo default) | Login, heavy JS, forms — not for normal Q&A |

Pattern: search **5+** hits → pick **2–3** URLs → extract. Matches WebGPT browse separation and common production stacks ([search→fetch layering](https://ai-tldr.dev/learn/ai-agents/tool-use/agent-web-search-browsing/); Anthropic [web_fetch](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool) + search).

### P7 — Honest demos, not sleight-of-hand
- Sensible defaults are **visible policy** (prompt + host pin), not hidden provider magic.
- Optional UI may let partners **clear/edit the system prompt**; when cleared, fall back to the built-in default so the demo stays non-naive.
- Do not teach “start with 1 result” as compaction wisdom.

---

## 4. Decision trees

### 4.1 Should the host expose `max_results` to the model?

```
Need partner to tune count live?
  no  → HIDE param; bind floor (5) in tool closure          [preferred for playground]
  yes → keep in schema BUT server-clamp max(n, FLOOR)
        AND description: "omit/raise; never 1 unless user asked for a single link"
Schema default alone without hide/clamp?
  → REJECT (Exe proved models override default with 1)
```

### 4.2 Search vs extract this turn?

```
Have enough titled/snippet evidence to answer with citations?
  yes → answer (cite URLs)
  no, no SERP yet → web_search
  no, SERP weak/empty → reformulate query; web_search again
  no, SERP promising but shallow → web_extract on 2–3 URLs
User named a URL or “open/read this” → web_extract
Timeline / “what started” / multi-event → search then extract several
```

### 4.3 User pushback?

```
Challenge / correction / “not what I meant” / “before that”
  → Do NOT ask user to fetch
  → Re-read history for original intent
  → New web_search (broader or time-shifted query)
  → web_extract on new candidates
  → Answer with updated citations
```

### 4.4 How much history?

```
Playground demo (short sessions):
  → Full user+assistant turns for the session (no arbitrary truncation)
  → Tool cards may be UI-only IF assistant text already cites findings;
     prefer including tool results when context budget allows
Long sessions (uncertain — measure):
  → Keep last N turns full; summarize older tool payloads to URL+title lists
  → Never drop the immediately prior user correction
```

---

## 5. Glossary

| Term | Meaning |
|------|---------|
| **Harness** | Host code: system prompt, tool schemas, message assembly, clamps — not the search provider. |
| **Floor** | Hard minimum `max_results` applied server-side regardless of model intent. |
| **Host-pin** | Parameter bound in the tool closure / factory; absent from model-facing schema. |
| **Decision surface** | Pre-fetch SERP evidence available before answer/fetch/re-search. |
| **Extract** | Fetch URL → cleaned text/markdown for the model (vs SERP snippet). |
| **Pushback** | User challenges answer adequacy or intent match. |
| **Cold start** | Model sees only the latest user message — no prior turns/tools. |
| **Compaction (harmful)** | Over-shortening queries or result counts in ways that destroy recall. |
| **Compaction (benign)** | Truncating extract previews / trimming boilerplate to save tokens. |

---

## 6. Uncertainties (mark clearly)

- **Exact optimal floor (5 vs 8):** 5 matches Tavily/LangChain defaults and Play P0; 8–10 better for open-ended research. **Not rigorously A/B’d on this playground** — treat 5 as demo floor, document raise path.
- **Tool results in history vs text-only:** Full tool messages are more faithful (LangGraph default) but burn tokens. Play P0 uses user+assistant text in the UI history; **extend to tool messages when budget allows** — uncertainty on demo latency/cost tradeoff.
- **Summarization policy for long chats:** No single best recipe; prefer full turns until measured pressure, then summarize *tool payloads* before *user intent*.
- **Model variance:** Same stack sometimes emits `max_results: 5` (host-preset evidence) and sometimes `1` (Quant) — freestyle is stochastic; hiding the param removes the variance class.

---

## 7. Ownership sketch (Router vs Play)

| Concern | Likely owner |
|---------|----------------|
| Playground message assembly, system prompt, hide/floor `max_results` in demo tools | **Play** (host demo) |
| Library `search(max_results=None)` omit-to-provider semantics | **Router / library** (already correct; do not invent cross-provider default of 1) |
| Documenting harness SoT / partner guidance | **Rig** (this tree) + Play README |
| Provider quality / ranking | **Out of Rig scope** |

See also open questions in the handback from [`DEFAULTS.md`](DEFAULTS.md).
