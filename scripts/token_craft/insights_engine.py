"""
Prescriptive Insights Engine

Generates specific, actionable, measurable insights instead of generic advice.
"""

from typing import Dict, List
from datetime import datetime, timedelta


class InsightsEngine:
    """Generate prescriptive insights from waste and usage data."""

    # Threshold triggers for insights
    INSIGHT_TRIGGERS = {
        'repeated_context': {
            'threshold': 1000,  # tokens wasted
            'frequency': 'daily',
            'priority': 'high'
        },
        'verbose_prompts': {
            'threshold': 2.0,  # ratio vs baseline
            'frequency': 'weekly',
            'priority': 'medium'
        },
        'cache_drop': {
            'threshold': -20,  # percentage point drop
            'frequency': 'weekly',
            'priority': 'high'
        },
        'redundant_reads': {
            'threshold': 3,  # same file read count
            'frequency': 'daily',
            'priority': 'low'
        },
        'prompt_bloat': {
            'threshold': 500,  # tokens wasted
            'frequency': 'weekly',
            'priority': 'medium'
        }
    }

    def __init__(self, score_data: Dict, history_data: List[Dict]):
        """
        Initialize insights engine.

        Args:
            score_data: Complete score breakdown with waste data
            history_data: Parsed history.jsonl data
        """
        self.score_data = score_data
        self.history_data = history_data
        self.breakdown = score_data.get("breakdown", {})

    def generate_insights(self) -> List[Dict]:
        """
        Generate all prescriptive insights.

        Returns:
            List of insights sorted by priority
        """
        insights = []

        # Generate insights from each data source
        insights.extend(self._generate_repeated_context_insights())
        insights.extend(self._generate_verbose_prompt_insights())
        insights.extend(self._generate_cache_drop_insights())
        insights.extend(self._generate_redundant_read_insights())
        insights.extend(self._generate_prompt_bloat_insights())
        insights.extend(self._generate_efficiency_pattern_insights())

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda i: priority_order.get(i['priority'], 3))

        return insights

    def _generate_repeated_context_insights(self) -> List[Dict]:
        """Generate insights about repeated context waste."""
        insights = []

        waste_data = self.breakdown.get("waste_awareness", {})
        patterns = waste_data.get("waste_patterns", {})
        repeated_context = patterns.get("repeated_context", {})

        waste_tokens = repeated_context.get("waste_tokens", 0)
        examples = repeated_context.get("examples", [])

        # Check threshold
        if waste_tokens < self.INSIGHT_TRIGGERS['repeated_context']['threshold']:
            return insights

        # Calculate daily savings potential
        days_active = waste_data.get("days_active", 30)
        daily_waste = waste_tokens / days_active if days_active > 0 else 0

        # Extract example snippet
        example_snippet = "project context"
        if examples and len(examples) > 0:
            example_text = examples[0]
            if isinstance(example_text, str):
                # Extract text from format like '"context snippet..." (200 tokens)'
                if '"' in example_text:
                    example_snippet = example_text.split('"')[1].split('...')[0]

        insight = {
            'type': 'repeated_context',
            'priority': 'high',
            'title': 'REPEATED CONTEXT',
            'message': (
                f"You repeated \"{example_snippet}\" multiple times across messages "
                f"→ Wasted {waste_tokens:,} tokens. "
                f"Add this context to CLAUDE.md to save ~{daily_waste:.0f} tokens/day."
            ),
            'waste_tokens': waste_tokens,
            'daily_savings': round(daily_waste, 0),
            'action': f"Add repeated context to CLAUDE.md in your top projects",
            'implementation_time': '10 minutes'
        }

        insights.append(insight)
        return insights

    def _generate_verbose_prompt_insights(self) -> List[Dict]:
        """Generate insights about verbose prompts."""
        insights = []

        waste_data = self.breakdown.get("waste_awareness", {})
        patterns = waste_data.get("waste_patterns", {})
        verbose_prompts = patterns.get("verbose_prompts", {})

        waste_tokens = verbose_prompts.get("waste_tokens", 0)
        examples = verbose_prompts.get("examples", [])

        # Check threshold
        if waste_tokens < 1000:  # Minimum threshold
            return insights

        # Calculate average waste per prompt
        verbose_count = verbose_prompts.get("frequency", 1)
        avg_waste = waste_tokens / verbose_count if verbose_count > 0 else 0

        # Extract example
        verbose_example = "Could you please help me..."
        concise_example = "Edit file.py"
        verbose_tokens = 0
        concise_tokens = 0

        if examples and len(examples) > 0:
            example = examples[0]
            if isinstance(example, dict):
                verbose_example = example.get('verbose', verbose_example)
                verbose_tokens = example.get('actual_tokens', 0)
                concise_tokens = example.get('baseline_tokens', 0)
                concise_example = example.get('concise_version', concise_example)

        insight = {
            'type': 'verbose_prompts',
            'priority': 'medium',
            'title': 'VERBOSE PROMPTS',
            'message': (
                f"Your prompts average {verbose_tokens} tokens vs benchmark {concise_tokens}. "
                f"Example: \"{verbose_example[:50]}...\" ({verbose_tokens} tokens) "
                f"vs \"{concise_example}\" ({concise_tokens} tokens). "
                f"Potential savings: ~{waste_tokens:,} tokens total."
            ),
            'waste_tokens': waste_tokens,
            'daily_savings': round(waste_tokens / 7, 0),  # Weekly pattern
            'action': 'Be more direct: "Edit file.py" vs "Could you please edit file.py"',
            'implementation_time': 'Immediate'
        }

        insights.append(insight)
        return insights

    def _generate_cache_drop_insights(self) -> List[Dict]:
        """Generate insights about cache effectiveness drops."""
        insights = []

        cache_data = self.breakdown.get("cache_effectiveness", {})
        cache_hit_rate = cache_data.get("cache_hit_rate", 0)

        # Detect drops (would need historical data - for now, flag low rates)
        if cache_hit_rate < 30:
            # Low cache usage
            total_regular_input = cache_data.get("total_regular_input", 0)
            potential_savings = int(total_regular_input * 0.6 * 0.9)  # 60% could be cached, 90% savings

            insight = {
                'type': 'cache_drop',
                'priority': 'high',
                'title': 'LOW CACHE USAGE',
                'message': (
                    f"Cache hit rate is {cache_hit_rate:.1f}% (target: 60%+). "
                    f"Cause: Switching projects frequently or short sessions. "
                    f"Solution: Focus on 2-3 projects per day for better caching. "
                    f"Potential recovery: ~{potential_savings:,} tokens."
                ),
                'waste_tokens': potential_savings,
                'daily_savings': potential_savings / 7,
                'action': 'Work on fewer projects per day to maximize cache hits',
                'implementation_time': 'Immediate (workflow change)'
            }

            insights.append(insight)

        return insights

    def _generate_redundant_read_insights(self) -> List[Dict]:
        """Generate insights about redundant file reads."""
        insights = []

        waste_data = self.breakdown.get("waste_awareness", {})
        patterns = waste_data.get("waste_patterns", {})
        redundant_reads = patterns.get("redundant_file_reads", {})

        waste_tokens = redundant_reads.get("waste_tokens", 0)
        total_redundant = redundant_reads.get("frequency", 0)

        # Check threshold
        if total_redundant < 3:
            return insights

        insight = {
            'type': 'redundant_reads',
            'priority': 'low',
            'title': 'REDUNDANT FILE READS',
            'message': (
                f"Pattern detected: You read the same files {total_redundant} times in short windows "
                f"→ Wasted {waste_tokens:,} tokens. "
                f"Better approach: Reference previous reads or use context windows efficiently."
            ),
            'waste_tokens': waste_tokens,
            'daily_savings': waste_tokens / 7,
            'action': 'Reference earlier file reads: "As shown in file.py above..." vs re-reading',
            'implementation_time': 'Immediate'
        }

        insights.append(insight)
        return insights

    def _generate_prompt_bloat_insights(self) -> List[Dict]:
        """Generate insights about prompt bloat."""
        insights = []

        waste_data = self.breakdown.get("waste_awareness", {})
        patterns = waste_data.get("waste_patterns", {})
        prompt_bloat = patterns.get("prompt_bloat", {})

        waste_tokens = prompt_bloat.get("waste_tokens", 0)
        bloat_phrases = prompt_bloat.get("bloat_phrases", {})

        # Check threshold
        if waste_tokens < self.INSIGHT_TRIGGERS['prompt_bloat']['threshold']:
            return insights

        # Get most common bloat phrase
        most_common = "pleasantries"
        if bloat_phrases:
            most_common = list(bloat_phrases.keys())[0]

        insight = {
            'type': 'prompt_bloat',
            'priority': 'medium',
            'title': 'PROMPT BLOAT',
            'message': (
                f"Remove unnecessary pleasantries like '{most_common}'. "
                f"AI doesn't need politeness tokens. "
                f"Wasted {waste_tokens:,} tokens on boilerplate. "
                f"Fix: Be direct and concise."
            ),
            'waste_tokens': waste_tokens,
            'daily_savings': waste_tokens / 7,
            'action': 'Remove "please", "could you", "thank you" from prompts',
            'implementation_time': 'Immediate'
        }

        insights.append(insight)
        return insights

    def _generate_efficiency_pattern_insights(self) -> List[Dict]:
        """Generate insights about efficiency patterns."""
        insights = []

        token_efficiency = self.breakdown.get("token_efficiency", {})
        tier = token_efficiency.get("tier", "average")
        user_avg = token_efficiency.get("user_avg", 0)
        baseline_avg = token_efficiency.get("baseline_avg", 0)

        # Flag if significantly above baseline
        if tier in ["needs_work", "poor"]:
            ratio = token_efficiency.get("ratio", 1.0)
            excess_tokens = user_avg - baseline_avg

            insight = {
                'type': 'efficiency_pattern',
                'priority': 'high',
                'title': 'INEFFICIENCY PATTERN',
                'message': (
                    f"Your sessions average {user_avg:,.0f} tokens vs benchmark {baseline_avg:,.0f} "
                    f"({ratio:.1f}x baseline). "
                    f"Excess: {excess_tokens:,.0f} tokens/session. "
                    f"Review your longest sessions for optimization opportunities."
                ),
                'waste_tokens': int(excess_tokens),
                'daily_savings': int(excess_tokens * 3),  # Assume 3 sessions/day
                'action': 'Break large tasks into smaller, focused sessions (5-15 messages)',
                'implementation_time': 'Immediate (workflow change)'
            }

            insights.append(insight)

        return insights

    def format_insights_section(self, insights: List[Dict]) -> str:
        """
        Format insights into a readable report section.

        Args:
            insights: List of generated insights

        Returns:
            Formatted string for report
        """
        if not insights:
            return ""

        lines = []
        lines.append("⚠️  Optimization Opportunities:")
        lines.append("=" * 70)
        lines.append("")

        for i, insight in enumerate(insights[:5], 1):  # Show top 5
            priority_label = f"({insight['priority'].upper()} Priority)"
            lines.append(f"{i}. {insight['title']} {priority_label}")
            lines.append(f"   {insight['message']}")
            lines.append(f"   Fix: {insight['action']}")
            lines.append(f"   Savings: ~{insight.get('daily_savings', 0):,.0f} tokens/day")
            lines.append(f"   Time: {insight.get('implementation_time', 'Unknown')}")
            lines.append("")

        return "\n".join(lines)
