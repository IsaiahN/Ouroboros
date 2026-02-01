#!/usr/bin/env python3
"""
CODE PATTERN SCANNER FOR DATA DISCONNECTIONS
=============================================
Scans codebase for patterns that often lead to data being silently ignored.

Run: python manual_tools/scan_disconnection_patterns.py

Patterns we look for:
1. `if X is None: return` - Early returns that skip data usage
2. `if confidence < threshold: return None` - Threshold gates
3. `getattr(self, X, None)` followed by `if X is None` - Missing initialization
4. DB query followed by conditional that might skip usage
5. `if not hasattr(self, X):` - Missing attribute guards
"""

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# Files to scan
TARGET_FILES = [
    "core_gameplay.py",
    "agent_self_model.py",
    "action_handler.py",
    "network_knowledge_synthesis.py",
    "terminal_pattern_detector.py",
    "mastery_system.py",
    "abstraction_config.py",
    "cods_engine.py",
]

class DisconnectionPatternScanner:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.findings: List[Dict] = []

    def scan_all(self):
        """Scan all target files for disconnection patterns."""
        print("=" * 70)
        print("CODE PATTERN SCANNER - Finding potential data disconnections")
        print("=" * 70)

        for filename in TARGET_FILES:
            filepath = self.base_dir / filename
            if filepath.exists():
                self.scan_file(filepath)
            else:
                print(f"  [SKIP] {filename} not found")

        self.print_findings()

    def scan_file(self, filepath: Path):
        """Scan a single file for patterns."""
        print(f"\n[SCANNING] {filepath.name}")

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        # Pattern 1: Early return on None
        self.find_none_returns(filepath, lines)

        # Pattern 2: Threshold gates that return None
        self.find_threshold_gates(filepath, lines)

        # Pattern 3: getattr with None default followed by None check
        self.find_getattr_none_patterns(filepath, lines)

        # Pattern 4: DB query followed by conditional skip
        self.find_db_query_skips(filepath, lines)

        # Pattern 5: hasattr guards
        self.find_hasattr_guards(filepath, lines)

        # Pattern 6: Functions that return None without logging
        self.find_silent_none_returns(filepath, lines)

    def find_none_returns(self, filepath: Path, lines: List[str]):
        """Find 'if X is None: return' patterns."""
        pattern = re.compile(r'if\s+(\w+)\s+is\s+None\s*:\s*$')

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                var_name = match.group(1)
                # Check if next non-empty line is a return
                for j in range(i+1, min(i+3, len(lines))):
                    if lines[j].strip().startswith('return'):
                        # Check if it's a meaningful variable (not just error handling)
                        if var_name not in ['error', 'e', 'err', 'exc']:
                            self.findings.append({
                                'file': filepath.name,
                                'line': i + 1,
                                'pattern': 'early_return_on_none',
                                'variable': var_name,
                                'code': line.strip(),
                                'severity': 'MEDIUM'
                            })
                        break

    def find_threshold_gates(self, filepath: Path, lines: List[str]):
        """Find threshold comparisons that return None."""
        # Match: if confidence < 0.4: return None
        pattern = re.compile(r'if\s+(\w+)\s*[<>]=?\s*([\d.]+)\s*:\s*$')

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                var_name = match.group(1)
                threshold = match.group(2)
                # Check if next line returns None
                for j in range(i+1, min(i+3, len(lines))):
                    if 'return None' in lines[j] or 'return\n' in lines[j] or lines[j].strip() == 'return':
                        if var_name in ['confidence', 'reliability', 'score', 'threshold', 'min_confidence']:
                            self.findings.append({
                                'file': filepath.name,
                                'line': i + 1,
                                'pattern': 'threshold_gate_returns_none',
                                'variable': var_name,
                                'threshold': threshold,
                                'code': line.strip(),
                                'severity': 'HIGH',
                                'suggestion': f"Consider 'least-bad' fallback when {var_name} is below threshold"
                            })
                        break

    def find_getattr_none_patterns(self, filepath: Path, lines: List[str]):
        """Find getattr(self, X, None) where None might be wrong default."""
        pattern = re.compile(r'getattr\s*\(\s*self\s*,\s*[\'"](\w+)[\'"]\s*,\s*None\s*\)')

        for i, line in enumerate(lines):
            matches = pattern.findall(line)
            for attr_name in matches:
                # Check if this attr is critical for decision making
                critical_attrs = ['_current_agent_position', '_controlled_object', '_self_model',
                                  '_hypothesis', '_network_wisdom', '_mastery']
                if any(critical in attr_name for critical in critical_attrs):
                    # Check if there's a None check that skips logic
                    for j in range(i, min(i+5, len(lines))):
                        if f'{attr_name} is None' in lines[j] or f'not {attr_name}' in lines[j]:
                            if 'return' in lines[j] or (j+1 < len(lines) and 'return' in lines[j+1]):
                                self.findings.append({
                                    'file': filepath.name,
                                    'line': i + 1,
                                    'pattern': 'getattr_none_skip',
                                    'attribute': attr_name,
                                    'code': line.strip()[:80],
                                    'severity': 'HIGH',
                                    'suggestion': f"Consider fallback logic when {attr_name} is None"
                                })
                            break

    def find_db_query_skips(self, filepath: Path, lines: List[str]):
        """Find DB queries where results might be silently discarded."""
        query_pattern = re.compile(r'(self\.db\.execute_query|execute_query)\s*\(')

        for i, line in enumerate(lines):
            if query_pattern.search(line):
                # Look for "if not rows:" or "if rows is None:" in next few lines
                for j in range(i, min(i+10, len(lines))):
                    if re.search(r'if\s+not\s+\w+\s*:', lines[j]) or re.search(r'if\s+\w+\s+is\s+None', lines[j]):
                        # Check if it returns None/continues without logging
                        for k in range(j, min(j+3, len(lines))):
                            if 'return None' in lines[k] and 'logger' not in lines[k-1] and 'logger' not in lines[k]:
                                self.findings.append({
                                    'file': filepath.name,
                                    'line': i + 1,
                                    'pattern': 'db_query_silent_skip',
                                    'code': line.strip()[:60] + '...',
                                    'severity': 'MEDIUM',
                                    'suggestion': "Add logging when DB query returns empty but data expected"
                                })
                                break
                        break

    def find_hasattr_guards(self, filepath: Path, lines: List[str]):
        """Find hasattr guards that might prevent feature usage."""
        pattern = re.compile(r'if\s+not\s+hasattr\s*\(\s*self\s*,\s*[\'"](\w+)[\'"]\s*\)')

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                attr_name = match.group(1)
                # Check if it leads to early return/continue
                for j in range(i, min(i+3, len(lines))):
                    if 'return' in lines[j] or 'continue' in lines[j]:
                        self.findings.append({
                            'file': filepath.name,
                            'line': i + 1,
                            'pattern': 'hasattr_guard_skip',
                            'attribute': attr_name,
                            'code': line.strip(),
                            'severity': 'LOW',
                            'suggestion': f"Verify {attr_name} is initialized in __init__"
                        })
                        break

    def find_silent_none_returns(self, filepath: Path, lines: List[str]):
        """Find functions that return None without explanation."""
        # Look for function definitions
        func_pattern = re.compile(r'def\s+(\w+)\s*\(')

        in_function = False
        func_name = ""
        func_start = 0

        for i, line in enumerate(lines):
            func_match = func_pattern.search(line)
            if func_match:
                in_function = True
                func_name = func_match.group(1)
                func_start = i

            if in_function and 'return None' in line:
                # Check if there's a logger call in the surrounding context
                context = lines[max(0, i-3):i+1]
                has_logging = any('logger' in l for l in context)

                if not has_logging and func_name.startswith('_get'):
                    self.findings.append({
                        'file': filepath.name,
                        'line': i + 1,
                        'pattern': 'silent_none_return',
                        'function': func_name,
                        'code': line.strip(),
                        'severity': 'LOW',
                        'suggestion': f"Add debug logging before return None in {func_name}"
                    })

    def print_findings(self):
        """Print all findings grouped by severity."""
        print("\n" + "=" * 70)
        print("SCAN RESULTS")
        print("=" * 70)

        if not self.findings:
            print("\n  [OK] No concerning patterns found!")
            return

        # Group by severity
        by_severity = defaultdict(list)
        for f in self.findings:
            by_severity[f['severity']].append(f)

        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            findings = by_severity.get(severity, [])
            if findings:
                print(f"\n[{severity}] {len(findings)} findings:")
                print("-" * 50)
                for f in findings[:10]:  # Show first 10 per severity
                    print(f"  {f['file']}:{f['line']} - {f['pattern']}")
                    if 'variable' in f:
                        print(f"    Variable: {f['variable']}")
                    if 'attribute' in f:
                        print(f"    Attribute: {f['attribute']}")
                    if 'suggestion' in f:
                        print(f"    Suggestion: {f['suggestion']}")
                    print(f"    Code: {f['code'][:70]}...")
                    print()
                if len(findings) > 10:
                    print(f"  ... and {len(findings) - 10} more")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  HIGH severity: {len(by_severity['HIGH'])}")
        print(f"  MEDIUM severity: {len(by_severity['MEDIUM'])}")
        print(f"  LOW severity: {len(by_severity['LOW'])}")
        print(f"\n  Total findings: {len(self.findings)}")

        print("\n" + "=" * 70)
        print("HOW TO USE THESE FINDINGS")
        print("=" * 70)
        print("""
  For each HIGH severity finding:
  1. Go to the file:line indicated
  2. Trace the data flow: Where does this data come from?
  3. Ask: "Is there a valid case where this data exists but gets ignored?"
  4. If yes: Add fallback/least-bad logic
  5. If no: Add debug logging to understand when it happens

  Common fixes:
  - threshold_gate_returns_none -> Add "least-bad" fallback
  - getattr_none_skip -> Add fallback when attribute not set
  - early_return_on_none -> Consider if None has a valid alternative
""")


def main():
    base_dir = Path(__file__).parent.parent
    scanner = DisconnectionPatternScanner(base_dir)
    scanner.scan_all()


if __name__ == "__main__":
    main()
