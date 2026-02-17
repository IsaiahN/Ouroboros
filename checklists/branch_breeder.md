# Branch Breeder -- combinatorial search across successful experiments
# Absorbs: copilot-instructions Part 9 (branch management, cherry-picking)

## Branch Operations (from copilot-instructions Part 9)
- [ ] Before merging, understand WHY branches differ (intentional design vs. merge accident)
- [ ] Check if borrowed code depends on other changes in the source branch
- [ ] Document what was combined and why in commit message

## Process
- [ ] Identify successful experiment branches from Trend Tracker
- [ ] Generate combination candidates (all pairs, then triples if pairs succeed)
- [ ] For each combination:
      - [ ] Attempt git merge into new crossbred/ branch
      - [ ] If merge conflict: flag for Code Reviewer LLM to resolve
      - [ ] Run Code Reviewer checklist on combined code
      - [ ] Run evolution trial on combined branch
      - [ ] Classify result: additive / synergistic / conflicting / dominant
- [ ] Promote best combination to lab/mainline candidate
