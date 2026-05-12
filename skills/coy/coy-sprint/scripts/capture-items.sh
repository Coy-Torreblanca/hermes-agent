#!/bin/bash
# Coy's capture items from May 9, 2026 — run once

# Add 3 todos to inbox.org
cat >> /data/syncthing/Sync/org/inbox.org << 'ORGDONE'

** TODO Migrate Apple Reminders to personal AI
Move all Apple Reminders into the Hermes personal assistant system so reminders
live in one place and are accessible to the agent.

** TODO Sprint planning — align personal AI epic to requirement file
Sprint has accumulated items across the trip. Need sprint planning session:
align the personal AI EPIC with the requirements/spec file created during
the May 8 flight. Review what's in the sprint, prune/consolidate, ensure
everything traces to the spec.

** TODO Send Gunnar my Discord information
ORGDONE

echo "✅ 3 todos appended to inbox.org"