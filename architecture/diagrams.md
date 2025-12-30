# Architecture Diagrams (Planning)

## Runtime Flow (modes enforced, ARC API unchanged)
```mermaid
flowchart TD
    A[INIT] --> B[STEP]
    B -->|loop| B
    B --> C[POST_STEP]
    C -->|if not done| B
    C --> D[FINALIZE]
```

## Event Bus + Plugins (DB-backed)
```mermaid
flowchart LR
    E[Event Bus] --> P1[Sequence Plugin]
    E --> P2[Viral Package Plugin]
    E --> P3[CODS Plugin]
    E --> P4[Hypothesis/Metacog Plugin]
    E --> P5[Prestige/Budget Plugin]
    E --> P6[Hook Failure Monitor]
    E --> P7[Sensation & Self-Model Plugin]
```

## Action Selection Pipeline (proposal combiner)
```mermaid
flowchart TD
    S1[Sequence Replay Proposals] --> M[Proposal Combiner]
    S2[CODS Operator Proposals] --> M
    S3[Role Priors / Heuristics] --> M
    S4[Escape / Safety] --> M
    S5[Exploration / Random] --> M
    M --> A[Chosen Action]
    A --> EV[ACTION_CHOSEN Event]
```

## Data Lineage (attempt_id is the spine)
```mermaid
flowchart LR
    ATT[attempts] --> AP[action_proposals_log]
    ATT --> SEQ[sequences]
    ATT --> PKG[viral_packages]
    ATT --> HYP[hypotheses/interpretations]
    ATT --> LES[lesson_interpretations]
    ATT --> HF[hook_failures]
```

## Two-Streams Influence per Decision
```mermaid
flowchart TD
    WA[w_A private memory] --> W[Weighted Mix]
    WB[w_B network wisdom] --> W
    W --> P[Proposal Weights]
    P --> A[Chosen Action]
```

## Games-as-Teachers (lesson-centric logging)
```mermaid
flowchart TD
    L1[Observe examples] --> L2[Interpret lesson]
    L2 --> L3[Test interpretation]
    L3 --> L4[Record coverage/contradictions]
    L4 --> L5[Extract lesson artifact]
    L5 --> L6[Validate transfer]
```
