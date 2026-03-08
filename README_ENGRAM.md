# autoresearch + Engram 🧠

> **Give your autonomous research agent a brain that remembers.**

This is a fork of [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) enhanced with [Engram](https://github.com/tonitangpotato/engram-ai) — a neuroscience-grounded memory system.

## The Problem

autoresearch is brilliant: an AI agent runs ML experiments autonomously while you sleep. But it has a fundamental limitation — **the agent has no long-term memory**. It records results in a TSV file, but can't:

- Remember *why* an experiment worked or failed
- Recognize patterns across dozens of experiments  
- Avoid repeating approaches that already crashed
- Build intuition about what directions are promising
- Continue intelligently after a session restart

## The Solution

Engram adds **cognitive memory** using real neuroscience models:

| Mechanism | What It Does | Research Basis |
|-----------|-------------|---------------|
| **ACT-R Activation** | Successful patterns float to the top naturally | Anderson (1993) |
| **Hebbian Learning** | Co-occurring successful changes get linked | Hebb (1949) |
| **Ebbinghaus Forgetting** | Failed experiments fade away over time | Ebbinghaus (1885) |
| **Memory Consolidation** | Raw results → stable patterns | Born & Diekelmann (2010) |

## Quick Start

```bash
# Standard autoresearch setup
uv sync
uv run prepare.py

# Add Engram
pip install engramai

# Use the enhanced program
# Point your AI agent to program_engram.md instead of program.md
```

Or use the Python wrapper directly:

```bash
# Before each experiment — what should I try?
python engram_wrapper.py recall

# After each experiment — store the result
python engram_wrapper.py store --status keep --val_bpb 0.993 --prev_bpb 0.997 --description "increased LR to 0.04"

# Every 10 experiments — find patterns
python engram_wrapper.py reflect

# Need ideas? — get memory-informed suggestions
python engram_wrapper.py suggest
```

## What Changes

The experiment loop stays identical. Engram adds two steps:

```diff
  LOOP FOREVER:
+   1. RECALL — query Engram: what worked? what failed? what patterns?
    2. Choose an experiment idea (now informed by memory)
    3. Modify train.py, git commit
    4. Run: uv run train.py > run.log 2>&1
    5. Check results
+   6. STORE — save result + context to Engram
    7. Keep or discard
+   8. REFLECT — every 10 experiments, analyze patterns
```

## Example Memory Evolution

**After 10 experiments:**
```
🧠 Recall:
  💡 What worked: "LR increase to 0.04 improved by 0.004"
  ⚠️  What failed: "GeLU activation made things worse"
  🚫 Avoid: activation, gelu, swish
```

**After 50 experiments:**
```
🧠 Recall:
  🧬 Pattern: "Architecture changes (width/depth) are 3x more effective than optimizer tweaks"
  🧬 Pattern: "Combining 2 successful changes usually works, combining 3+ usually crashes"
  💡 Best direction: "Try rotary embeddings — attention hasn't been explored yet"
```

**After 100 experiments:**
```
🧠 Recall:
  🧬 Stable pattern (high confidence): "Optimal model for 5-min budget is ~60M params, 10 layers, width 768"
  🧬 Stable pattern: "Muon optimizer consistently beats AdamW by 0.002-0.005 val_bpb"
  💡 Unexplored: "No experiments on data ordering, curriculum learning, or mixed precision"
```

The agent develops **research intuition** — exactly like a human researcher does over months of work.

## Architecture

```
autoresearch (Karpathy)
├── prepare.py     — data prep (unchanged)
├── train.py       — model code (agent modifies)
├── program.md     — original agent instructions
│
└── + Engram enhancement
    ├── program_engram.md    — enhanced instructions with memory
    ├── engram_wrapper.py    — Python helper for memory operations
    └── autoresearch_memory.db  — SQLite cognitive memory (auto-created)
```

## Why Neuroscience?

Most "memory" systems for AI agents are just databases with search. Engram models how human researchers actually remember:

- **You don't remember every failed experiment** — unimportant ones fade (Ebbinghaus forgetting)
- **Successful strategies stick** — they get reinforced every time they work (Hebbian learning)
- **You develop intuition** — patterns emerge from hundreds of observations (ACT-R activation)
- **You sleep on it** — raw experiences consolidate into stable knowledge (memory consolidation)

This is exactly what an autonomous research agent needs.

## Production Stats

Engram has been running in production for 30+ days:
- 3,846 memories stored
- 230,103 successful recalls
- 12,510 Hebbian reinforcement links
- ~90ms average recall latency
- $0 API cost (runs locally, no embeddings needed)

## License

MIT (same as autoresearch)

---

Built by [@horseonedragon](https://x.com/horseonedragon) · [Engram on GitHub](https://github.com/tonitangpotato/engram-ai) · [PyPI](https://pypi.org/project/engramai/)
