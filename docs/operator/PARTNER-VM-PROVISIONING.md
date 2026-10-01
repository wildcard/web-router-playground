# Operator Notes: Partner VM Provisioning

Internal reference for operators managing partner sandbox access.

> **Audience:** Operators and infrastructure team  
> **Related:** [PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md)

---

## Provisioning Paths

### Shared VM (Current Default)

- VM: `webrouter-aisdk.exe.xyz`
- **Web-only:** Safe with host inject; most partners stay here
- **Root upgrade:** Only after clearing host inject; partner BYOK required
- **Custody lock:** Never grant Root while host keys in process environment

### Dedicated VM (Scale Path)

When multiple partners need concurrent IDE access or isolation is required:

**Clone command:**
```bash
# Shared capacity (uses account vCPU pool)
ssh exe.dev 'cp webrouter-aisdk wr-<partner-slug> --cpu=2 --memory=4GB'

# Standalone (dedicated capacity, metered billing)
ssh exe.dev 'cp webrouter-aisdk wr-<partner-slug> --standalone --cpu=2 --memory=4GB'
```

**Post-clone checklist:**
1. Git sync to latest: `git fetch && git checkout -B main origin/main`
2. **Scrub secrets:** Clear `.env` (all lengths 0), shred `/tmp/wr-inject*`, no host keys in env
3. Start app without keys: `uv run uvicorn webapp.main:app --host 0.0.0.0 --port 8811`
4. Set private: `share set-private wr-<slug>`
5. Grant access: `share add wr-<slug> partner@email.com` (Web first)
6. Root only after key posture safe: `share add wr-<slug> partner@email.com --root`

**Teardown:**
```bash
ssh exe.dev 'rm wr-<slug>'
```

### Cost Reference (2026-10-01)

- **Shared capacity clone:** $0 per VM (contends for account's 2 vCPU pool)
- **Standalone clone:** ~$0.105 per 2 vCPU per hour
- **Example:** 8-hour session ≈ $0.84; 15 concurrent partners × 8h ≈ $12.60

## Key Management Rules

### Pattern A: Partner BYOK (Preferred)
- Partner pastes keys via Session UI or IDE environment
- Safe with Root access
- No host custody concerns

### Pattern B: Host Inject (Web-only)
- Keys in uvicorn process environment
- **Web access only** — never Root
- Time-boxed for demos
- Repo `.env` must remain empty (lengths 0)

### Pattern C: Edge Integrations (Future)
- Exe integrations / HTTP Proxy at `*.int.exe.xyz`
- Secrets held server-side
- Root cannot read via `printenv`
- Requires app wiring changes

## Partner Key Scoping

- **Do not** use personal credentials (e.g., Kobi's OpenAI) for partner infrastructure
- Use platform/team API keys scoped to partner workloads
- Document key owner, scope, rotation plan in operator notes
- Never commit keys to repository

## Access Control Checklist

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Share status | `ssh exe.dev 'share show <vm> --json'` | `"status":"private"` |
| Anonymous gate | `curl -sS -o /dev/null -w '%{http_code}\n' --max-redirs 0 https://<vm>.exe.xyz/` | `307` (login redirect) |
| ACL review | Same `share show` | Web-only or documented Root with clear inject |
| No host inject | `ssh <vm>.exe.xyz 'curl -sS http://127.0.0.1:8811/api/providers'` | Host keys `false` when Root exists |

## Capacity Planning

- **Personal account:** 2 vCPU / 4 GB shared pool
- **15–20 partners on Web:** Manageable on shared VM
- **Multiple concurrent IDE sessions:** Consider standalone clones or upgrade account to 8/16 vCPU
- **Wall-clock clone:** ~1–3 min copy + ~2–5 min bootstrap

## Documentation

Partner-facing flow and custody rules: [PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md)

---

**Security principle:** Web custody lock ensures partners without shell access cannot read host keys. Root access requires cleared environment and partner BYOK.

**Operations principle:** Prefer Web-only for evaluation; provision Root/dedicated VMs on explicit request after security review.
