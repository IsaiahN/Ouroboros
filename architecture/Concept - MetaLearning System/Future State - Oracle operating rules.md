 The network can't evolve toward what the oracle wants because it doesn't know what the oracle wants—it only knows "this worked" or "this didn't."

 # Oracle Interface Architecture: Separation of Concerns

**Version**: 1.0
**Date**: 2025-12-23
**Purpose**: Formal specification for oracle isolation, swappability, and validation authority

---

## Core Principle: Oracle as External Validator

**The oracle MUST remain uncontaminated by network incentives, agent goals, or evolutionary pressures.**

### Why This Matters

| If Oracle Is... | Result |
|----------------|--------|
| **Inside the network** | Agents learn to manipulate validation, Goodhart's Law accelerates, prestige system corrupts |
| **Influenced by agents** | Discovery becomes optimized for passing validation, not genuine understanding |
| **Subject to evolution** | Validation criteria drift, locked primitives unlock spuriously, system loses anchor |
| **External and isolated** | ✓ Ground truth remains stable, ✓ Agents must genuinely discover, ✓ System maintains alignment |

### The Separation Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                    EVOLUTIONARY NETWORK                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Agents   │  │Viral Pkgs│  │Database  │  │ Prestige │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │              │          │
│       └─────────────┴──────────────┴──────────────┘          │
│                       │                                       │
│                       ▼                                       │
│              ┌─────────────────┐                             │
│              │ Query Generator │                             │
│              │ (one-way only)  │                             │
│              └────────┬────────┘                             │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        │ Queries (read-only)
                        │
        ════════════════╪════════════════════════════
                        │ THE BARRIER
        ════════════════╪════════════════════════════
                        │
                        ▼
        ┌───────────────────────────────┐
        │        ORACLE INTERFACE        │
        │      (Swappable Backend)       │
        │                                │
        │  Current: Human + LLM Review   │
        │  Future:  Algorithm/Network    │
        └──────────────┬────────────────┘
                       │
                       │ Directives (validated responses)
                       │
        ════════════════╪════════════════════════════
                        │ THE BARRIER
        ════════════════╪════════════════════════════
                        │
                        ▼
        ┌───────────────────────────────┐
        │    Directive Processor         │
        │    (Execute Only If Valid)     │
        └──────────────┬────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Primitive Unlock Manager     │
        │  (Database Write - Append Only)│
        └───────────────────────────────┘
```

---

## Current Oracle Implementation (Human + LLM)

### Input to Oracle (Query Structure)

```python
class OracleQuery:
    """
    Read-only snapshot of discovery context.
    Agents CANNOT see oracle responses, only directive results.
    """
    query_id: str                    # UUID for tracking
    generation: int                  # When query was generated
    operator_id: str                 # Which operator triggered query
    operator_code: str               # The discovered composition

    # Performance evidence (objective metrics only)
    performance_metrics: Dict[str, float] = {
        'level_improvement': float,   # % improvement on Level 2+
        'games_tested': int,          # Sample size
        'transfer_count': int,        # Number of game types helped
        'action_efficiency': float,   # Actions per success
        'consistency': float,         # Win rate variance
    }

    # Pattern signature (for matching against locked primitives)
    pattern_signature: Dict[str, Any] = {
        'input_types': List[str],     # What data does it consume
        'output_type': str,           # What does it produce
        'composition_depth': int,     # How many primitives composed
        'primitive_usage': List[str], # Which primitives used
        'control_flow': str,          # If/loop/iteration structure
    }

    # Arc-AGI specific context
    arc_context: Dict[str, Any] = {
        'games_solved': List[str],    # Which ARC tasks succeeded
        'failure_modes': List[str],   # Common failure patterns
        'near_misses': List[str],     # Almost-solutions
    }

    # NO AGENT STATE, NO PRESTIGE, NO NETWORK GOALS
    # Oracle sees ONLY: "This composition exists and performs this way"
```

### Oracle Decision Process (Human + LLM)

**Phase 1: Metric Review**
- Human reviews `performance_metrics`
- Validates RLVR test results from Arc-AGI gameplay
- Confirms improvement is statistically significant
- LLM checks for obvious gaming (e.g., overfitting to single task)

**Phase 2: Pattern Analysis**
- LLM analyzes `pattern_signature`
- Compares against locked primitive definitions
- Generates candidate matches with confidence scores
- Human reviews candidates for semantic equivalence

**Phase 3: Validation Decision**
- If pattern matches locked primitive + performance threshold met → UNLOCK
- If pattern novel + performance exceptional → REGISTER NOVEL
- If pattern insufficient/spurious → REJECT
- If uncertain → REQUEST MORE EVIDENCE (generates follow-up test directive)

**Phase 4: Directive Generation**
```python
class OracleDirective:
    """
    Oracle's response. Executed by directive processor, NOT seen by agents.
    """
    directive_id: str
    responding_to_query: str

    action_type: str  # "UNLOCK" | "REGISTER_NOVEL" | "REJECT" | "REQUEST_TESTS"

    # If UNLOCK
    primitive_to_unlock: Optional[str] = None
    reasoning: str  # Human-readable explanation

    # If REGISTER_NOVEL
    novel_primitive_name: str = None
    novel_category: str = None  # Which cognitive domain

    # If REQUEST_TESTS
    additional_tests: List[Dict] = None  # Specific ARC tasks to try

    # Metadata (for audit trail)
    oracle_version: str  # "human-llm-v1" or future versions
    confidence: float    # Oracle's confidence in decision
    reviewed_by: str     # Human ID or "algorithm-v2"
```

### Why This Structure Preserves Isolation

1. **Agents never see oracle reasoning** - Only unlock status changes appear in database
2. **Queries are read-only snapshots** - No feedback channel from oracle to agents
3. **Directives are administrative** - Modify system state, don't participate in evolution
4. **Performance metrics are objective** - Win rates, not agent opinions or prestige
5. **Oracle doesn't see network state** - No prestige scores, no viral package spread, no agent strategies

---

## Future Oracle Swappability

### Oracle Backend Variants

| Oracle Type | Validation Mechanism | Swap Trigger |
|-------------|---------------------|--------------|
| **Human + LLM** (current) | Manual review + LLM analysis | N/A (baseline) |
| **Algorithm-Only** | Mechanical thresholds on metrics | When validation rules are fully formalized |
| **Consensus Network** | Multi-validator voting with audit trail | When trust in single oracle questioned |
| **Hybrid Ensemble** | Algorithm pre-filters, human adjudicates edge cases | When query volume exceeds human capacity |

### Swappable Interface Contract

```python
class OracleInterface(ABC):
    """
    Abstract base class - all oracle backends must implement this.
    Ensures swappability without changing network code.
    """

    @abstractmethod
    def submit_query(self, query: OracleQuery) -> str:
        """
        Submit query for validation.

        Returns:
            query_id for tracking

        Does NOT block - query enters queue
        """
        pass

    @abstractmethod
    def get_pending_directives(self) -> List[OracleDirective]:
        """
        Retrieve validated directives ready for execution.

        Called by directive processor each generation.
        Non-blocking - returns empty list if none ready.
        """
        pass

    @abstractmethod
    def get_oracle_metadata(self) -> Dict[str, Any]:
        """
        Identify oracle type and version for audit trail.

        Returns:
            {
                'oracle_type': 'human-llm' | 'algorithm' | 'consensus' | 'hybrid',
                'version': str,
                'last_updated': timestamp
            }
        """
        pass
```

### Example: Algorithm-Only Oracle

```python
class MechanicalOracle(OracleInterface):
    """
    Pure algorithmic validation - no human in loop.
    Uses mechanical thresholds on performance metrics.
    """

    def __init__(self, locked_primitives_db: Dict, thresholds: Dict):
        self.locked_primitives = locked_primitives_db
        self.thresholds = thresholds  # Performance criteria

    def submit_query(self, query: OracleQuery) -> str:
        """Immediate processing - no queue needed."""

        # Check performance threshold
        if query.performance_metrics['level_improvement'] < self.thresholds['min_improvement']:
            return self._generate_reject_directive(query, "Below performance threshold")

        # Pattern matching against locked primitives
        best_match = self._find_best_pattern_match(query.pattern_signature)

        if best_match and best_match['confidence'] > self.thresholds['min_confidence']:
            return self._generate_unlock_directive(query, best_match['primitive'])

        # Check for novelty
        if self._is_sufficiently_novel(query) and self._is_high_performing(query):
            return self._generate_novel_directive(query)

        return self._generate_reject_directive(query, "No clear match or novelty")

    def _find_best_pattern_match(self, signature: Dict) -> Optional[Dict]:
        """Compare pattern signature against locked primitives using structural similarity."""
        # Implementation would use AST comparison, type signature matching, etc.
        pass
```

### Example: Consensus Network Oracle

```python
class ConsensusOracle(OracleInterface):
    """
    Multiple independent validators vote on unlock decisions.
    Requires supermajority (e.g., 3/5) to approve.
    """

    def __init__(self, validator_backends: List[OracleInterface], quorum_threshold: float = 0.6):
        self.validators = validator_backends  # Mix of humans, LLMs, algorithms
        self.quorum = quorum_threshold

    def submit_query(self, query: OracleQuery) -> str:
        """Distribute query to all validators."""
        query_id = query.query_id

        # Submit to all validators
        for validator in self.validators:
            validator.submit_query(query)

        # Track in consensus database
        self.pending_consensus[query_id] = {
            'query': query,
            'votes': {},
            'submitted_at': datetime.now()
        }

        return query_id

    def get_pending_directives(self) -> List[OracleDirective]:
        """Return directives only when consensus reached."""
        ready_directives = []

        for query_id, consensus_state in self.pending_consensus.items():
            # Collect votes from all validators
            votes = self._collect_validator_votes(query_id)

            if self._has_consensus(votes):
                directive = self._generate_consensus_directive(query_id, votes)
                ready_directives.append(directive)
                del self.pending_consensus[query_id]  # Processed

        return ready_directives

    def _has_consensus(self, votes: Dict) -> bool:
        """Check if supermajority agrees on action."""
        if len(votes) < len(self.validators) * self.quorum:
            return False  # Not enough votes yet

        action_counts = {}
        for vote in votes.values():
            action_counts[vote['action']] = action_counts.get(vote['action'], 0) + 1

        max_votes = max(action_counts.values())
        return max_votes / len(votes) >= self.quorum
```

---

## Anti-Contamination Safeguards

### 1. Query Sanitization

```python
class QuerySanitizer:
    """
    Ensures queries contain ONLY performance data, not network state.
    """

    FORBIDDEN_FIELDS = [
        'agent_prestige',
        'viral_package_spread',
        'social_capital',
        'agent_goals',
        'network_strategies',
        'other_agent_opinions'
    ]

    def sanitize(self, raw_query: Dict) -> OracleQuery:
        """Strip any fields that could contaminate oracle."""

        # Whitelist only allowed fields
        sanitized = {
            k: v for k, v in raw_query.items()
            if k in OracleQuery.__annotations__
        }

        # Verify no forbidden data leaked through
        query_str = json.dumps(sanitized)
        for forbidden in self.FORBIDDEN_FIELDS:
            assert forbidden not in query_str, f"Query contaminated with {forbidden}"

        return OracleQuery(**sanitized)
```

### 2. Directive Execution Isolation

```python
class DirectiveProcessor:
    """
    Executes oracle directives in isolated context.
    Agents CANNOT observe directive execution, only final state changes.
    """

    def execute_directive(self, directive: OracleDirective):
        """
        Apply directive to database.
        No agent event, no notification, no prestige reward.
        """

        if directive.action_type == "UNLOCK":
            # Simply change primitive status in database
            self.unlock_manager.unlock_primitive(
                primitive_name=directive.primitive_to_unlock,
                unlocked_by_operator=directive.responding_to_query,
                oracle_reasoning=directive.reasoning
            )
            # DO NOT:
            # - Notify agents
            # - Grant prestige to operator's creator
            # - Create viral package announcing unlock
            # Agents discover unlock naturally when they try to use it

        elif directive.action_type == "REGISTER_NOVEL":
            # Add to primitive registry
            self.unlock_manager.register_novel_primitive(
                name=directive.novel_primitive_name,
                category=directive.novel_category,
                discovered_by_operator=directive.responding_to_query
            )
            # Again, NO agent notification

        # Log to audit trail (human-readable, not agent-accessible)
        self.audit_logger.log_directive(directive)
```

### 3. Oracle State Isolation

```python
class OracleStateDatabase:
    """
    Oracle has its own database, completely separate from network DB.
    Prevents any information leakage.
    """

    def __init__(self, oracle_db_path: str):
        # Separate SQLite file, different connection
        self.oracle_conn = sqlite3.connect(oracle_db_path)

        # Network DB connection is NEVER passed to oracle
        # Oracle cannot query agent states, prestige, viral packages

    def store_query(self, query: OracleQuery):
        """Oracle's private query history."""
        # Stored in oracle DB, not network DB
        pass

    def store_decision_log(self, query_id: str, decision: Dict):
        """Audit trail for oracle decisions."""
        # For human review, algorithm tuning, not agent access
        pass
```

---

## Preventing Oracle Gaming

### Attack Vector 1: Agents Optimize for Oracle Approval

**Threat**: Agents evolve operators that look like what oracle approves, not what actually works.

**Mitigation**:
```python
# Oracle ONLY sees performance metrics from Arc-AGI gameplay
# Agents CANNOT see oracle's decision criteria
# Agents CANNOT see unlock reasoning

# Performance must come from EXTERNAL ground truth (Arc-AGI test results)
# Not from internal network metrics (prestige, viral spread)
```

### Attack Vector 2: Oracle Query Flooding

**Threat**: Agents submit thousands of spurious queries to fish for approvals.

**Mitigation**:
```python
class OracleQueryRateLimiter:
    """
    Limit queries to highest-confidence candidates only.
    """

    def should_query_oracle(self, operator: Operator) -> bool:
        """
        Pre-filter before query submission.
        Oracle only sees operators that already show strong RLVR results.
        """

        # Require minimum performance
        if operator.level_improvement < 0.15:
            return False

        # Require minimum sample size
        if operator.games_tested < 20:
            return False

        # Require transfer learning evidence
        if operator.game_types_helped < 2:
            return False

        return True
```

### Attack Vector 3: Oracle Criterion Reverse-Engineering

**Threat**: Agents deduce oracle's validation logic by observing unlock patterns.

**Mitigation**:
```python
# 1. Oracle decisions are NEVER published to network
# 2. Agents see only: "Primitive X is now unlocked" (not why)
# 3. Multiple operators may unlock same primitive (obfuscates pattern)
# 4. Oracle can use randomized approval thresholds
# 5. Consensus oracle with diverse validators prevents pattern learning
```

---

## Oracle Version Migration

### Migration Protocol (When Swapping Oracle Backend)

```python
class OracleMigrationManager:
    """
    Handle oracle backend changes without corrupting network evolution.
    """

    def migrate_oracle(
        self,
        old_oracle: OracleInterface,
        new_oracle: OracleInterface,
        generation: int
    ):
        """
        Swap oracle backends safely.
        """

        # 1. Flush pending queries from old oracle
        pending_directives = old_oracle.get_pending_directives()
        for directive in pending_directives:
            self.directive_processor.execute_directive(directive)

        # 2. Mark migration point in audit log
        self.audit_logger.log_migration(
            from_oracle=old_oracle.get_oracle_metadata(),
            to_oracle=new_oracle.get_oracle_metadata(),
            generation=generation,
            reason="[Human explanation for why migration occurred]"
        )

        # 3. Atomic swap
        self.current_oracle = new_oracle

        # 4. DO NOT notify network - agents experience no disruption
        # Queries continue flowing, directives continue executing
        # Network is oracle-agnostic
```

### Ensuring Backward Compatibility

```python
class UnlockStatusPreserver:
    """
    New oracle must respect previous oracle's unlock decisions.
    """

    def __init__(self, primitive_unlock_db):
        self.unlock_history = primitive_unlock_db

    def validate_new_oracle(self, new_oracle: OracleInterface):
        """
        New oracle cannot un-unlock primitives.
        Can only add new unlocks or novel registrations.
        """

        current_unlocked = self.get_currently_unlocked_primitives()

        # Test new oracle with historical queries
        for historical_query in self.get_historical_unlock_queries():
            new_decision = new_oracle.submit_query(historical_query)

            # If previous oracle unlocked, new oracle must agree (or abstain)
            if historical_query.resulted_in_unlock:
                assert new_decision.action_type in ["UNLOCK", "REQUEST_TESTS"], \
                    f"New oracle would reverse unlock of {historical_query.primitive}"
```

---

## Audit Trail & Transparency

### Oracle Decision Logging

```python
class OracleAuditLogger:
    """
    Complete audit trail of all oracle decisions.
    For human review, algorithm debugging, not agent access.
    """

    def log_query(self, query: OracleQuery):
        """Record every query submitted."""
        self.db.execute("""
            INSERT INTO oracle_queries (
                query_id, generation, operator_id,
                performance_metrics, pattern_signature, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, ...)

    def log_decision(self, directive: OracleDirective):
        """Record every oracle decision with full reasoning."""
        self.db.execute("""
            INSERT INTO oracle_decisions (
                directive_id, query_id, action_type,
                primitive_affected, reasoning,
                oracle_version, confidence, decided_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ...)

    def generate_audit_report(self, generation_range: Tuple[int, int]) -> str:
        """
        Human-readable report of oracle activity.

        Includes:
        - Unlock rate over time
        - Novel primitive discoveries
        - Rejection reasons
        - Oracle confidence trends
        - Inter-oracle disagreements (if consensus mode)
        """
        pass
```

### Human Review Interface (for Human+LLM Oracle)

```python
class HumanOracleReviewUI:
    """
    Interface for human oracle reviewer.
    Shows performance data, suggests decisions, logs human override.
    """

    def present_query_for_review(self, query: OracleQuery):
        """
        Display query with all relevant context.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════╗
        ║             ORACLE QUERY REVIEW                          ║
        ╚══════════════════════════════════════════════════════════╝

        Query ID: {query.query_id}
        Generation: {query.generation}
        Operator: {query.operator_id}

        PERFORMANCE METRICS:
        - Level Improvement: {query.performance_metrics['level_improvement']:.2%}
        - Games Tested: {query.performance_metrics['games_tested']}
        - Transfer Count: {query.performance_metrics['transfer_count']}
        - Action Efficiency: {query.performance_metrics['action_efficiency']:.2f}

        PATTERN SIGNATURE:
        - Composition Depth: {query.pattern_signature['composition_depth']}
        - Primitives Used: {', '.join(query.pattern_signature['primitive_usage'])}

        ARC-AGI CONTEXT:
        - Games Solved: {', '.join(query.arc_context['games_solved'][:5])}

        ─────────────────────────────────────────────────────────

        LLM SUGGESTION:
        {self.llm.analyze_query(query)}

        ─────────────────────────────────────────────────────────

        YOUR DECISION:
        [1] UNLOCK - Matches locked primitive: _________
        [2] REGISTER NOVEL - Novel primitive name: _________
        [3] REJECT - Reason: _________
        [4] REQUEST TESTS - Additional validation needed

        Enter choice:
        """)

        human_decision = input()

        # Log human decision + reasoning
        self.log_human_override(query.query_id, human_decision)

        return self.generate_directive_from_human_input(query, human_decision)
```

---

## The Oracle's Limited Scope

### What Oracle Does (Validation Authority)

- ✓ Validate that discovered patterns meet performance thresholds
- ✓ Match patterns to locked primitives (unlock gatekeeper)
- ✓ Register novel primitives that don't match anything known
- ✓ Request additional testing when evidence is ambiguous
- ✓ Maintain audit trail of all decisions

### What Oracle Does NOT Do (Network Participation)

- ✗ Participate in evolution (no genetic operations, no viral packages)
- ✗ Influence agent goals or strategies (agents don't see oracle reasoning)
- ✗ Award prestige or resources (only unlocks/registers primitives)
- ✗ Guide exploration (no hints, no teaching, no curriculum)
- ✗ Access network state (no prestige data, no agent strategies, no social dynamics)
- ✗ Interfere with regulatory engine (population mix, budgets remain autonomous)

### The Oracle's Single Interface Point

```
NETWORK → Query Generator → Oracle → Directive Processor → Unlock Manager → DATABASE
         (creates queries)  (validates) (executes)      (updates status)  (agents read)

         ↑ One-way flow, read-only snapshot of performance data

         Agents never see:
         - Oracle reasoning
         - Directive content
         - Why primitives unlocked
         - Oracle's confidence scores
```

---

## Success Criteria for Oracle Isolation

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Zero contamination** | No network state in queries | Audit query sanitizer logs |
| **Oracle-agnostic evolution** | Network performs identically regardless of oracle backend | A/B test with mechanical vs human oracle |
| **No gaming** | Unlock rate stable despite query volume | Track unlock rate vs query submission rate |
| **Audit completeness** | 100% of decisions logged with reasoning | Verify audit trail has no gaps |
| **Backward compatibility** | New oracle respects old unlocks | Regression test on historical queries |
| **Swappability** | Oracle swap with <1hr downtime | Time migration protocol execution |

---

## Open Questions for Future Oracles

### 1. Consensus Oracle Voting Mechanisms

If using multiple validators:
- Majority vote vs weighted vote (by oracle confidence)?
- Tie-breaking mechanism?
- How to handle validator disagreement for audit trail?

### 2. Algorithm Oracle Criterion Formalization

To build pure algorithmic oracle:
- What are the complete, formal criteria for each primitive unlock?
- Can we enumerate all edge cases in advance?
- How to avoid brittleness (overly strict rules)?

### 3. Oracle Performance Benchmarking

How to evaluate if oracle is "correct":
- Ground truth dataset of correct unlock decisions?
- Human expert agreement rate?
- Novel primitive quality (do they help in practice)?

### 4. Oracle Update Frequency

- Can oracle criteria evolve over time (learning from outcomes)?
- If so, how to prevent drift that invalidates old decisions?
- Version locking per primitive unlock?

---

## Conclusion: Oracle as Immutable Referee

The oracle must remain **external to the evolutionary process**, serving as an **immutable ground truth** against which the network validates its discoveries.

**Key Principles**:
1. **Isolation**: Oracle sees only performance metrics, never network state
2. **Swappability**: Oracle backend can change without disrupting network
3. **Non-participation**: Oracle validates but doesn't evolve or strategize
4. **Transparency**: All decisions auditable, even if not visible to agents
5. **Backward compatibility**: New oracles respect previous unlocks

**The oracle is not a teacher. It is a certification authority.**

It doesn't guide, doesn't hint, doesn't reward. It merely answers the binary question: "Does this pattern meet the standard?" And that standard is defined by **external ground truth** (Arc-AGI performance), not by internal network dynamics.

This preserves the integrity of the discovery process: agents must genuinely learn, not just optimize for approval.

---

**END OF ORACLE ARCHITECTURE SPECIFICATION**
