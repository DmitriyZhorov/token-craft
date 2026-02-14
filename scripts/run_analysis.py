"""Non-interactive Token-Craft runner for skill invocation."""
import sys
import io
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add token_craft to path
sys.path.insert(0, str(Path(__file__).parent))

from skill_handler import TokenCraftHandler

def main():
    """Run Token-Craft analysis non-interactively."""
    # Parse mode argument
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'

    # Normalize mode variations (handle aliases)
    mode_map = {
        'full': 'full',
        'detailed': 'full',
        'complete': 'full',
        'summary': 'summary',
        'overview': 'summary',
        'quick': 'quick',
        'status': 'quick',
        'one-line': 'quick',
        'json': 'json'
    }

    # Normalize to lowercase and map
    mode_normalized = mode_map.get(mode.lower(), 'full')

    # Run analysis
    handler = TokenCraftHandler()
    report = handler.run(mode=mode_normalized)
    print(report)

if __name__ == "__main__":
    main()
