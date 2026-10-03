# Partner 30s experience (invite sandbox)

**URL:** `https://webrouter-aisdk.exe.xyz/` (private / invite-only)

## How this works

**This is an invite-only preview** of WebRouter search and extract, used as tools inside the Vercel AI SDK for Python. Not a public package launch.

**Click a starter, or type your own.** You will see `web_search` and `web_extract` cards, and which provider served them.

**Chips turn green** when a key is already on this session. If they are not, you are still in the right place. **Session keys** is a paste for this visit only. This preview does not ship with a shared key.

**The open-source example is this same app.** A 30-second walkthrough is in the repo. You do not need the repo to try this page.

---

## Walkthrough

1. **Land** — Dark chat UI titled **WebRouter × Vercel AI SDK (Python)**. Tagline makes clear: live **search + extract** via WebRouter typed web-context (`@ai.tool` / `build_tools(WebRouter())`). Not a blank shell.
2. **Keys** — Provider chips (nimble / tavily / exa / openai) show green when ready. Host-injected Nimble session env (mode b) or partner **Session keys** paste / `.env` BYOK (mode a). Warn hint if anything required is missing.
3. **Try** — Click a starter (Search + extract / Web search / URL extract) or type your own. Example: *"Search for retrieval-augmented generation, then extract the top Wikipedia result and summarize in two sentences."*
4. **See tools** — Streaming cards for `web_search` / `web_extract`; each finishes with **served by \<provider\>**. That is live web-context through WebRouter on the Vercel AI SDK host.
5. **Optional** — Switch provider dropdown (auto / nimble / tavily / exa) and send again.

Claim-safe close: Layer-1 typed web-context; search + extract only; preview / invite-gated; vendored wheel — not a public PyPI launch.
