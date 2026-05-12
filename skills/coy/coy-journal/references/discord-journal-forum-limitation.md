# Discord #journal Forum Channel — send_message Limitations

## Problem
The `#journal` channel on the Lab Discord server is a **Forum channel**, not a regular text channel. Forum channels only accept thread creation (via Discord UI or API thread creation endpoint), not regular message posting. `send_message` cannot create new forum threads.

## Targets Tried (all failed)

| Target | Result |
|--------|--------|
| `discord:#journal` | Could not resolve |
| `discord:Lab / #journal` | Could not resolve |
| `discord:Lab / #journal / May 6, 2026` | Could not resolve |
| `discord:#journal /` | Could not resolve |
| `discord:Lab / #journal / hi / topic 1501421147252850789` | 404 Unknown Channel |
| `discord:Lab / #journal / give me an overview of my day? / topic 1501427950556418190` | 404 Unknown Channel |

## Workaround
1. Post journal template/summary to `discord:#general` (resolves reliably)
2. Instruct Coy to copy it into a new #journal forum post manually
3. Once a thread exists with a discoverable topic ID, future updates can target it

## Session Reference
- Date: May 6, 2026
- Session: 20260506_025808_3cdaec97 (partial context)
