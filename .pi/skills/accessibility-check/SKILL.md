---
name: accessibility-check
description: Check and request macOS Accessibility permission required for CGEvent key injection. Use before testing text injection.
---

# Accessibility Check Skill

Verify and request macOS Accessibility permission.

## Check Status

```bash
python .pi/skills/accessibility-check/scripts/check.py
```

## Why It's Needed

espin uses CGEvent to inject keystrokes into the active application. This requires Accessibility permission.

## Grant Permission

1. Open: System Settings → Privacy & Security → Accessibility
2. Click "+" and add your terminal app (Terminal.app, iTerm2, etc.)
3. Or run: open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
4. Restart your terminal/IDE

## Apps That Need Permission

- Terminal.app
- iTerm2
- WezTerm
- VS Code
- Cursor
- Any app you run espin from

## Troubleshooting

**Still not working after granting:**
- Restart the app completely (Cmd+Q, then reopen)
- Check if the permission toggle is ON (not just added)
- Some apps need to be re-added after updates
