# Contributing

This repository is the public PersonFu profile hub. Changes should improve signal, automation, developer usefulness, or safe public education.

## Good changes

- Improve profile links, demos, screenshots, or project routing.
- Add small dependency-free tools under `scripts/`.
- Add checks that keep the repo clean and safe.
- Improve docs with concrete project status, setup, or verification notes.
- Keep cybersecurity and RF content lawful, defensive, and public-source framed.

## Avoid

- Root-level planning dumps.
- Badge farming, empty commits, or fake activity.
- Unsupported claims.
- Secrets, tokens, private keys, credentials, personal data, or doxxing.
- Unauthorized-access walkthroughs, malware behavior, stealth, persistence, evasion, or credential theft material.

## Local checks

```bash
python scripts/repo_health.py
pytest -q
python generate_tower_defense.py
```

The README is the profile surface. Keep it polished and avoid broad rewrites unless the change is clearly better.
