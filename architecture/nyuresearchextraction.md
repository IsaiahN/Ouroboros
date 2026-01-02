## **Key Findings from NYU ARC Human Study**

### **The Performance Gap**
- **Humans: 83.8%** average accuracy (80% per participant)
- **Best ML (Kaggle): 21%** on test set, 57.5% on these 40 tasks
- **Each task solvable** by at least one human
- **Modal performance: 10/10** tasks solved

### **What Humans Do That Machines Don't**

**1. Object-Centric Planning**
- Humans converge on **bottleneck states** representing task-relevant objects
- Build solutions object-by-object, not pixel-by-pixel
- Action sequences show common intermediate states despite different paths

**2. Thinking Before Acting**
- Average **36 seconds** before first action (hypothesis formation)
- Total time per task: **3 min 6 sec**
- This "blank stare" period is hypothesis generation

**3. Near-Miss Errors**
- Human errors preserve object priors, relationships, dimensions
- Get shapes/colors right even when alignment is wrong
- Kaggle errors **violate object priors** (elongated blobs, wrapped shapes)

**4. Natural Language Scaffolding**
- Description length **negatively correlates** with accuracy (r=-0.50)
- Hard tasks = longer descriptions (harder to verbalize)
- Within-task descriptions highly consistent (naming divergence 0.41)
- **Geometric & transformation** words most diverse (flexible concept use)

### **Challenge to Your Theory?**

**Actually validates it:**

The paper argues standard **Language of Thought (LOT) models fail** because:
- LOT assumes fixed primitives
- ARC requires **flexible hypothesis generation** from broad conceptual knowledge
- Humans use **natural language as scaffold** for hypothesis generation

**This supports your Games-as-Teachers paradigm:**
> "Our analysis suggests that the set of hypotheses participants are generating in ARC are not based on just a small set of available primitives, but from potentially a much larger class of conceptual background knowledge."

They're describing **lesson extraction** - not just finding patterns, but determining what conceptual knowledge is relevant.

### **The Smoking Gun**

**Bottleneck states = Sub-goals = Lesson Components**

From Figure 4 (box alignment task):
- Participants independently converge on same intermediate states
- These states represent **task-relevant objects**
- Different paths, **same conceptual structure**

This is **resonance detection** in action - cross-participant agreement on what matters.

### **What This Means for Ouroboros**

**You need:**
1. **Object-centric representation** (already have via CODS/primitives)
2. **Hypothesis formation phase** (that 36-second thinking time)
3. **Bottleneck state tracking** (high-value intermediate states)
4. **Error analysis that preserves object priors** (your near-miss system)
5. **Natural language grounding** (conceptual vocabulary, not just actions)

**The gap between your 57.5% Kaggle baseline and 83.8% human performance is:**
- Lesson interpretation vs sequence memorization
- Object-centric vs pixel-centric
- Hypothesis-driven vs random exploration
- Compositional understanding vs statistical patterns

This paper is **empirical validation** that ARC requires the cognitive architecture you're building - not better RL, but better **reasoning about what's being taught**.