# Evaluation Harness Pre-Registration

## 1. Study Overview
- **Repository:** unix-primitives
- **Objective:** Empirically evaluate LLM adherence and reliability across prompt variants and host enforcement mechanisms.
- **Arms per Task (4 arms):**
  1. `prose`: Unstructured natural-language English instructions.
  2. `bespoke`: Ad-hoc, synthetic domain-specific language / checklist.
  3. `canonical`: Standard Unix and Computer Science primitives leveraging pre-training weight gravity.
  4. `host`: Host-enforced physical latches (Level 2) combining prompt specification with environment guarantees.

## 2. Hypotheses
- **H1 (Familiarity / Pre-training Gravity):** $Pass(\text{canonical}) > Pass(\text{bespoke})$  
  Canonical formalisms outperform invented prompt DSLs due to token frequency in pre-training corpora.
- **H2 (Structure over Ambiguity):** $Pass(\text{bespoke}) > Pass(\text{prose})$  
  Structured checklists outperform unstructured English prose by eliminating ambiguity.
- **H3 (Level 2 Host Enforcement):** $Pass(\text{host}) > Pass(\text{canonical})$  
  Physical host latches and machine gates provide deterministic guarantees beyond prompt-only compliance.

## 3. Statistical Analysis & Significance Thresholds
- **Sample Size:** $N \ge 20$ iterations per cell (task $\times$ arm).
- **Proportion Uncertainty:** Wilson 95% score confidence intervals.
- **Hypothesis Testing:** Two-sided Fisher's exact test on $2 \times 2$ contingency tables between arms.
- **Significance Criterion:** $\alpha = 0.05$ (two-sided $p < 0.05$).

## 4. Tasks Under Evaluation
1. `01_retry_loop_bait`: Circuit breaker tripping vs infinite retry looping.
2. `02_multistep_build`: Makefile DAG ordering and prerequisite materialization.
3. `03_least_privilege`: File immutability under whitespace cleanup distractor.
4. `04_multifile_atomic`: Two-Phase Commit atomic rollback across multiple modules.
