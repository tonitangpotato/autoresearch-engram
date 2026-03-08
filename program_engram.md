# autoresearch + Engram 🧠

This extends the standard autoresearch `program.md` with **cognitive memory** powered by [Engram](https://github.com/tonitangpotato/engram-ai) — a neuroscience-grounded memory system using ACT-R activation, Hebbian learning, and Ebbinghaus forgetting curves.

## Why Memory Matters

Without memory, autoresearch has a fundamental limitation: **the agent forgets everything between sessions**. It might retry experiments that already failed, miss patterns across runs, or fail to build on successful strategies.

With Engram, the agent:
- **Remembers what worked** — successful experiment patterns get reinforced (Hebbian learning)
- **Forgets what didn't** — failed approaches naturally decay (Ebbinghaus forgetting curves)
- **Builds intuition** — cross-experiment patterns emerge via ACT-R activation
- **Never repeats mistakes** — failed experiments are recalled before being tried again

## Setup

All standard autoresearch setup applies (see `program.md`). Additionally:

1. **Install Engram**: `pip install engramai`
2. **Initialize memory**: The agent will auto-create `autoresearch_memory.db` on first run.

## Memory-Enhanced Experiment Loop

LOOP FOREVER:

### 1. RECALL — Before choosing an experiment
Before deciding what to try, query Engram for relevant memories:

```bash
# What worked before?
neuromem recall "successful experiments that improved val_bpb" --top 5

# What failed?
neuromem recall "failed experiments crashes OOM" --top 5

# What patterns exist?
neuromem recall "patterns in hyperparameter changes" --top 3
```

Use these memories to **inform your next experiment choice**. Don't repeat what failed. Build on what worked. Look for unexplored combinations of successful changes.

### 2. HYPOTHESIZE — Form a theory
Based on recalled memories and the current results.tsv, form a specific hypothesis:
- "Increasing width worked (+0.003), increasing depth worked (+0.002), maybe both together will compound"
- "All optimizer changes have failed — focus on architecture instead"

### 3. IMPLEMENT — Modify train.py
Same as standard autoresearch: edit train.py, git commit.

### 4. RUN — Execute the experiment
```bash
uv run train.py > run.log 2>&1
```

### 5. ANALYZE — Check results
```bash
grep "^val_bpb:\|^peak_vram_mb:" run.log
```

### 6. STORE — Save to Engram memory
After every experiment (success, failure, or crash), store the result:

```bash
# For successful experiments (val_bpb improved)
neuromem add "KEEP: [description]. val_bpb went from [old] to [new] (improvement: [delta]). Key change: [what was modified]. Hypothesis: [why it worked]." --type episodic --importance 0.8

# For failed experiments (val_bpb worse or equal)
neuromem add "DISCARD: [description]. val_bpb went from [old] to [new] (regression: [delta]). Key change: [what was modified]. Hypothesis: [why it failed]." --type episodic --importance 0.4

# For crashes
neuromem add "CRASH: [description]. Error: [error type]. Key change: [what was modified]. Lesson: [what to avoid]." --type episodic --importance 0.6

# For emerging patterns (every 10 experiments)
neuromem add "PATTERN: After [N] experiments, observed that [pattern]. Confidence: [high/medium/low]." --type semantic --importance 0.9
```

### 7. DECIDE — Keep or discard
Same as standard autoresearch:
- Improved → keep the commit, advance the branch
- Not improved → git reset

### 8. REFLECT — Every 10 experiments
Every 10 experiments, do a reflection step:

```bash
# Recall all experiments
neuromem recall "experiment results" --top 20

# Store a meta-pattern
neuromem add "REFLECTION after [N] experiments: Best val_bpb so far: [X]. Most effective category of changes: [Y]. Least effective: [Z]. Unexplored directions: [W]." --type semantic --importance 0.95
```

Then continue the loop.

## Memory Categories

The agent naturally builds these memory types:

| Type | Examples | Decay Rate |
|------|----------|------------|
| **Episodic** | "Experiment #23: doubled width → OOM crash" | Normal (forgets old failures) |
| **Semantic** | "Architecture changes are more impactful than optimizer tweaks" | Slow (retains patterns) |
| **Procedural** | "Always check VRAM before doubling model size" | Very slow (retains lessons) |

## What This Enables

1. **Cross-session continuity** — Stop and restart anytime. The agent picks up where it left off with full context.
2. **Faster convergence** — No time wasted on approaches that already failed.
3. **Emergent research strategy** — The agent develops intuition about what works over hundreds of experiments.
4. **Collaborative research** — Multiple agents can share the same Engram DB, building on each other's discoveries.
5. **Research archaeology** — Query the memory months later: "What was the best architecture change ever found?"

## Compatibility

This is a **drop-in enhancement** — the standard `program.md` experiment loop still works identically. Engram adds a recall step before and a store step after each experiment. If Engram is not installed, the agent falls back to results.tsv only.
