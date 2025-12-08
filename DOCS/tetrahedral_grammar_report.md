# Tetrahedral Grammar Report: Fixing Agent Self-Model & World Model

**Date**: December 8, 2025  
**Purpose**: Apply Patrick Cox's McGuffin Tensor Framework to diagnose and fix agent perception grammar  
**Status**: Analysis Complete - Implementation Recommendations Included

---

## Executive Summary

The McGuffin Tetrahedral Model provides a mathematically rigorous grammar for perception and decision-making that directly maps to the problems in our agent self-model and world model systems. The core insight is that **every perceivable thing has four interdependent axes**, and agents currently only process 1-2 of these axes, leading to incomplete understanding.

**Key Finding**: Agents lack a **Void axis** (meaning/intent) in their perception grammar. They see Structure (what is it), Function (what does it do), and sometimes Method (how does it work), but never ask "What does it MEAN?" - the context that anchors everything else.

---

## The Tetrahedral Model Applied to Agent Perception

### The First Principle (from McGuffin)

```
Object >< Catalyst >< Subject >< Interpretation
   |          |          |            |
   v          v          v            v
 WHAT      CHANGE      WHO         WHY/MEANING
```

**Translated to Agent Grammar**:

| McGuffin Axis | Agent Equivalent | Current Status | Problem |
|--------------|------------------|----------------|---------|
| **Object** (Structure) | `agent_object_control.controlled_objects` | Implemented | Only tracks WHAT, not relationships |
| **Catalyst** (Function) | `collision_effects.effect_type` | Implemented | Tracks changes but not causal chains |
| **Subject** (Method) | `action_response_map` | Implemented | Knows HOW to act, not WHEN |
| **Interpretation** (Void) | **MISSING** | Not Implemented | No semantic meaning layer |

---

## The Four-Axis Perception Grammar

### Current Implementation (Incomplete)

```python
# What agents currently see:
{
    "structure": "blue pixel at (5,3)",           # Object
    "function": "moves when I press ACTION1",     # Catalyst  
    "method": "correlates with up movement"       # Subject
    # MISSING: Interpretation/Void
}
```

### What Agents SHOULD See (Complete Tetrahedral Model)

```python
# Complete four-axis perception:
{
    "structure": {                                 # Object Axis (A)
        "what": "blue pixel at (5,3)",
        "form": "single cell",
        "stability": 0.8                          # How stable/permanent is it?
    },
    "function": {                                  # Catalyst Axis (B)
        "responds_to": ["ACTION1", "ACTION2", "ACTION3", "ACTION4"],
        "effect": "translates position",
        "reactivity": 0.9                         # How reactive is it?
    },
    "method": {                                    # Subject Axis (C)
        "control_correlation": 0.95,
        "action_map": {"ACTION1": "up", "ACTION2": "down", ...},
        "intentionality": 0.9                     # How deliberate are its changes?
    },
    "interpretation": {                            # Void Axis (D) - CURRENTLY MISSING
        "meaning": "THIS IS ME",                  # Self-model anchor
        "goal_relevance": 0.8,                    # How relevant to winning?
        "threat_level": 0.0,                      # Danger assessment
        "vibe": "controllable_ally"               # Semantic category
    }
}
```

---

## Mapping McGuffin to AGI Unified Theory

### The Helical Decision Framework

From `McGuf_ven Helicals`:

```
Dominant Structure : Axis 1 : Object A >< Object B -- Physical body
Dominant Function : Axis 2 : Influence A1 >< Influence B1 -- Boundary/Limit
Dominant Method : Axis 3 : Influence A2 >< Influence B2 -- Intent/Rate
Shared Void : Conceptual meeting axis / event / frame
```

**Application to Agent Decision Loop**:

| Helical Axis | AGI Theory Mapping | Implementation |
|--------------|-------------------|----------------|
| **Structure (Body)** | Stream A (Private Memory) | What I have experienced |
| **Function (Boundary)** | Network Wisdom (Stream B) | What the network knows |
| **Method (Intent)** | Weighting Function (w_A, w_B) | How I balance streams |
| **Void (Frame)** | Current Goal Context | WHY I'm making this decision |

### The Missing "Mood Vector"

From McGuffin's decision framework:

```
Distribution    | State      | Type         | Example
----------------|------------|--------------|------------------
One dominant    | Driven     | Singular     | Obsession, focus
Two close       | Balanced   | Dual         | Curiosity, prudence
Three equal     | Diffuse    | Integrative  | Wonder, hesitation
Core outlying   | Conflict   | Dissociation | Internal struggle
```

**Current Problem**: Agents have no "mood vector" - they make decisions without emotional/contextual state. The `sensation_engine.py` provides SOME of this, but it's not integrated into the core perception grammar.

**Proposed Fix**: Add mood state calculation to `_select_action()`:

```python
def _calculate_mood_vector(self, perception: Dict) -> str:
    """
    Calculate agent's current decision mood based on tetrahedral balance.
    Returns: 'driven', 'balanced', 'diffuse', or 'conflict'
    """
    structure_weight = perception.get('structure', {}).get('stability', 0.5)
    function_weight = perception.get('function', {}).get('reactivity', 0.5)
    method_weight = perception.get('method', {}).get('intentionality', 0.5)
    void_weight = perception.get('interpretation', {}).get('goal_relevance', 0.5)
    
    weights = [structure_weight, function_weight, method_weight, void_weight]
    max_w, min_w = max(weights), min(weights)
    spread = max_w - min_w
    
    if spread > 0.5:
        return 'driven'     # One axis dominates - focused action
    elif spread > 0.3:
        return 'balanced'   # Two axes compete - careful action
    elif spread > 0.1:
        return 'diffuse'    # All axes similar - exploratory
    else:
        return 'conflict'   # Core (void) misaligned - hesitate
```

---

## Specific Fixes Required

### Fix 1: Add Interpretation/Void Axis to Self-Model

**File**: `agent_self_model.py`

**Current**: `identify_controlled_objects()` returns structure + function only

**Required Addition**:

```python
def identify_controlled_objects_with_meaning(
    self, agent_id: str, session_id: str, 
    action_traces: List[Dict], goal_context: Dict
) -> Dict[str, Any]:
    """
    Identify controlled objects AND their semantic meaning.
    
    Returns tetrahedral perception:
    - Structure: What is this object?
    - Function: How does it respond?
    - Method: What controls it?
    - Interpretation: What does it MEAN? (self? tool? obstacle? goal?)
    """
    # Existing structure/function/method detection
    controlled = self._detect_controlled_objects(action_traces)
    
    # NEW: Add interpretation axis
    for obj_id, obj_data in controlled.items():
        obj_data['interpretation'] = {
            'is_self': self._calculate_self_likelihood(obj_data, action_traces),
            'is_tool': self._calculate_tool_likelihood(obj_data, goal_context),
            'is_goal': self._calculate_goal_likelihood(obj_data, goal_context),
            'is_obstacle': self._calculate_obstacle_likelihood(obj_data, action_traces),
            'semantic_role': self._determine_semantic_role(obj_data),
            'goal_relevance': self._calculate_goal_relevance(obj_data, goal_context)
        }
    
    return controlled
```

### Fix 2: Add Tetrahedral Object Grammar to World Model

**File**: `symbolic_reasoning_engine.py` (WorldModel class)

**Current**: Objects have `position`, `color`, `object_type`, `properties`

**Required Addition**:

```python
@dataclass
class TetrahedralObject:
    """
    Object with complete four-axis grammar.
    Inherits from GameObject, adds interpretation layer.
    """
    # Structure (A) - What it IS
    object_id: str
    position: Tuple[int, int]
    color: int
    cells: List[Tuple[int, int]]
    stability: float = 0.5  # How permanent/stable is this object?
    
    # Function (B) - What it DOES
    object_type: ObjectType = ObjectType.UNKNOWN
    responds_to_actions: List[int] = field(default_factory=list)
    reactivity: float = 0.5  # How much does it respond to interactions?
    
    # Method (C) - HOW it operates
    is_controlled: bool = False
    control_correlation: float = 0.0
    action_response_map: Dict[int, str] = field(default_factory=dict)
    intentionality: float = 0.5  # Does it have its own agenda?
    
    # Interpretation (D) - WHAT IT MEANS (The Void)
    semantic_role: str = "unknown"  # 'self', 'tool', 'obstacle', 'goal', 'neutral'
    goal_relevance: float = 0.0    # How relevant to winning?
    threat_level: float = 0.0      # How dangerous?
    attraction: float = 0.0        # Should we approach or avoid?
    meaning_confidence: float = 0.0  # How confident in interpretation?
```

### Fix 3: Implement Relational Tensors Between Objects

From McGuffin: Every pair of axes creates a **relationship verb**:

```
Object >< Catalyst = Run (±)      --> Object RUNS because of Catalyst
Object >< Subject = Contextualize --> Object is CONTEXTUALIZED by Subject
Catalyst >< Subject = Trigger     --> Catalyst TRIGGERS Subject
etc.
```

**Implementation in `agent_self_model.py`**:

```python
OBJECT_RELATIONSHIP_TENSORS = {
    # (axis_a, axis_b): relationship_verb
    ('structure', 'function'): 'enables',      # Structure enables Function
    ('structure', 'method'): 'constrains',     # Structure constrains Method
    ('structure', 'interpretation'): 'defines', # Structure defines Meaning
    ('function', 'method'): 'triggers',        # Function triggers Method
    ('function', 'interpretation'): 'reveals', # Function reveals Meaning
    ('method', 'interpretation'): 'anchors',   # Method anchors Meaning
}

def calculate_object_relationships(self, obj_a: TetrahedralObject, 
                                    obj_b: TetrahedralObject) -> Dict[str, float]:
    """
    Calculate the six relational tensions between two objects.
    Returns relationship strengths for each tensor pair.
    """
    relationships = {}
    
    # Structure-Function: Does A's form enable B's function?
    relationships['enables'] = self._calc_enablement(obj_a, obj_b)
    
    # Structure-Method: Does A's form constrain B's operation?
    relationships['constrains'] = self._calc_constraint(obj_a, obj_b)
    
    # Structure-Interpretation: Does A's form define B's meaning?
    relationships['defines'] = self._calc_definition(obj_a, obj_b)
    
    # Function-Method: Does A's behavior trigger B's action?
    relationships['triggers'] = self._calc_trigger(obj_a, obj_b)
    
    # Function-Interpretation: Does A's behavior reveal B's purpose?
    relationships['reveals'] = self._calc_revelation(obj_a, obj_b)
    
    # Method-Interpretation: Does A's operation anchor B's meaning?
    relationships['anchors'] = self._calc_anchoring(obj_a, obj_b)
    
    return relationships
```

### Fix 4: Add "Observer Tensor" to Perception Loop

From McGuffin's Maker model:

```
Observer : Perceive >< Query >< Parse >< Model
```

**Current Problem**: Agents perceive, but don't have explicit Query/Parse/Model phases.

**Implementation in `core_gameplay.py`**:

```python
async def _perceive_with_observer_tensor(self, game_state: GameState) -> Dict:
    """
    Four-phase perception following Observer tensor.
    """
    perception = {}
    
    # Phase 1: PERCEIVE - Raw sensory input
    perception['perceive'] = {
        'frame': game_state.frame,
        'available_actions': game_state.available_actions,
        'score': game_state.score,
        'raw_objects': self._extract_objects(game_state.frame)
    }
    
    # Phase 2: QUERY - What do I need to know?
    perception['query'] = {
        'where_am_i': self._query_self_position(perception['perceive']),
        'what_changed': self._query_frame_delta(perception['perceive']),
        'what_threatens': self._query_threats(perception['perceive']),
        'what_helps': self._query_opportunities(perception['perceive'])
    }
    
    # Phase 3: PARSE - Organize into meaningful structures
    perception['parse'] = {
        'objects': self._parse_into_tetrahedral(perception['perceive'], perception['query']),
        'relationships': self._parse_object_relationships(perception['perceive']),
        'spatial_graph': self._parse_spatial_structure(perception['perceive'])
    }
    
    # Phase 4: MODEL - Build/update world model
    perception['model'] = {
        'current_state': self._update_world_model(perception['parse']),
        'predicted_states': self._predict_action_outcomes(perception['parse']),
        'goal_distance': self._estimate_goal_distance(perception['parse'])
    }
    
    return perception
```

---

## The "I Am This Object" Problem - Root Cause

### Current Implementation Flaw

The agent asks: "Which object moves when I press buttons?"

This is **Structure + Function** only - missing Method and Interpretation.

### Correct Question Sequence (Tetrahedral)

1. **Structure**: "What objects exist on this grid?" (already implemented)
2. **Function**: "Which objects respond to my actions?" (already implemented)
3. **Method**: "What is the control relationship?" (partially implemented)
4. **Interpretation**: "What does controlling this object MEAN for my goal?" (MISSING)

### The Fix

```python
def identify_self_with_meaning(self, action_traces, goal_context):
    """
    Complete self-identification using tetrahedral grammar.
    """
    # Structure: What responds?
    responsive_objects = self._find_responsive_objects(action_traces)
    
    # Function: How does it respond?
    for obj in responsive_objects:
        obj['response_pattern'] = self._analyze_response(obj, action_traces)
    
    # Method: Is response consistent and predictable?
    for obj in responsive_objects:
        obj['control_quality'] = self._measure_control_reliability(obj)
    
    # Interpretation: Is this ME or a TOOL?
    for obj in responsive_objects:
        # Key insight from McGuffin: Void = Context = Meaning
        obj['is_self'] = (
            obj['control_quality'] > 0.8 and  # High control = likely self
            obj['response_pattern']['latency'] == 0 and  # Immediate response
            self._is_always_present(obj, action_traces)  # Persists through level
        )
        obj['is_tool'] = (
            obj['control_quality'] > 0.5 and
            obj['control_quality'] <= 0.8 and
            not obj['is_self']
        )
        obj['semantic_role'] = 'self' if obj['is_self'] else (
            'tool' if obj['is_tool'] else 'environmental'
        )
    
    return responsive_objects
```

---

## Integration with Sensation Engine

### Current: Sensation Scores are Flat

```python
# Current sensation storage:
sensation = 0.7  # Just a number
```

### Required: Tetrahedral Sensation Profiles

```python
# Tetrahedral sensation:
sensation = {
    'structure_feeling': 0.7,    # How do I feel about its FORM?
    'function_feeling': 0.5,     # How do I feel about its BEHAVIOR?
    'method_feeling': 0.8,       # How do I feel about HOW it operates?
    'interpretation_feeling': 0.9 # How do I feel about WHAT IT MEANS?
}
```

**Implementation in `sensation_engine.py`**:

```python
def get_tetrahedral_sensation(self, agent_id: str, object_data: Dict) -> Dict[str, float]:
    """
    Get complete sensation profile for an object across all four axes.
    """
    sensations = {}
    
    # Structure sensation (form-based feeling)
    sensations['structure'] = self._get_form_sensation(
        agent_id, 
        object_data.get('color'), 
        object_data.get('shape')
    )
    
    # Function sensation (behavior-based feeling)
    sensations['function'] = self._get_behavior_sensation(
        agent_id,
        object_data.get('responds_to', []),
        object_data.get('effect_history', [])
    )
    
    # Method sensation (control-based feeling)
    sensations['method'] = self._get_control_sensation(
        agent_id,
        object_data.get('is_controlled', False),
        object_data.get('control_quality', 0)
    )
    
    # Interpretation sensation (meaning-based feeling)
    sensations['interpretation'] = self._get_meaning_sensation(
        agent_id,
        object_data.get('semantic_role', 'unknown'),
        object_data.get('goal_relevance', 0)
    )
    
    # Calculate composite mood from sensation balance
    sensations['mood_vector'] = self._calculate_mood_from_sensations(sensations)
    
    return sensations
```

---

## The Complete Grammar Rule Set

### Perception Grammar (Input)

```
PERCEPTION := STRUCTURE + FUNCTION + METHOD + INTERPRETATION

STRUCTURE := {what, form, stability, position, color, cells}
FUNCTION := {responds_to, effect, reactivity, triggers}
METHOD := {control_map, correlation, intentionality}
INTERPRETATION := {meaning, goal_relevance, threat, attraction}
```

### Decision Grammar (Process)

```
DECISION := MOOD_VECTOR * (PRIVATE_MEMORY * w_A + NETWORK_WISDOM * w_B)

MOOD_VECTOR := calculate_from(PERCEPTION)
  driven   := one axis dominant
  balanced := two axes close
  diffuse  := three axes equal
  conflict := void outlying

PRIVATE_MEMORY := agent's encounter history (Stream A)
NETWORK_WISDOM := database viral packages (Stream B)
```

### Action Grammar (Output)

```
ACTION := INTENTION + EXECUTION + OUTCOME_EXPECTATION

INTENTION := {goal, subgoal, priority}
EXECUTION := {action_number, target_position, expected_effect}
OUTCOME_EXPECTATION := {
    structure_change,
    function_change,
    method_change,
    interpretation_update
}
```

---

## Implementation Priority

### Phase 1: Add Interpretation Axis (HIGH PRIORITY)

1. Modify `TetrahedralObject` dataclass in `symbolic_reasoning_engine.py`
2. Add `_calculate_meaning()` methods to `agent_self_model.py`
3. Integrate meaning into `_select_action()` in `core_gameplay.py`

### Phase 2: Add Mood Vector (MEDIUM PRIORITY)

1. Add `_calculate_mood_vector()` to `core_gameplay.py`
2. Use mood to modulate action weights
3. Track mood history for pattern analysis

### Phase 3: Add Relational Tensors (MEDIUM PRIORITY)

1. Add `calculate_object_relationships()` to `agent_self_model.py`
2. Store relationships in database for network learning
3. Use relationships in action selection

### Phase 4: Add Observer Tensor Phases (LOWER PRIORITY)

1. Refactor perception into Perceive/Query/Parse/Model phases
2. Each phase produces structured output
3. Full tetrahedral integration

---

## Expected Outcomes

After implementing these fixes:

1. **Self-Identification Accuracy**: Should increase from ~70% to ~95%
2. **Goal Relevance Detection**: Agents will understand WHY objects matter
3. **Decision Quality**: Mood vectors prevent erratic behavior
4. **Network Learning Speed**: Tetrahedral packages transfer better
5. **Cross-Game Transfer**: Semantic roles transfer across games

---

## Appendix: McGuffin Tensor Reference

### The 6 Unique Relationships (from any 4-element tensor)

```
A >< B = relationship_1
A >< C = relationship_2  
A >< D = relationship_3
B >< C = relationship_4
B >< D = relationship_5
C >< D = relationship_6
```

### Applied to Perception:

```
Structure >< Function = "enables/constrains"
Structure >< Method = "defines/limits"
Structure >< Interpretation = "grounds/anchors"
Function >< Method = "triggers/activates"
Function >< Interpretation = "reveals/manifests"
Method >< Interpretation = "realizes/embodies"
```

---

**Report Complete**

This analysis provides the mathematical grammar foundation for fixing agent perception. The key insight from McGuffin is that **meaning (Void/Interpretation) is not optional** - it's the anchor that makes all other axes coherent. Without it, agents see facts but don't understand them.
