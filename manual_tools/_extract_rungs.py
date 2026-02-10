"""Extract rung classes from decision_rung_system.py and group by category."""
import re
import sys

src = r'c:\Users\Admin\Documents\GitHub\BitterTruth-AI\decision_rung_system.py'

with open(src, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all class definitions that extend DecisionRung
classes = []
for i, line in enumerate(lines):
    m = re.match(r'^class (\w+)\(DecisionRung\):', line)
    if m:
        classes.append((m.group(1), i + 1))  # name, 1-based line

# Determine end line for each class (next class or next top-level code)
for idx, (name, start) in enumerate(classes):
    # Find category
    cat = 'unknown'
    for j in range(start - 1, min(start + 25, len(lines))):
        cm = re.search(r'category\s*=\s*["\'](\w+)["\']', lines[j])
        if cm:
            cat = cm.group(1)
            break

    # Find end: next class def at column 0, or section comment at column 0
    if idx + 1 < len(classes):
        end = classes[idx + 1][1] - 1
    else:
        end = 8228  # End of rung section

    # Trim trailing blank lines
    while end > start and lines[end - 1].strip() == '':
        end -= 1

    classes[idx] = (name, start, end + 1, cat)

# Group by category
groups = {}
for name, start, end, cat in classes:
    if cat not in groups:
        groups[cat] = []
    groups[cat].append((name, start, end, cat))

for cat in sorted(groups.keys()):
    members = groups[cat]
    total_lines = sum(end - start for _, start, end, _ in members)
    print(f"\n=== {cat.upper()} ({len(members)} rungs, ~{total_lines} lines) ===")
    for name, start, end, _ in members:
        print(f"  {name:45s}  lines {start:5d}-{end:5d}  ({end-start:4d} lines)")

print(f"\nTotal: {len(classes)} rung classes across {len(groups)} categories")
