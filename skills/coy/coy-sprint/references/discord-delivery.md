# Discord Channel Delivery for Cron Jobs

Cron jobs can deliver output to Discord channels instead of Telegram or local-only.

## Current Channel-Job Mapping (May 5, 2026)

| #channel | Type | Job(s) | Frequency | Purpose |
|---|---|---|---|---|
| `#daily-briefing` | Text | 6 AM Triage, Org refile | Mon-Fri mornings / 8 PM | Work planning & inbox triage |
| `#coach` | Text | Hourly Check-in Coach | Every hour 5 AM–9 PM | Productivity coaching pings |
| `#gbrain` | Text | Nightly git diff → gbrain sync | Daily 2 AM | Knowledge graph sync reports |
| `#rss` | Text | RSS daily scan | Daily 4 AM | Feed scanning (11 feeds, skim-and-go) |
| `#journal` | Forum | End-of-day journal summaries | Daily 8 PM | Daily recap threads by date |

## How to Route a Cron Job to Discord

```bash
cronjob action='update' job_id='<id>' deliver='discord:#channel-name'
```

The `discord:` prefix routes to the Discord delivery adapter. The channel name must exist in the Discord server (use `send_message action='list'` to discover available targets).

## Setting Up New Channels

1. Coy creates the channel in Discord (Hermes cannot create channels)
2. Run `send_message action='list'` to discover the new target
3. Update the cron job's `deliver` parameter
4. Verify with `cronjob action='list'` that `deliver` shows `discord:#channel-name`

### Forum Channels

Forum channels (type 15) may not be auto-discovered by the gateway's periodic refresh even though the adapter supports them natively (`_send_to_forum` auto-creates thread posts). If `send_message action='list'` doesn't show the forum after a gateway restart:

1. Find the guild ID:
   ```bash
   curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
     "https://discord.com/api/v10/users/@me/guilds" | jq '.[] | {id, name}'
   ```

2. Find the forum channel ID:
   ```bash
   curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
     "https://discord.com/api/v10/guilds/<GUILD_ID>/channels" | \
     jq '.[] | select(.name=="journal") | {id, name, type}'
   ```
   Forum channels have type 15.

3. Manually inject into the channel directory:
   ```bash
   python3 -c "
   import json
   with open('/data/.hermes/channel_directory.json') as f:
       data = json.load(f)
   data['platforms']['discord'].insert(0, {
       'id': '<FORUM_CHANNEL_ID>',
       'name': 'journal',
       'guild': '<GUILD_NAME>',
       'type': 'forum'
   })
   with open('/data/.hermes/channel_directory.json', 'w') as f:
       json.dump(data, f, indent=2)
   "
   ```

4. Test: `send_message target='discord:#journal' message='test'`
5. Update the cron: `cronjob action='update' job_id='<id>' deliver='discord:#journal'`

**Pitfall:** The channel directory auto-refreshes every 5 minutes and may overwrite manual entries if the gateway's `guild.forum_channels` still doesn't include the forum. Monitor after refreshing.

## Forum Channels

The Hermes Discord adapter supports forum channels (type 15). When a cron delivers to a forum, the adapter **auto-creates a thread post** with a title derived from the message content (first line or `_derive_forum_thread_name()`). No special config needed — just route with `discord:#forum-name`.

### Setting Up a New Forum for Cron Delivery

1. Coy creates the forum channel in Discord (Hermes cannot create channels)
2. **Restart the gateway** to refresh the channel directory: `hermes gateway restart`
   - New forums do NOT auto-discover — the directory only refreshes on gateway start or manual re-scan
3. Run `send_message action='list'` to verify the forum appears
4. Test with a manual message: `send_message target='discord:#forum-name' message='test'`
5. Update the cron job's `deliver` parameter

### Pitfalls

- **Forum not in channel directory**: If `send_message action='list'` doesn't show the forum, the gateway hasn't discovered it yet. Restart (`hermes gateway restart`). Discovered May 5: `#journal` forum was invisible until restart was proposed.
- **Old threads from text-channel era**: When converting a text channel to a forum, old threads may break (404). The forum is a new channel entity — old thread IDs don't carry over.

## Channel Design Principles

- **Separate by noise level**: High-frequency jobs (hourly coach) get their own channel so Coy can mute them during deep focus
- **Keep low-frequency together**: 6 AM triage and Org refile (2x/day combined) share `#daily-briefing`
- **Tech/system output**: `#gbrain` for sync reports, CI-like output Coy checks occasionally
- **Personal/journal**: `#journal` for end-of-day recaps — low noise, high signal
- **Information intake**: `#rss` for feed scanning (firehose, skim-and-go)

## Text Channel vs Forum Decision Framework

| Type | Best for | Examples |
|---|---|---|
| **Text channel** | Transient firehose, skim-and-go, no need to revisit | `#rss`, `#coach`, `#daily-briefing`, `#gbrain` |
| **Forum** | Self-contained threads worth revisiting, taggable by domain | `#journal` (daily threads by date, tags: #work #spiritual), `#ideas` (one idea per post), `#help-desk` (isolated issues) |

**Key test:** Would Coy ever scroll back to find something from last week? If yes → forum. If it's purely consumption/pings → text channel.

## Migration from Telegram

When migrating a job from Telegram to Discord:
1. Update the cron job's `deliver` parameter
2. The old Telegram delivery stops immediately
3. No cleanup needed on Telegram side
