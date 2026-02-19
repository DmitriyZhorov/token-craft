# Token-Craft Project Context

**Note:** Global permission policy from `~/.claude/CLAUDE.md` applies to this project.

## Project Overview

**Token-Craft** is a gamified LLM token optimization tool that analyzes Claude Code usage and provides personalized recommendations through space exploration ranks.

- **Language:** Python 3.8+ (standard library only)
- **Type:** CLI tool + Claude Skill
- **Status:** Production ready (v1.1.0)
- **Repository:** https://github.com/DmitriyZhorov/token-analyzer

## Project Structure

```
token-analyzer/
├── token_craft/          # Core package (13 modules)
│   ├── scoring_engine.py
│   ├── rank_system.py
│   ├── pricing_calculator.py
│   └── ...
├── skill_handler.py      # Main entry point (interactive)
├── skill_handler_full.py # Full featured handler
└── tests/                # Unit tests
```

## Python Style
- Follow PEP 8
- Type hints for function signatures
- Docstrings for public methods
- Keep functions under 50 lines
- Use descriptive variable names

## Common Tasks

### Run Token-Craft Analysis
```bash
python skill_handler.py
```

### Run Tests
```bash
python -m pytest tests/
```

## Dependencies

**Core:** Python 3.8+ standard library only
**Optional:** `requests` (for hero.epam.com API integration)

## Data Locations
- **History:** `~/.claude/history.jsonl`
- **Stats:** `~/.claude/stats-cache.json`
- **Profile:** `~/.claude/token-craft/user_profile.json`
- **Snapshots:** `~/.claude/token-craft/snapshots/`

## Version

Current: **v1.1.0** (February 12, 2026)
