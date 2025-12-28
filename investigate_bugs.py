"""
Investigate Bugs - LLM Entry Point for Autonomous Bug Investigation
====================================================================

This script is the entry point for the LLM (Claude) to investigate and fix
reasoning bugs detected by the Oracle during evolution runs.

USAGE:
------
1. List open bugs:
   python investigate_bugs.py --list
   
2. Get investigation prompt for highest priority bug:
   python investigate_bugs.py --investigate
   
3. Investigate specific bug:
   python investigate_bugs.py --investigate BUG_ID
   
4. Mark bug as fixed:
   python investigate_bugs.py --fix BUG_ID "Description of fix"
   
5. Full report with history:
   python investigate_bugs.py --report

Rule 1: Disable pycache
Rule 2: All data in database
Rule 11: No unicode emojis
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
import json
import argparse
from datetime import datetime
from typing import Optional

from database_interface import DatabaseInterface
from oracle_health_monitor import OracleHealthMonitor


def main():
    parser = argparse.ArgumentParser(
        description='Investigate reasoning bugs detected by Oracle'
    )
    parser.add_argument('--list', action='store_true',
                        help='List all open bugs')
    parser.add_argument('--investigate', nargs='?', const='auto', metavar='BUG_ID',
                        help='Get investigation prompt (optional: specific bug ID)')
    parser.add_argument('--fix', nargs=2, metavar=('BUG_ID', 'DESCRIPTION'),
                        help='Mark a bug as fixed')
    parser.add_argument('--report', action='store_true',
                        help='Print full bug report with history')
    parser.add_argument('--critical-only', action='store_true',
                        help='Show only critical bugs')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Initialize Oracle
    db = DatabaseInterface('core_data.db')
    oracle = OracleHealthMonitor(db=db)
    
    if args.list:
        list_bugs(oracle, critical_only=args.critical_only, as_json=args.json)
    elif args.investigate:
        bug_id = args.investigate if args.investigate != 'auto' else None
        investigate_bug(oracle, bug_id)
    elif args.fix:
        bug_id, description = args.fix
        fix_bug(oracle, bug_id, description)
    elif args.report:
        oracle.print_bug_report()
        print("\n--- Bug History ---")
        history = oracle.get_bug_history(limit=10)
        for bug in history:
            status_icon = "[OPEN]" if bug['status'] == 'open' else "[FIXED]"
            print(f"{status_icon} {bug['bug_type']} ({bug['bug_id']}): {bug['occurrence_count']} occurrences")
    else:
        # Default: show summary and next action
        show_summary(oracle)


def list_bugs(oracle: OracleHealthMonitor, critical_only: bool = False, as_json: bool = False):
    """List all open bugs."""
    severity = 'critical' if critical_only else None
    bugs = oracle.get_open_bugs(severity=severity)
    
    if as_json:
        # Clean up for JSON output
        for bug in bugs:
            if 'evidence_json' in bug:
                del bug['evidence_json']
            if 'affected_games_json' in bug:
                del bug['affected_games_json']
        print(json.dumps(bugs, indent=2, default=str))
        return
    
    if not bugs:
        print("[OK] No open bugs found")
        return
    
    print(f"\nOpen Reasoning Bugs: {len(bugs)}")
    print("-" * 60)
    
    for bug in bugs:
        severity_tag = "[CRIT]" if bug['severity'] == 'critical' else "[WARN]"
        print(f"\n{severity_tag} {bug['bug_type']}")
        print(f"    ID: {bug['bug_id']}")
        print(f"    Occurrences: {bug['occurrence_count']}")
        print(f"    First seen: Generation {bug['generation']}")
        print(f"    Description: {bug['description'][:100]}...")


def investigate_bug(oracle: OracleHealthMonitor, bug_id: Optional[str] = None):
    """Get investigation prompt for a bug."""
    prompt = oracle.get_bug_investigation_prompt(bug_id)
    print(prompt)


def fix_bug(oracle: OracleHealthMonitor, bug_id: str, description: str):
    """Mark a bug as fixed."""
    oracle.mark_bug_fixed(bug_id, description)
    print(f"[OK] Bug {bug_id} marked as fixed")
    print(f"    Fix: {description}")


def show_summary(oracle: OracleHealthMonitor):
    """Show summary and suggest next action."""
    bugs = oracle.get_open_bugs()
    critical = [b for b in bugs if b['severity'] == 'critical']
    warnings = [b for b in bugs if b['severity'] == 'warning']
    
    print("\n" + "=" * 60)
    print("REASONING BUG INVESTIGATION DASHBOARD")
    print("=" * 60)
    
    if not bugs:
        print("[OK] No open reasoning bugs - system healthy")
        print("\nRun an evolution to detect new bugs:")
        print("  python run_evolution.py")
        print("=" * 60)
        return
    
    print(f"\nOpen Bugs: {len(bugs)}")
    print(f"  Critical: {len(critical)}")
    print(f"  Warnings: {len(warnings)}")
    
    # Show highest priority bug
    top_bug = bugs[0]
    print(f"\n--- Highest Priority Bug ---")
    print(f"Type: {top_bug['bug_type']}")
    print(f"Severity: {top_bug['severity'].upper()}")
    print(f"Occurrences: {top_bug['occurrence_count']}")
    print(f"Description: {top_bug['description'][:80]}...")
    
    print("\n--- Next Steps ---")
    print("1. Get investigation details:")
    print(f"   python investigate_bugs.py --investigate {top_bug['bug_id']}")
    print("\n2. After fixing, mark as resolved:")
    print(f"   python investigate_bugs.py --fix {top_bug['bug_id']} \"description of fix\"")
    
    print("\n--- Quick Commands ---")
    print("  --list              List all open bugs")
    print("  --investigate       Get investigation prompt")
    print("  --report            Full report with history")
    print("=" * 60)


if __name__ == "__main__":
    main()
