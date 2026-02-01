from __future__ import annotations

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be early

"""In-process event bus scaffolding for behavior-parity loop split.

This bus is intentionally simple: emit-only from orchestrator, subscribe/handle in plugins.
Plugins must be idempotent and should not raise; exceptions are returned to the caller for
hook failure logging. Mode/role/budget enforcement stays in the orchestrator/guards.

Events and payload expectations mirror architecture/runtime/events.md.
"""

import hashlib
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class EventType(Enum):
    RUN_INIT = auto()
    ACTION_PROPOSALS = auto()
    ACTION_CHOSEN = auto()
    ACTION_EXECUTED = auto()
    FRAME_CHANGED = auto()
    STEP_COMPLETE = auto()
    RUN_FINALIZED = auto()
    HOOK_FAILURE_DETECTED = auto()
    GUARD_TRIGGERED = auto()
    COMPREHENSION_GAP_DETECTED = auto()
    HEARTBEAT_MISSED = auto()
    MODE_VIOLATION = auto()
    ROLE_ASSIGNMENT_SET = auto()
    SEQUENCE_REPLAY_STARTED = auto()
    SEQUENCE_REPLAY_FINISHED = auto()
    CODS_OPERATOR_USED = auto()
    LESSON_INTERPRETATION_READY = auto()


GuardCode = Tuple[str, Dict[str, Any]]  # (code, detail payload)
Subscriber = Callable[[EventType, Dict[str, Any]], None]


@dataclass
class Event:
    event_type: EventType
    payload: Dict[str, Any]


class EventBus:
    """Minimal pub/sub bus with local subscribers.

    - publish returns a list of (subscriber, exception) pairs for callers to log.
    - subscribers are invoked synchronously in registration order.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Subscriber]] = {}
        self._hook_failure_event: Optional[EventType] = None

    def subscribe(self, event_type: EventType, handler: Subscriber) -> None:
        handlers = self._subscribers.setdefault(event_type, [])
        handlers.append(handler)

    def set_hook_failure_event(self, event_type: EventType) -> None:
        """Configure an event type to emit when subscriber callbacks fail."""
        self._hook_failure_event = event_type

    def publish(self, event: Event) -> List[Tuple[Subscriber, Exception]]:
        failures: List[Tuple[Subscriber, Exception]] = []
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event.event_type, event.payload)
            except Exception as exc:  # narrow to capture for hook_failures logging by caller
                failures.append((handler, exc))
                if self._hook_failure_event:
                    try:
                        fail_evt = Event(
                            event_type=self._hook_failure_event,
                            payload={
                                "hook": event.event_type.name.lower(),
                                "hook_phase": "unknown",
                                "errors": [str(exc)],
                                "stack_hash": hashlib.sha256(str(exc).encode("utf-8", "ignore")).hexdigest()[:12],
                                **event.payload,
                            },
                        )
                        # Emit internally without recursing into hook failure emission
                        inner_handlers = self._subscribers.get(self._hook_failure_event, [])
                        for h in inner_handlers:
                            try:
                                h(fail_evt.event_type, fail_evt.payload)
                            except Exception:
                                # Avoid infinite loop; swallow secondary failures
                                pass
                    except Exception:
                        pass
        return failures


def make_event(event_type: EventType, **payload: Any) -> Event:
    return Event(event_type=event_type, payload=payload)
