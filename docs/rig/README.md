# Rig — Harness expertise (vendored)

Research-backed harness guidance for web-search chat agents.

**Source:** Rig (harness expert) — vendored into this repo for stable references.

## Files

- **[`DEFAULTS.md`](DEFAULTS.md)** — Concrete defaults for web_search + web_extract demo harness  
  - §4: Default system prompt (copy-pasteable)
  - §2: `max_results` floor + hide-vs-host-pin policy
  - §1: History policy (full `messages[]`)
  - §7: UI editable vs fixed (never empty system)

- **[`STANDING.md`](STANDING.md)** — Standing principles for host/harness design  
  - P1: Host pins budgets; model owns queries
  - P3: Multi-turn history mandatory
  - P4: Re-search on pushback
  - Canonical anti-patterns (thin SERP, over-compacted queries, follow-up amnesia)

## Usage in playground

`examples/vercel-ai-sdk/` implements these defaults:
- System prompt from DEFAULTS.md §4
- `max_results` hidden from model, floored at 5 (§2)
- Full chat history in `messages[]` (§1)
- Reset → built-in default, never empty system (§7)

**Host/demo configuration only** — not Nimble WebRouter product claims.
