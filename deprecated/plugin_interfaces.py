from __future__ import annotations

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be early

"""Plugin interface scaffolding for event-first runtime.

Each plugin registers for EventType values and receives payloads from the bus.
Plugins must be idempotent and mode-aware; side-effects (DB writes) are allowed
only when mode == LIVE. Exceptions should be caught by callers and logged as
hook failures; plugins should raise only when they cannot proceed.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Protocol

from event_bus import Event, EventBus, EventType


class Plugin(Protocol):
    def interested_events(self) -> Iterable[EventType]:
        """Return events this plugin wants to handle."""
        ...

    def handle_event(self, event: Event) -> None:
        """Handle an event. Must be idempotent; raise to signal hook failure."""
        ...


@dataclass
class PluginManager:
    bus: EventBus
    plugins: List[Plugin]

    def register_all(self) -> None:
        for plugin in self.plugins:
            for ev in plugin.interested_events():
                self.bus.subscribe(ev, lambda et, payload, p=plugin: p.handle_event(Event(et, payload)))


class ModeAwarePlugin:
    """Mixin for mode-aware plugins; subclass should implement handle()."""

    allowed_modes: List[str] = ["LIVE"]

    def __init__(self, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        self.allowed_modes = list(allowed_modes)

    def interested_events(self) -> Iterable[EventType]:  # pragma: no cover - to be overridden
        return []

    def handle_event(self, event: Event) -> None:
        mode = event.payload.get("mode")
        if mode not in self.allowed_modes:
            return
        self.handle(event)

    def handle(self, event: Event) -> None:  # pragma: no cover - to be overridden
        raise NotImplementedError
