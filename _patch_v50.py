"""
v50: after replay (partial or zero), always fall through to cognitive play.
After replay wins L1, env is at L2 start. Cognitive play can try L2+
without calling make() again. This replaces the v49 partial-score break.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '                # v49: competition mode \u2014 replay partial/fail handling\n'
    '                if competition_mode:\n'
    '                    if score > 0.0:\n'
    '                        # Partial replay success: keep score, stop here\n'
    '                        # (cannot call make() again in competition)\n'
    '                        break\n'
    '                    # score==0: fall through to cognitive play in same attempt\n'
    '                else:\n'
    '                    continue\n'
)

# Also try the ASCII-escaped version that JSON may produce
OLD_ASCII = (
    '                # v49: competition mode \\u2014 replay partial/fail handling\n'
    '                if competition_mode:\n'
    '                    if score > 0.0:\n'
    '                        # Partial replay success: keep score, stop here\n'
    '                        # (cannot call make() again in competition)\n'
    '                        break\n'
    '                    # score==0: fall through to cognitive play in same attempt\n'
    '                else:\n'
    '                    continue\n'
)

NEW = (
    '                # v49/v50: always fall through to cognitive play after replay\n'
    '                # - replay wins L1: env is at L2 start, cognitive plays L2+\n'
    '                # - replay fails: cognitive plays from L1\n'
    '                # In competition mode, never continue (would call make() again).\n'
    '                if not competition_mode:\n'
    '                    continue  # offline: try again from scratch next attempt\n'
    '                # competition_mode: fall through to cognitive play below\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v50" in src:
        print(f"  Cell {i}: v50 already applied")
        continue
    replaced = False
    for old in [OLD, OLD_ASCII]:
        if old in src:
            src = src.replace(old, NEW, 1)
            replaced = True
            break
    if replaced:
        cell["source"] = [src]
        print(f"  Cell {i}: applied v50")
    elif "v49" in src:
        print(f"  Cell {i}: WARNING v49 found but patch string didn't match")
        # Debug: show what we have
        idx = src.find("v49")
        print(f"    Context: {repr(src[idx:idx+300])}")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
