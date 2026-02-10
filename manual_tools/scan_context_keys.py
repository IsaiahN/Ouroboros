"""Quick scan of context keys used by decision rungs vs provided by ContextBuilder."""
import re
import sys

sys.dont_write_bytecode = True

# Read rung system
with open('decision_rung_system.py', 'r', encoding='utf-8') as f:
    rung_content = f.read()

# Find all context.get('key') and context['key'] patterns
pat_get = re.compile(r"""context\.get\(\s*['"](\w+)['"]""")
pat_bracket = re.compile(r"""context\[\s*['"](\w+)['"]""")

rung_keys = sorted(set(pat_get.findall(rung_content) + pat_bracket.findall(rung_content)))

# Read context_builder to see what to_dict() emits
with open('context_builder.py', 'r', encoding='utf-8') as f:
    cb_content = f.read()

# Find all keys in DecisionContext.to_dict return dict
pat_dict_key = re.compile(r"""['"](\w+)['"]\s*:""")
# Find lines within DecisionContext.to_dict method
in_to_dict = False
in_decision_context = False
provided_keys = set()
for line in cb_content.split('\n'):
    if 'class DecisionContext' in line:
        in_decision_context = True
    if in_decision_context and 'def to_dict' in line:
        in_to_dict = True
        continue
    if in_to_dict:
        # Stop at next method def at same or lower indent
        stripped = line.strip()
        if stripped.startswith('def ') and 'to_dict' not in stripped:
            break
        if stripped.startswith('class '):
            break
        matches = pat_dict_key.findall(line)
        provided_keys.update(matches)

print(f"Context keys consumed by rungs: {len(rung_keys)}")
print(f"Context keys provided by ContextBuilder.to_dict(): {len(provided_keys)}")
print()

missing = sorted(set(rung_keys) - provided_keys)
if missing:
    print(f"MISSING from ContextBuilder ({len(missing)}):")
    for k in missing:
        print(f"  [MISS] {k}")
else:
    print("[OK] All rung keys are provided by ContextBuilder")

print()
extra = sorted(provided_keys - set(rung_keys))
if extra:
    print(f"Extra in ContextBuilder (not consumed by rungs): {len(extra)}")
    for k in extra:
        print(f"  [EXTRA] {k}")
