import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Cognitive Replay Viewer — Watch the agent think.

Renders CognitiveFrame replays in several formats:
  1. Console log (one line per action)
  2. Console dashboard (multi-line per action, live-view style)
  3. HTML report (full game replay as static HTML)

Usage:
    from tools.replay_viewer import ReplayViewer
    from engines.cognition.cognitive_frame import CognitiveFrame

    viewer = ReplayViewer(frames)
    viewer.print_log()          # Quick scan
    viewer.print_dashboard()    # Detailed view
    viewer.save_html("replay.html")  # Permanent record
"""

import json
from typing import Dict, List, Optional

from engines.cognition.cognitive_frame import CognitiveFrame


class ReplayViewer:
    """Renders cognitive frame replays."""

    def __init__(self, frames: List[CognitiveFrame]):
        self._frames = frames

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    # ─── Console Formats ──────────────────────────────────────────────

    def print_log(self, start: int = 0, end: Optional[int] = None):
        """One line per action — for quick scanning."""
        for cf in self._frames[start:end]:
            print(cf.to_log_line())

    def print_dashboard(self, start: int = 0, end: Optional[int] = None):
        """Multi-line dashboard — for detailed analysis."""
        for cf in self._frames[start:end]:
            print(cf.to_dashboard())
            print()

    def print_summary(self):
        """Game-level summary statistics."""
        if not self._frames:
            print("[REPLAY] No frames to display")
            return

        total = len(self._frames)
        last = self._frames[-1]

        # Count action speeds
        speeds: Dict[str, int] = {}
        for cf in self._frames:
            speeds[cf.action_speed] = speeds.get(cf.action_speed, 0) + 1

        # Count frame changes
        changes = sum(1 for cf in self._frames if cf.frame_changed)
        level_ups = sum(1 for cf in self._frames if cf.level_changed)

        # Track unique positions
        positions = set()
        for cf in self._frames:
            if cf.action_x is not None:
                positions.add((cf.action_x, cf.action_y))

        # Track certainty trajectory
        certs = [cf.certainty for cf in self._frames]
        avg_cert = sum(certs) / len(certs) if certs else 0.0

        # Track map growth
        map_completeness = [cf.map_completeness for cf in self._frames if cf.map_completeness > 0]
        final_map = map_completeness[-1] if map_completeness else 0.0

        # Strategies used
        strategies = set(cf.strategy for cf in self._frames)

        print(f"\n{'=' * 60}")
        print(f"  GAME REPLAY SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Total actions:    {total}")
        print(f"  Frame changes:    {changes} ({changes/total:.0%})")
        print(f"  Level-ups:        {level_ups}")
        print(f"  Unique positions: {len(positions)}")
        print(f"  Final level:      {last.level}")
        print(f"{'-' * 60}")
        print(f"  Action speeds:")
        for speed, count in sorted(speeds.items()):
            print(f"    {speed:12s}: {count:3d} ({count/total:.0%})")
        print(f"{'-' * 60}")
        print(f"  Certainty:   avg={avg_cert:.2f}")
        print(f"  Map:         final={final_map:.0%}")
        print(f"  Strategies:  {', '.join(sorted(strategies))}")
        print(f"  Puzzle type: {last.puzzle_type}")
        print(f"{'=' * 60}\n")

    # ─── HTML Report ──────────────────────────────────────────────────

    def save_html(self, path: str):
        """Save a full HTML replay report."""
        html = self._render_html()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[REPLAY] Saved HTML report: {path}")

    def _render_html(self) -> str:
        """Generate HTML for the replay."""
        rows = []
        for cf in self._frames:
            speed_color = {
                'mapped': '#2ecc71',
                'reasoned': '#3498db',
                'explore': '#f39c12',
                'random': '#e74c3c',
            }.get(cf.action_speed, '#95a5a6')

            change_icon = '[CHG]' if cf.frame_changed else '[---]'
            if cf.level_changed:
                change_icon = '[LVL]'

            coord = ''
            if cf.action_x is not None:
                coord = f'({cf.action_x},{cf.action_y})'

            rows.append(f'''
            <tr>
                <td>{cf.action_number}</td>
                <td>{cf.level}</td>
                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">{cf.perception_summary}</td>
                <td>{cf.strategy}</td>
                <td>{cf.certainty:.2f}</td>
                <td>{cf.map_completeness:.0%}</td>
                <td style="color:{speed_color};font-weight:bold">{cf.action_speed}</td>
                <td>A{cf.action_type} {coord}</td>
                <td>{change_icon}</td>
                <td>{cf.surprise:.2f}</td>
            </tr>''')

        return f'''<!DOCTYPE html>
<html>
<head>
<title>Cognitive Replay</title>
<style>
body {{ font-family: 'Consolas', 'Courier New', monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }}
h1 {{ color: #00d4ff; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
th {{ background: #16213e; color: #00d4ff; padding: 8px 12px; text-align: left; position: sticky; top: 0; }}
td {{ padding: 6px 12px; border-bottom: 1px solid #333; }}
tr:hover {{ background: #16213e; }}
.summary {{ background: #16213e; padding: 15px; border-radius: 8px; margin: 10px 0; }}
.metric {{ display: inline-block; margin: 0 20px; text-align: center; }}
.metric .value {{ font-size: 24px; color: #00d4ff; }}
.metric .label {{ font-size: 12px; color: #888; }}
</style>
</head>
<body>
<h1>Cognitive Replay</h1>
<div class="summary">
    <div class="metric">
        <div class="value">{len(self._frames)}</div>
        <div class="label">Actions</div>
    </div>
    <div class="metric">
        <div class="value">{sum(1 for cf in self._frames if cf.frame_changed)}</div>
        <div class="label">Frame Changes</div>
    </div>
    <div class="metric">
        <div class="value">{sum(1 for cf in self._frames if cf.level_changed)}</div>
        <div class="label">Level Ups</div>
    </div>
    <div class="metric">
        <div class="value">{self._frames[-1].level if self._frames else 0}</div>
        <div class="label">Final Level</div>
    </div>
    <div class="metric">
        <div class="value">{self._frames[-1].map_completeness:.0%}" if self._frames else "0%"</div>
        <div class="label">Map Complete</div>
    </div>
</div>
<table>
<thead>
<tr>
    <th>#</th><th>Lvl</th><th>Perception</th><th>Strategy</th>
    <th>Cert</th><th>Map</th><th>Speed</th><th>Action</th>
    <th>Result</th><th>Surprise</th>
</tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</body>
</html>'''

    # ─── Data Export ──────────────────────────────────────────────────

    def to_json(self) -> str:
        """Export replay as JSON."""
        return json.dumps([cf.to_dict() for cf in self._frames], indent=2)

    def save_json(self, path: str):
        """Save replay as JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        print(f"[REPLAY] Saved JSON: {path}")
