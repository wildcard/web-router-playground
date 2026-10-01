# Partner Access Playbook

This document describes how partners access the **WebRouter** invite-gated sandbox (`https://webrouter-aisdk.exe.xyz/`), the access levels available, and key security constraints around secret custody.

> **Audience:** Partners evaluating WebRouter integrations.  
> **Status:** Invite-only preview. Not a public playground.

## Related Documentation

- **[PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md)** — Complete access ladder from Web to live code editing, provisioning paths, and visual walkthrough
- **[PARTNER-EMAIL-ADDON.md](PARTNER-EMAIL-ADDON.md)** — Quick start message for new partners
- **[guide-shots/](guide-shots/)** — Screenshots of the live editing workflow

---

## Access Overview

The WebRouter sandbox is hosted on **exe.dev** as a private invite-only VM. Access is granted per partner email after account registration. The sandbox runs the monorepo's [`examples/vercel-ai-sdk/`](../examples/vercel-ai-sdk/) tree with live web search and extract tools.

### Getting access

**Partners receive access via an invite link** that allows registration and Web access in one step.

The typical workflow:
1. Host sends you a registration link (out-of-band via Slack, email, etc.)
2. Open the link and create an exe.dev account or log in with your existing account
3. After registration/login, you'll have Web access to `https://webrouter-aisdk.exe.xyz/`

Alternatively, if you already have an exe.dev account, the host may grant Web access directly to your email address. In that case, simply log into exe.dev with that email and open the sandbox URL.

**Note:** Do not rely on exe.dev system invite emails for access notification. The host will coordinate access grants directly with you.

---

## Access Levels

### Web Access (Browser Playground)

**Web** access grants:
- HTTPS access to the running playground at `https://webrouter-aisdk.exe.xyz/`
- Full chat UI with live web search and extract tools
- System prompt and configuration controls
- **No shell, SSH, or filesystem access**

Web-only partners **cannot** read environment variables or VM files. This is the default and recommended access level for most partners evaluating WebRouter.

### Root / Editor Access (VS Code / SSH)

**Root** access grants:
- Everything in Web access, plus:
- SSH access via `ssh webrouter-aisdk.exe.xyz`
- VS Code Remote-SSH and Cursor Remote-SSH
- Terminal access via browser or IDE
- Full VM filesystem and process access

**Important:** 
- Root access allows reading environment variables and files on the VM, including any secrets in the process environment
- **Root access requires an existing exe.dev account** — you must have Web access first before Root can be granted
- **Root access requires operator provisioning** — see [PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md) for the complete access ladder and live code editing paths

---

## Secret Custody and the Custody Lock

### BYOK (Bring Your Own Keys)

Partners can provide their own API keys in two ways:
- **Session keys UI:** Paste keys into the web interface's "Session keys" panel for process-only injection (recommended)
- **Local `.env`:** When running a local clone, copy `.env.example` to `.env` and add your keys

Keys provided via Session keys or local `.env` are **never** visible to other partners or stored on the hosted VM.

### Host-injected keys (Web-only safe)

The host may inject API keys into the VM process environment to enable demos without requiring partner BYOK. This mode is **safe only when all partners have Web-only access**.

**Host-injected keys are NOT safe with Root access** because Root partners can read process environment variables via shell commands like `printenv` or by inspecting `/proc/<pid>/environ`.

### The Custody Lock Rule

**Root access is never granted while host-injected keys are live in the VM process environment.**

If you need Root/Editor access to modify code, the sequence is:

1. Host clears all injected keys and restarts the application without secrets
2. Host grants Root access (requires your existing exe.dev account)
3. You use **BYOK Session keys** (not host-injected keys)
4. You open VS Code / Cursor via Remote-SSH to `webrouter-aisdk.exe.xyz`
5. You edit code under `/home/exedev/web-router-playground/examples/vercel-ai-sdk`

This sequence ensures no partner with Root access can read host-provided API keys.

**Most partners do not need Root access** — Web access is sufficient for evaluating WebRouter's capabilities.

**Alternative:** For isolated editing or when multiple partners need concurrent IDE access, the operator may provision a **dedicated partner VM**. See [PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md#option-b-dedicated-partner-vm-preferred-at-scale) for details on dedicated VM provisioning.

---

## Private Share Model

The WebRouter sandbox operates under a **private invite-only model**:

- Anonymous visitors receive a **307 login redirect** (not Guest Preview access)
- Only authenticated exe.dev accounts with explicit grants can access the playground
- No public shared API keys
- Typically ~15–20 curated partners

This is **not a public playground**. The monorepo source code is public for reference, but the **running sandbox with live keys** remains invite-gated.

---

## IDE Access (VS Code / Cursor)

For partners with Root access who need to edit code:

### VS Code Remote-SSH

1. Install the [Remote-SSH extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)
2. Open the invite link or use the "Open in VS Code" button from the exe.dev dashboard
3. Alternatively, use the vscode:// URL format: `vscode://vscode-remote/ssh-remote+webrouter-aisdk.exe.xyz/home/exedev`
4. Navigate to `/home/exedev/web-router-playground/examples/vercel-ai-sdk`

### Cursor Remote-SSH

1. Use Remote-SSH in Cursor to connect to `webrouter-aisdk.exe.xyz`
2. Open the folder `/home/exedev/web-router-playground/examples/vercel-ai-sdk`
3. Edit, commit, and push changes as you would in a local environment

### After code changes

The application runs in a tmux session. After editing code:
1. Restart the uvicorn process in the tmux session
2. Refresh your browser to see changes at `https://webrouter-aisdk.exe.xyz/`

See the [vercel-ai-sdk README](../examples/vercel-ai-sdk/README.md) and [`PARTNER_TWEAK.md`](../examples/vercel-ai-sdk/PARTNER_TWEAK.md) for details on modifying the integration.

---

## Configuration and Demos

The sandbox includes harness controls for demonstrations:

- **System prompt editor:** View and modify the agent's system instructions
- **Max results tuning:** Adjust search result limits (default 5, research mode 8–10)
- **Provider selection:** Switch between search providers (auto / nimble / tavily / exa)

These configuration options are available in the web UI. System prompt and max results preferences persist in browser sessionStorage and can be reset to built-in defaults.

---

## Key Principles Summary

1. **Login first:** Create your exe.dev account with the email that will be granted access
2. **Web by default:** Most partners need only Web access for evaluation
3. **Root requires trust:** Root access sees everything on the VM, including environment variables
4. **Custody lock:** Host clears injected keys before granting Root; partners use BYOK
5. **Private only:** Invite-gated access, not a public playground with shared keys
6. **Tools under examples:** Integration code lives at [`examples/vercel-ai-sdk/`](../examples/vercel-ai-sdk/)

---

## Resources

- **[PARTNER-SANDBOX-FLOWS.md](PARTNER-SANDBOX-FLOWS.md)** — Complete access ladder and provisioning paths
- **[PARTNER-EMAIL-ADDON.md](PARTNER-EMAIL-ADDON.md)** — Quick start message
- [Vercel AI SDK integration README](../examples/vercel-ai-sdk/README.md)
- [Partner tweak guide (add tools, configure router)](../examples/vercel-ai-sdk/PARTNER_TWEAK.md)
- [exe.dev Sharing documentation](https://exe.dev/docs/sharing)
- [exe.dev FAQ: VS Code](https://exe.dev/docs/faq/vscode)

For access issues or questions, contact the host who sent your invite.
