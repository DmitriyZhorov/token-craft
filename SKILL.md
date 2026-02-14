---
name: token-craft
description: "Gamified LLM token optimization tool that analyzes Claude Code usage patterns. Detects real token waste (repeated context, verbose prompts, redundant reads), calculates scores across 11 categories (1450 points max), provides space-themed ranks from Cadet to Galactic Legend, and gives prescriptive insights with concrete token savings. Includes A/B testing, ROI measurement, and pattern validation. Use when users ask to check token optimization score, find token waste, see their rank, get recommendations to reduce token usage, or invoke /token-craft."
---

# Token-Craft v2.0

Gamified LLM token optimization tool with real waste detection, A/B testing, and prescriptive insights.

## What It Does

1. **Waste Detection** - Finds repeated context, verbose prompts, redundant reads, prompt bloat
2. **11-Category Scoring** - Token efficiency, optimization adoption, self-sufficiency, improvement trend, best practices, cache effectiveness, tool efficiency, session focus, cost efficiency, learning growth, waste awareness (1450 pts max)
3. **Space Ranks** - Cadet through Galactic Legend based on score
4. **Prescriptive Insights** - Concrete savings ("Save 2,400 tokens/day") not generic advice
5. **A/B Testing** - Compares approaches, proves which methods work
6. **ROI Measurement** - Tracks recommendations from generation to implementation to actual savings
7. **Pattern Library** - Validates patterns with success rates and evidence

## Execution

```bash
# Locate Token-Craft scripts
SKILL_DIR="$HOME/.claude/skills/token-craft/scripts"

if [ ! -f "$SKILL_DIR/run_analysis.py" ]; then
  echo "Token-Craft not found. Install:"
  echo "  git clone https://github.com/DmitriyZhorov/token-craft.git"
  echo "  cp -r token-craft/scripts ~/.claude/skills/token-craft/scripts"
  exit 1
fi

cd "$SKILL_DIR"

# Parse arguments (default: full)
MODE="${ARGUMENTS:-full}"
case "$MODE" in
  quick|status|one-line) MODE="quick" ;;
  summary|overview)      MODE="summary" ;;
  full|detailed|complete|*) MODE="full" ;;
esac

python run_analysis.py "$MODE"
```

## Arguments

| Argument | Aliases | Output |
|----------|---------|--------|
| `full` | `detailed`, `complete` | Complete report with waste detection + insights (default) |
| `summary` | `overview` | Rank and score overview |
| `quick` | `status`, `one-line` | One-line status |

## Argument Selection

- "waste", "optimization", "savings" - use `full`
- "what's my rank?", "quick status" - use `quick`
- "give me a summary" - use `summary`
- No args / just `/token-craft` - default to `full`

## Output Format

```
Current Rank: [ICON] [RANK] (score/1450)
Next Rank: [NAME] in X points

Score Breakdown (11 categories):
  Token Efficiency:      XXX/300
  Optimization Adoption: XXX/325
  ...
  Waste Awareness:       XXX/100

Token Waste Analysis:
  Total waste: X,XXX tokens
  Daily rate: ~XXX tokens/day
  Patterns: repeated context, verbose prompts, ...

Top Recommendations:
  1. [Action] - Save ~XXX tokens/day
  ...
```

## Presenting Results

After running and getting output:

1. Acknowledge rank and score
2. Highlight waste patterns (if detected)
3. Show concrete savings numbers
4. Recommend ONE specific next action with implementation time
5. Show historical ROI if available

**With waste detected:**
```
You're a [RANK] with [SCORE] points.

I found actual waste in your usage:
- Repeated context: X,XXX tokens wasted
- Verbose prompts: X,XXX tokens wasted

Biggest opportunity: [PATTERN]
  Fix: [ACTION] (takes [TIME])
  Savings: ~XXX tokens/day
```

**No waste detected:**
```
You're a [RANK] with [SCORE] points.
Strengths: [HIGH CATEGORIES]
Top opportunity: [LOWEST CATEGORY] - [ACTION] could add [PTS] points.
```

## Ranks (v2.0 thresholds)

| Range | Rank | Icon |
|-------|------|------|
| 0-269 | Cadet | graduation cap |
| 270-539 | Pilot | airplane |
| 540-809 | Navigator | compass |
| 810-1079 | Commander | star |
| 1080-1349 | Captain | pilot |
| 1350-1619 | Admiral | medal |
| 1620+ | Galactic Legend | galaxy |

## Data Sources

- History: `~/.claude/history.jsonl`
- Stats: `~/.claude/stats-cache.json`
- Profile: `~/.claude/token-craft/user_profile.json`
- Snapshots: `~/.claude/token-craft/snapshots/`

## Requirements

- Python 3.8+ (standard library only, no external packages)
- Read access to `~/.claude/history.jsonl`

## Troubleshooting

1. **"Token-Craft not found"** - Clone repo and copy scripts to `~/.claude/skills/token-craft/scripts/`
2. **Import errors** - Ensure Python 3.8+ (`python --version`)
3. **Empty report** - Check `~/.claude/history.jsonl` exists and has data
