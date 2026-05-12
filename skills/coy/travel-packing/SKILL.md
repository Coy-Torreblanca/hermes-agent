---
name: travel-packing
description: Manage Coy's travel packing lists — create, update, and check items for upcoming trips.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [travel, packing, checklist, gbrain]
---

# Travel Packing Lists

Manage Coy's packing lists for upcoming trips. Lists live as gbrain checklist pages, NOT as org files.

## Trigger Conditions

- User says "add X to my packlist" or "add X to my packing list"
- User says "what's on my packing list?" or "check my packlist"
- User mentions packing for a trip
- User says "remind me to pack X"

## Where Packlists Live

**Packlists are gbrain pages (type: `checklist`), not org files.** Do NOT create org files in `/data/syncthing/Sync/org/personal/` for packing — use gbrain.

### Finding a Packlist

1. List recent gbrain pages: `mcp_gbrain_list_pages(limit=50)`
2. Scan for pages with "packing" or "trip" in the slug or title
3. If the user refers to a specific trip, match by destination or date
4. Load the page with `mcp_gbrain_get_page(slug=...)`

Canonical packlist page (also serves as the template for all future trips):
- `mexico-packing-list` — Travel Packing Template (primary; pre-travel checklist)

Other trip-specific pages:
- `trip/may-2026-packing` — May 2026 trip (tech/accessories focused; supplementary)

### Viewing a Packlist

```
mcp_gbrain_get_page(slug="mexico-packing-list")
```

Present items grouped by the existing sections.

### Adding Items

1. Load the full page with `mcp_gbrain_get_page` + `mcp_gbrain_get_chunks` if needed
2. Add the new `- [ ]` item under the appropriate section
3. Write back with `mcp_gbrain_put_page` including the full content (not just a diff)

### Adding a New Section

Add a new `## Section Name` heading above the items, then add items beneath it. Example:

```
## ⚠️ CRITICAL — Do Not Forget
- [ ] Glasses
- [ ] Wallet
- [ ] Passport
```

## Pre-Travel Reminder Workflow

When Coy has a trip coming up (or asks \"remind me what to pack\"):

1. Load the canonical packlist: `mcp_gbrain_get_page(slug=\"mexico-packing-list\")`
2. Walk through each section — **Packing List**, **CRITICAL**, **Devices** — reading items aloud
3. Ask if anything was added since the list was last checked
4. After review, offer to mark items as completed or add new ones

The `mexico-packing-list` page has been templatized: it serves as both a trip-specific checklist AND the base template for all future trips. When a new trip needs a packlist, clone this page's structure.

## Packlist Structure Convention

Coy's packlists have these typical sections:
- **Packing List** — main items (clothing, toiletries, accessories)
- **CRITICAL** — must-not-forget items (glasses, wallet, passport)
- **Devices** — electronics to charge and bring

## Preflight Checklist

A separate gbrain checklist page exists for pre-travel rituals — things to do before leaving, not things to pack. Load it when the user is preparing to depart:

```
mcp_gbrain_get_page(slug="travel/preflight-checklist")
```

Current items include: weigh bag, chargers, wedding ring, charge devices, confirm flight time, Syncthing running, turn up AC, Melody's neck pillow. Lessons learned from past trips are recorded at the bottom of the page.

When the user mentions a travel mistake (overweight bag, forgotten item, missed step), offer to add it to the preflight checklist.

## Pitfalls

- **Don't create org files for packlists.** The canonical home is gbrain. Creating an org file leads to stale duplicates and confusion.
- **Packlist ≠ preflight checklist.** The packlist is "what to bring." The preflight checklist is "what to do before leaving." They live in separate gbrain pages. Don't mix them.
- **Don't rely on search_files or gbrain search alone.** Use `mcp_gbrain_list_pages` to browse page titles — the search index may not always hit checklist-type pages.
- **Google the filesystem before gbrain as a fallback.** The Sync directory and org files won't have packlists. Trust gbrain.
- **Devices section** is where charge reminders and electronics live. The authoritative device list is on the gbrain packlist page itself (Pixel phone, MacBook Pro, overhead headphones) — always read the gbrain page rather than relying on memory or session context.
