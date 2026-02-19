# Token-Craft v3.0

**Gamified LLM token optimization tool** that analyzes Claude Code usage patterns and provides prescriptive insights through space-themed ranks and achievements.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-79%2B%20passing-brightgreen)]()

## Features

### 🎮 Gamification System (v3.0)

- **10 Space Ranks** - Cadet → Galactic Legend (exponential progression)
- **2300+ Points Max** - Up from 1450 in v2.0 (59% harder progression)
- **Difficulty Scaling** - Challenges increase as you advance (up to 43% harder targets for veterans)
- **Streak Multipliers** - 1.0x-1.25x bonus for consecutive improving sessions (+10-50 bonus points)
- **Combo Bonuses** - +25 to +150 pts for excellence across multiple categories
- **25+ Achievements** - Unlock milestones, streaks, combos, exploration, special challenges
- **Time-Based Mechanics**:
  - Recency bonuses (+25% for same-day improvements)
  - Inactivity decay (50% reduction after 31 days)
  - Seasonal resets (fresh competition every 30 days)
- **Regression Detection** - Multi-signal performance analysis with recovery guidance

### 📊 Comprehensive Analysis

- **11 Scoring Categories**:
  - Token Efficiency (250 pts)
  - Optimization Adoption (400 pts)
  - Improvement Trend (125 pts)
  - Cache Effectiveness (75 pts)
  - Waste Awareness (100 pts)
  - Tool Efficiency (75 pts)
  - Cost Efficiency (75 pts)
  - Session Focus (75 pts)
  - Learning Growth (75 pts)
  - Best Practices (50 pts)
  - Plus bonuses (streaks, combos, achievements)

- **Token Waste Detection** - Real patterns: repeated context, verbose prompts, redundant reads
- **Prescriptive Insights** - Concrete savings ("Save 2,400 tokens/day"), not generic advice
- **Historical Tracking** - Snapshots, trends, delta analysis, regression alerts
- **User Profile** - Persistent state tracking rank, achievements, streaks, seasonal data

## Installation

### As a Claude Code Skill

```bash
# Clone repository
git clone https://github.com/DmitriyZhorov/token-craft.git

# Copy to Claude Code skills directory
cp -r token-craft ~/.claude/skills/token-craft
```

Then use in Claude Code:
```
/token-craft
```

### As a Python Package (Standalone)

```bash
# Clone and install
git clone https://github.com/DmitriyZhorov/token-craft.git
cd token-craft
python skill_handler.py
```

## Quick Start

### Run Analysis

```bash
# Interactive menu (default)
python skill_handler.py

# Non-interactive modes
python skill_handler.py --mode quick      # One-line status
python skill_handler.py --mode summary    # Rank and score overview
python skill_handler.py --mode full       # Complete v3.0 report
```

### Output Example

```
======================================================================
          ⚡ TOKEN-CRAFT v3.0 - GAMIFIED OPTIMIZATION REPORT
======================================================================

🚀 RANK: CAPTAIN
   📊 Score: 750 / 2300 pts (32.6%)

----------------------------------------------------------------------
📈 SCORING BREAKDOWN (10 Categories)
----------------------------------------------------------------------
  Token Efficiency........... 180 / 250 (72.0%)
  Optimization Adoption...... 320 / 400 (80.0%)
  Improvement Trend.......... 100 / 125 (80.0%)
  Cache Effectiveness........ 60 / 75 (80.0%)
  ...

----------------------------------------------------------------------
🎁 BONUSES & MULTIPLIERS
----------------------------------------------------------------------
  Streak (Length: 5)
    Multiplier: 1.15x
    Bonus Points: +25

  Combo (Gold)
    Categories: 4 > 80%
    Bonus Points: +100

----------------------------------------------------------------------
🎯 NEWLY UNLOCKED ACHIEVEMENTS
----------------------------------------------------------------------
  ✓ Efficiency Master (+100 pts)
  ✓ Promoted to Captain (+50 pts)

----------------------------------------------------------------------
🚀 NEXT MILESTONE
----------------------------------------------------------------------
  Rank: ⭐ Commander
  Points Needed: 50
======================================================================
```

## Key Systems

### Difficulty Modifier
Progressively tightens targets as users advance:
- **Cadet**: 35,000 tokens/session baseline
- **Captain**: 28,000 tokens/session (-20%)
- **Legend**: 20,000 tokens/session (-43%)

### Streak System
Rewards consistency:
- Session 1: 1.0x (baseline)
- Session 3: 1.10x + 20 pts
- Session 5: 1.20x + 40 pts
- Session 6+: 1.25x + 50 pts (max)

**Breaks** if score doesn't improve vs previous session.

### Achievement Engine
25+ achievements across categories:
- **Progression** (5): Cadet, Navigator, Captain, Admiral, Galactic Legend
- **Excellence** (5): Efficiency Expert, Optimization Master, Cache Champion, etc.
- **Streaks** (3): 5-session, 10-session, 20-session
- **Combos** (3): Well-Rounded, Proficiency, Perfectionist
- **Exploration** (4): 10/50/100/200 sessions
- **Special** (5): Zero Waste Pioneer, Best Practice Champion, etc.

### Regression Detection
Multi-signal analysis combining:
- Efficiency regression (5%+ drop from personal best)
- Score regression (10%+ drop from trend)
- Consecutive decline (3+ declining sessions)

**Severity levels** (none/minor/moderate/severe) with difficulty adjustments and recovery guidance.

## Repository Structure

```
token-craft/
├── token_craft/                    # Core package (25+ modules)
│   ├── scoring_engine.py           # Main scoring with v3.0 logic
│   ├── rank_system.py              # 10-rank progression system
│   ├── difficulty_modifier.py      # Rank-based difficulty scaling
│   ├── streak_system.py            # Streak & combo bonus logic
│   ├── achievement_engine.py       # 25+ achievement system
│   ├── time_based_mechanics.py     # Recency/decay/seasonal
│   ├── regression_detector.py      # Performance regression detection
│   ├── migration_engine.py         # v2.0→v3.0 backwards compatibility
│   ├── user_profile.py             # User state and persistence
│   ├── snapshot_manager.py         # Historical snapshots
│   ├── delta_calculator.py         # Trend analysis
│   └── ... (15+ more modules)
│
├── tests/
│   └── test_scoring.py             # 79+ test methods
│
├── skill_handler.py                # Skill entry point (interactive menu)
├── skill_handler_full.py           # Full-featured handler
├── token-craft.skill               # Packaged skill distribution
│
├── README.md                       # This file
├── SKILL.md                        # Skill documentation
├── LICENSE                         # MIT license
└── .gitignore
```

## Testing

```bash
# Run full test suite
python -m pytest tests/ -v

# Run specific test class
python -m pytest tests/test_scoring.py::TestDifficultyModifier -v

# Run with coverage
python -m pytest tests/ --cov=token_craft --cov-report=html
```

**Test Coverage:**
- 79+ test methods across 12 test classes
- Validates all v3.0 systems (difficulty, streaks, achievements, regression, etc.)
- Tests scoring formulas, rank progression, edge cases

## Data Locations

Token-Craft stores data in `~/.claude/` directory:

```
~/.claude/
├── history.jsonl              # Claude Code usage history (read-only)
├── stats-cache.json           # Session statistics (read-only)
└── token-craft/
    ├── user_profile.json      # User state (rank, achievements, streaks)
    └── snapshots/             # Historical snapshots for trend analysis
        ├── snapshot_2026_02_18_153000.json
        └── ...
```

## Version History

### v3.0 (February 2026)
- **New**: 10-rank exponential progression (vs 7 ranks in v2.0)
- **New**: Difficulty scaling by rank (up to 43% harder)
- **New**: Streak multipliers (1.0x-1.25x) + bonus points
- **New**: Combo bonuses (+25 to +150 pts)
- **New**: 25+ achievement system with unlocks
- **New**: Time-based mechanics (recency, decay, seasonal resets)
- **New**: Regression detection with severity levels
- **New**: Migration engine for v2.0→v3.0 backwards compatibility
- **Removed**: Duplicate self-sufficiency category
- **Removed**: Warm-up bonuses (participation trophies)
- **Impact**: Time to max rank: 3-6 months (vs 5-10 sessions in v2.0)

### v2.0 (Earlier)
- 7 space ranks (Cadet-Legend)
- 1450 points max
- 11 categories with warm-up bonuses

## Requirements

- **Python**: 3.8+
- **Dependencies**: Standard library only (no external packages required)
- **Optional**: `requests` (for hero.epam.com API integration, not required)

## License

MIT License - see [LICENSE](LICENSE)

## Development

### Running Locally

```bash
# Clone and setup
git clone https://github.com/DmitriyZhorov/token-craft.git
cd token-craft

# Interactive analysis
python skill_handler.py

# Run tests
python -m pytest tests/ -v

# Run specific handler
python skill_handler_full.py
```

### Code Structure

- **Python 3.8+** with type hints
- **PEP 8** compliant
- Modular design: each system is independent
- Comprehensive docstrings and tests

### Contributing

Contributions welcome! Areas of interest:

- New achievement types
- Additional regression signals
- UI/output improvements
- Performance optimizations
- Documentation

## Troubleshooting

### No Data

**Problem**: "Empty report" or no history found

**Solution**:
1. Ensure `~/.claude/history.jsonl` exists
2. Verify you have Claude Code usage history
3. Check file permissions: `ls -la ~/.claude/history.jsonl`

### Import Errors

**Problem**: "No module named 'token_craft'"

**Solution**:
1. Verify Python version: `python --version` (need 3.8+)
2. Ensure in correct directory: `cd token-craft`
3. Try: `python -m pytest tests/` to validate setup

### Skill Not Found

**Problem**: "Token-Craft not found" in Claude Code

**Solution**:
1. Clone repository to `~/.claude/skills/token-craft/`
2. Verify structure: `ls ~/.claude/skills/token-craft/skill_handler.py`
3. Restart Claude Code

## Support

- GitHub Issues: [DmitriyZhorov/token-craft/issues](https://github.com/DmitriyZhorov/token-craft/issues)
- Documentation: See [SKILL.md](SKILL.md) for skill usage details

---

**Token-Craft v3.0** — Gamify your token optimization journey! 🚀
