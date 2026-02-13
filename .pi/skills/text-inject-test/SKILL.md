---
name: text-inject-test
description: Test CGEvent key injection for text input. Use to verify text injection works and debug typing simulation issues.
---

# Text Inject Test Skill

Test CGEvent key injection for typing text into active applications.

## Setup

```bash
uv add pyobjc-framework-Quartz
```

## Test Basic Text Injection

```bash
python .pi/skills/text-inject-test/scripts/test_inject.py "hello world"
```

## Test Key Codes

```bash
python .pi/skills/text-inject-test/scripts/test_keys.py
```

## Test Streaming

```bash
python .pi/skills/text-inject-test/scripts/test_stream.py
```

## Check Permission

```bash
python .pi/skills/text-inject-test/scripts/check_permission.py
```

## Troubleshooting

- Requires Accessibility permission
- Focus a text field first
- Some apps block synthetic events
