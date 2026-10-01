# Guide Screenshots

Visual walkthrough of the live code editing flow for partners with Root access.

## Flow: Web → Clear Inject → Root/BYOK → IDE Edit → Remount → Live

### Curated Walkthrough (S6 Live Edit Path)

The numbered screenshots below provide a complete partner sandbox walkthrough:

1. **01-authed-playground-byok.png**  
   Authenticated Web playground on `webrouter-aisdk.exe.xyz` with **Session keys (BYOK)** open/empty and **Harness** available. Host inject cleared; partner brings their own keys.

2. **02-cursor-remote-connected.png**  
   Cursor Remote-SSH connected to `webrouter-aisdk.exe.xyz`, folder `examples/vercel-ai-sdk` (window title shows `[SSH: webrouter-aisdk.exe.xyz]`).

3. **03-ide-file-edit.png**  
   IDE on the Remote folder during the partner edit (explorer shows `PARTNER_TWEAK.md` / `webapp`; one visible UI string change).

4. **04-live-after-remount.png**  
   Live playground after remount/restart; header shows **· S6 partner live**.

See `CAPTIONS.md` for detailed context on each shot.

### Legacy Screenshots

The following earlier screenshots (`s6-*.png`) are retained for reference but superseded by the numbered set:

- `s6-remote-open-proof.png` / `s6-remote-still-open.png` — earlier Remote-SSH connection shots
- `s6-cursor-remote-1.png` — earlier IDE window frame
- `s6-tweak-live-after.png` — earlier live playground after remount

## Usage

Reference the numbered images from documentation with relative paths:

```markdown
![Authenticated playground with BYOK](guide-shots/01-authed-playground-byok.png)
![Remote SSH connection](guide-shots/02-cursor-remote-connected.png)
![IDE file editing](guide-shots/03-ide-file-edit.png)
![Live after remount](guide-shots/04-live-after-remount.png)
```

**Note:** No secrets or key values visible in frames. Share tokens redacted where applicable.
