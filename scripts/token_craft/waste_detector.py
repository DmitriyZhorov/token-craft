"""
Waste Detection Engine

Detects real token waste patterns through message content analysis.
Replaces keyword-based heuristics with actual pattern detection.
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import re


class WasteDetector:
    """Detect token waste patterns in conversation history."""

    # Token estimation: ~4 chars per token
    CHARS_PER_TOKEN = 4

    # Bloat phrases to detect
    BLOAT_PHRASES = [
        "please", "could you", "would you", "i would like",
        "if possible", "if you don't mind", "when you get a chance",
        "thank you", "thanks", "appreciate it", "much appreciated"
    ]

    # Task classification keywords
    SIMPLE_TASK_KEYWORDS = [
        "read", "show", "list", "ls", "cat", "view", "get",
        "display", "print", "find", "search"
    ]

    MEDIUM_TASK_KEYWORDS = [
        "edit", "modify", "change", "update", "refactor",
        "fix", "add", "remove", "replace"
    ]

    COMPLEX_TASK_KEYWORDS = [
        "design", "implement", "create", "build", "debug",
        "analyze", "explain", "architect", "plan"
    ]

    def __init__(self, history_data: List[Dict]):
        """
        Initialize waste detector.

        Args:
            history_data: Parsed history.jsonl data
        """
        self.history_data = history_data
        self.sessions = self._group_by_sessions()

    def _group_by_sessions(self) -> List[Dict]:
        """Group history data by session."""
        sessions = {}

        for entry in self.history_data:
            session_id = entry.get("sessionId", "unknown")

            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "messages": [],
                    "project": entry.get("project", "unknown"),
                    "timestamp": entry.get("timestamp")
                }

            sessions[session_id]["messages"].append(entry)

        return list(sessions.values())

    def detect_all_waste(self) -> Dict:
        """
        Run all waste detection algorithms.

        Returns:
            {
                'total_waste_tokens': int,
                'patterns': [
                    {
                        'type': str,
                        'estimated_waste': int,
                        'frequency': int,
                        'examples': List[str],
                        'recommendation': str
                    },
                    ...
                ]
            }
        """
        patterns = []

        # Run all detectors
        repeated_context = self.detect_repeated_context()
        if repeated_context['estimated_waste'] > 0:
            patterns.append(repeated_context)

        verbose_prompts = self.detect_verbose_prompts()
        if verbose_prompts['estimated_waste'] > 0:
            patterns.append(verbose_prompts)

        redundant_reads = self.detect_redundant_file_reads()
        if redundant_reads['estimated_waste'] > 0:
            patterns.append(redundant_reads)

        prompt_bloat = self.detect_prompt_bloat()
        if prompt_bloat['estimated_waste'] > 0:
            patterns.append(prompt_bloat)

        total_waste = sum(p['estimated_waste'] for p in patterns)

        return {
            'total_waste_tokens': total_waste,
            'patterns': patterns
        }

    def detect_repeated_context(self) -> Dict:
        """
        Detect repeated context across consecutive messages in sessions.

        Returns:
            {
                'type': 'repeated_context',
                'estimated_waste': int,
                'frequency': int,
                'examples': List[str],
                'sessions_affected': List[str],
                'recommendation': str
            }
        """
        total_waste = 0
        examples = []
        affected_sessions = []
        repetition_count = 0

        for session in self.sessions:
            messages = session.get("messages", [])
            if len(messages) < 2:
                continue

            # Extract user messages only
            user_messages = [
                msg for msg in messages
                if msg.get("type") == "say"
            ]

            if len(user_messages) < 2:
                continue

            # Compare consecutive messages
            for i in range(len(user_messages) - 1):
                msg1 = user_messages[i].get("text", "")
                msg2 = user_messages[i + 1].get("text", "")

                if not msg1 or not msg2:
                    continue

                # Extract n-grams and find overlap
                ngrams1 = self._extract_ngrams(msg1, n=4)
                ngrams2 = self._extract_ngrams(msg2, n=4)

                overlap = ngrams1 & ngrams2

                if overlap:
                    # Calculate overlap characters
                    overlap_chars = sum(len(' '.join(gram)) for gram in overlap)

                    # Check if significant overlap (>100 chars and >30% of shorter message)
                    min_length = min(len(msg1), len(msg2))
                    if overlap_chars > 100 and overlap_chars / min_length > 0.3:
                        waste_tokens = overlap_chars // self.CHARS_PER_TOKEN
                        total_waste += waste_tokens
                        repetition_count += 1

                        if len(examples) < 3:
                            # Get first repeated phrase as example
                            example_phrase = ' '.join(list(overlap)[0])
                            examples.append(f"\"{example_phrase[:60]}...\" ({waste_tokens} tokens)")

                        if session["session_id"] not in affected_sessions:
                            affected_sessions.append(session["session_id"])

        recommendation = ""
        if total_waste > 0:
            recommendation = (
                f"Add repeated context to CLAUDE.md or project documentation. "
                f"Save ~{total_waste // len(affected_sessions) if affected_sessions else 0} tokens/session."
            )

        return {
            'type': 'repeated_context',
            'estimated_waste': total_waste,
            'frequency': repetition_count,
            'examples': examples[:3],
            'sessions_affected': affected_sessions,
            'recommendation': recommendation
        }

    def _extract_ngrams(self, text: str, n: int = 4) -> Set[Tuple[str, ...]]:
        """
        Extract n-grams from text.

        Args:
            text: Input text
            n: N-gram size (default 4 words)

        Returns:
            Set of n-gram tuples
        """
        # Normalize: lowercase, remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        # Extract n-grams
        ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i:i+n])
            ngrams.add(ngram)

        return ngrams

    def detect_verbose_prompts(self) -> Dict:
        """
        Detect unnecessarily verbose prompts compared to task complexity.

        Returns:
            {
                'type': 'verbose_prompts',
                'estimated_waste': int,
                'verbose_count': int,
                'avg_length': int,
                'baseline_length': int,
                'examples': List[Tuple[str, int, int]],
                'recommendation': str
            }
        """
        total_waste = 0
        verbose_count = 0
        examples = []
        all_lengths = []

        for session in self.sessions:
            messages = session.get("messages", [])

            user_messages = [
                msg for msg in messages
                if msg.get("type") == "say"
            ]

            for msg in user_messages:
                text = msg.get("text", "")
                if not text:
                    continue

                # Classify task complexity
                task_type = self._classify_task_type(text)
                baseline = self._get_baseline_length(task_type)

                actual_length = len(text)
                all_lengths.append(actual_length)

                # Flag if >2x baseline
                if actual_length > baseline * 2:
                    waste_chars = actual_length - baseline
                    waste_tokens = waste_chars // self.CHARS_PER_TOKEN
                    total_waste += waste_tokens
                    verbose_count += 1

                    if len(examples) < 3:
                        concise_version = self._suggest_concise_version(text, task_type)
                        examples.append({
                            'verbose': f"{text[:80]}..." if len(text) > 80 else text,
                            'actual_tokens': actual_length // self.CHARS_PER_TOKEN,
                            'baseline_tokens': baseline // self.CHARS_PER_TOKEN,
                            'waste_tokens': waste_tokens,
                            'concise_version': concise_version
                        })

        avg_length = sum(all_lengths) // len(all_lengths) if all_lengths else 0

        recommendation = ""
        if total_waste > 0:
            recommendation = (
                f"Use more concise prompts. Be direct: 'Edit file.py' vs "
                f"'Could you please help me edit file.py'. "
                f"Potential savings: {total_waste // verbose_count if verbose_count else 0} tokens/prompt."
            )

        return {
            'type': 'verbose_prompts',
            'estimated_waste': total_waste,
            'verbose_count': verbose_count,
            'avg_length': avg_length,
            'baseline_length': 150,  # Overall average baseline
            'examples': examples[:3],
            'recommendation': recommendation
        }

    def _classify_task_type(self, text: str) -> str:
        """
        Classify task complexity based on keywords.

        Returns:
            'simple', 'medium', or 'complex'
        """
        text_lower = text.lower()

        # Check for complex task keywords first
        for keyword in self.COMPLEX_TASK_KEYWORDS:
            if keyword in text_lower:
                return 'complex'

        # Check for medium task keywords
        for keyword in self.MEDIUM_TASK_KEYWORDS:
            if keyword in text_lower:
                return 'medium'

        # Check for simple task keywords
        for keyword in self.SIMPLE_TASK_KEYWORDS:
            if keyword in text_lower:
                return 'simple'

        # Default to medium if unclear
        return 'medium'

    def _get_baseline_length(self, task_type: str) -> int:
        """Get baseline character length for task type."""
        baselines = {
            'simple': 50,
            'medium': 150,
            'complex': 300
        }
        return baselines.get(task_type, 150)

    def _suggest_concise_version(self, text: str, task_type: str) -> str:
        """Suggest a more concise version of the prompt."""
        # Remove common bloat phrases
        concise = text
        for phrase in ["could you please", "would you please", "i would like to",
                       "can you help me", "if possible", "when you get a chance"]:
            concise = re.sub(rf'\b{phrase}\b', '', concise, flags=re.IGNORECASE)

        # Trim whitespace
        concise = ' '.join(concise.split())

        # For simple tasks, extract the core command
        if task_type == 'simple':
            # Try to find the main action and target
            match = re.search(r'\b(read|show|list|find|cat|view)\s+([^\n\.]+)', concise, re.IGNORECASE)
            if match:
                concise = f"{match.group(1).capitalize()} {match.group(2).strip()}"

        return concise[:80] if len(concise) > 80 else concise

    def detect_redundant_file_reads(self) -> Dict:
        """
        Detect reading same file multiple times within short windows.

        Returns:
            {
                'type': 'redundant_file_reads',
                'estimated_waste': int,
                'files_affected': Dict[str, int],
                'total_redundant_reads': int,
                'recommendation': str
            }
        """
        # Track file reads with timestamps
        file_reads = defaultdict(list)  # file_path -> [(timestamp, estimated_size)]

        for entry in self.history_data:
            # Check for Read tool calls
            tool_calls = entry.get("toolCalls", [])
            if not tool_calls:
                continue

            timestamp_str = entry.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                continue

            for tool_call in tool_calls:
                if tool_call.get("name") == "Read":
                    params = tool_call.get("parameters", {})
                    file_path = params.get("file_path", "")

                    if file_path:
                        # Estimate file size (assume average 2000 tokens for read files)
                        estimated_tokens = 2000
                        file_reads[file_path].append((timestamp, estimated_tokens))

        # Find redundant reads (same file read >3 times within 1 hour)
        total_waste = 0
        files_affected = {}
        total_redundant = 0

        for file_path, reads in file_reads.items():
            if len(reads) < 2:
                continue

            # Sort by timestamp
            reads.sort(key=lambda x: x[0])

            # Check for reads within 1-hour windows
            redundant_count = 0
            for i in range(len(reads) - 1):
                for j in range(i + 1, len(reads)):
                    time_diff = reads[j][0] - reads[i][0]
                    if time_diff <= timedelta(hours=1):
                        redundant_count += 1
                        total_waste += reads[j][1]  # Waste is the re-read tokens

            if redundant_count >= 2:  # At least 3 total reads (2 redundant)
                files_affected[file_path] = redundant_count + 1
                total_redundant += redundant_count

        recommendation = ""
        if total_waste > 0:
            recommendation = (
                f"Cache file contents or reference previous reads. "
                f"Affected {len(files_affected)} files. "
                f"Consider using context windows more efficiently."
            )

        return {
            'type': 'redundant_file_reads',
            'estimated_waste': total_waste,
            'files_affected': dict(list(files_affected.items())[:5]),  # Top 5
            'total_redundant_reads': total_redundant,
            'recommendation': recommendation
        }

    def detect_prompt_bloat(self) -> Dict:
        """
        Detect boilerplate phrases and unnecessary pleasantries.

        Returns:
            {
                'type': 'prompt_bloat',
                'estimated_waste': int,
                'bloat_phrases': Dict[str, int],
                'avg_bloat_percentage': float,
                'recommendation': str
            }
        """
        total_waste = 0
        bloat_phrase_counts = defaultdict(int)
        bloat_percentages = []

        for session in self.sessions:
            messages = session.get("messages", [])

            user_messages = [
                msg for msg in messages
                if msg.get("type") == "say"
            ]

            for msg in user_messages:
                text = msg.get("text", "")
                if not text or len(text) < 20:
                    continue

                text_lower = text.lower()
                bloat_chars = 0

                # Count bloat phrases
                for phrase in self.BLOAT_PHRASES:
                    pattern = r'\b' + re.escape(phrase) + r'\b'
                    matches = re.findall(pattern, text_lower)
                    if matches:
                        bloat_phrase_counts[phrase] += len(matches)
                        bloat_chars += len(phrase) * len(matches)

                # Calculate bloat percentage
                if len(text) > 0:
                    bloat_pct = (bloat_chars / len(text)) * 100
                    bloat_percentages.append(bloat_pct)

                    # Flag if bloat >20% of message
                    if bloat_pct > 20:
                        waste_tokens = bloat_chars // self.CHARS_PER_TOKEN
                        total_waste += waste_tokens

        avg_bloat_pct = sum(bloat_percentages) / len(bloat_percentages) if bloat_percentages else 0

        # Get top bloat phrases
        top_bloat = dict(sorted(bloat_phrase_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        recommendation = ""
        if total_waste > 0:
            most_common = list(top_bloat.keys())[0] if top_bloat else "pleasantries"
            recommendation = (
                f"Remove unnecessary pleasantries like '{most_common}'. "
                f"Be direct and concise. AI doesn't need politeness tokens. "
                f"Potential savings: {total_waste} tokens."
            )

        return {
            'type': 'prompt_bloat',
            'estimated_waste': total_waste,
            'bloat_phrases': top_bloat,
            'avg_bloat_percentage': round(avg_bloat_pct, 1),
            'recommendation': recommendation
        }
