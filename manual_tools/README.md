# Manual Tools

**Purpose**: Standalone scripts for debugging, testing, analysis, and one-time operations.  
**Note**: These are NOT integrated into the main evolution loop - they are developer utilities.

---

## Folder Structure

```
manual_tools/
|-- analysis/           # Data analysis and auditing tools
|-- database/           # Database inspection and schema tools
|-- monitoring/         # System status and scorecard monitoring
|-- utilities/          # Replay URLs, emoji removal, tests
|-- README.md
```

---

## Analysis Tools (`analysis/`)

Tools for analyzing gameplay, prestige, and system behavior.

| File | Purpose | Usage |
|------|---------|-------|
| `gameplay_analyzer.py` | Analyze agent gameplay progression | `python analysis/gameplay_analyzer.py --hours 6` |
| `audit_prestige_system.py` | Audit prestige calculations | `python analysis/audit_prestige_system.py` |
| `pariah_analysis.py` | Analyze pariah system state | `python analysis/pariah_analysis.py` |

### gameplay_analyzer.py

```bash
python analysis/gameplay_analyzer.py                    # Default: last 3 hours
python analysis/gameplay_analyzer.py --hours 6          # Last 6 hours
python analysis/gameplay_analyzer.py --generations 270  # From generation 270+
python analysis/gameplay_analyzer.py --compare          # Include baseline comparison
python analysis/gameplay_analyzer.py --full             # Full analysis with all options
python analysis/gameplay_analyzer.py --no-games         # Skip individual game listing
python analysis/gameplay_analyzer.py --limit 50         # Show more games
```

---

## Database Tools (`database/`)

Tools for inspecting database schema and contents.

| File | Purpose | Usage |
|------|---------|-------|
| `schema_inspector.py` | Inspect database schema | `python database/schema_inspector.py --table agents` |
| `inspect_db.py` | Detailed database inspection | `python database/inspect_db.py` |

### schema_inspector.py

```bash
python database/schema_inspector.py                     # List all tables
python database/schema_inspector.py --table agents      # Show specific table details
python database/schema_inspector.py --table agents --sample  # With sample data
python database/schema_inspector.py --find generation   # Find tables with column
python database/schema_inspector.py --counts            # Show row counts
python database/schema_inspector.py --full              # Full schema dump
python database/schema_inspector.py --db path/to/db     # Use different database
```

---

## Monitoring Tools (`monitoring/`)

Tools for monitoring system status and reviewing scorecards.

| File | Purpose | Usage |
|------|---------|-------|
| `system_status_report.py` | Generate system status report | `python monitoring/system_status_report.py` |
| `review_scorecards.py` | Review game scorecards | `python monitoring/review_scorecards.py` |

---

## Utility Tools (`utilities/`)

Miscellaneous utility scripts.

| File | Purpose | Usage |
|------|---------|-------|
| `get_replay_url.py` | Get ARC game replay URL | `python utilities/get_replay_url.py <game_id>` |
| `remove_emojis.py` | Remove Unicode emojis from code (Rule 11) | `python utilities/remove_emojis.py` |
| `test_pariah_decay.py` | Test pariah toxicity decay | `python utilities/test_pariah_decay.py` |

---

## Running From Project Root

These tools reference the parent directory's modules. Run from project root:

```bash
# From project root (recommended)
python manual_tools/analysis/gameplay_analyzer.py --hours 3

# Or set PYTHONPATH if running from manual_tools
cd manual_tools
$env:PYTHONPATH = ".."
python analysis/gameplay_analyzer.py
```

---

**Note**: For database cleanup, use `safe_cleanup.py` in the project root (per Rule 12).
