#!/usr/bin/env python3
"""
engram_wrapper.py — Cognitive memory layer for autoresearch experiments.

Wraps the autoresearch experiment loop with Engram memory:
- Before each experiment: recall what worked/failed
- After each experiment: store the result with context
- Every N experiments: reflect on patterns

Usage:
    python engram_wrapper.py recall          # What should I try next?
    python engram_wrapper.py store --status keep --val_bpb 0.993 --description "increased LR"
    python engram_wrapper.py reflect         # Pattern analysis
    python engram_wrapper.py suggest         # AI-powered experiment suggestion

Requires: pip install engramai
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Try to import Engram
try:
    from engram import Memory
    HAS_ENGRAM = True
except ImportError:
    HAS_ENGRAM = False


DB_PATH = os.environ.get("ENGRAM_DB", "./autoresearch_memory.db")
RESULTS_TSV = "./results.tsv"


def get_memory():
    """Initialize Engram memory client."""
    if not HAS_ENGRAM:
        print("⚠️  Engram not installed. Install with: pip install engramai")
        print("   Falling back to results.tsv only.")
        return None
    return Memory(DB_PATH)


def parse_results_tsv():
    """Parse results.tsv into a list of experiment records."""
    results = []
    tsv_path = Path(RESULTS_TSV)
    if not tsv_path.exists():
        return results
    
    with open(tsv_path) as f:
        lines = f.readlines()
    
    if len(lines) <= 1:  # header only
        return results
    
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if len(parts) >= 5:
            results.append({
                'commit': parts[0],
                'val_bpb': float(parts[1]) if parts[1] != '0.000000' else None,
                'memory_gb': float(parts[2]),
                'status': parts[3],
                'description': parts[4],
            })
    return results


def cmd_recall(args):
    """Recall relevant memories before choosing an experiment."""
    mem = get_memory()
    results = parse_results_tsv()
    
    print("🧠 Recalling experiment memory...\n")
    
    # Show recent results from TSV
    if results:
        print(f"📊 {len(results)} experiments in results.tsv")
        kept = [r for r in results if r['status'] == 'keep']
        discarded = [r for r in results if r['status'] == 'discard']
        crashed = [r for r in results if r['status'] == 'crash']
        
        if kept:
            best = min(kept, key=lambda r: r['val_bpb'] or 999)
            print(f"   ✅ {len(kept)} kept (best: {best['val_bpb']:.6f} — {best['description']})")
        print(f"   ❌ {len(discarded)} discarded, 💥 {len(crashed)} crashed\n")
        
        # Show last 5
        print("   Last 5 experiments:")
        for r in results[-5:]:
            icon = {'keep': '✅', 'discard': '❌', 'crash': '💥'}.get(r['status'], '❓')
            bpb = f"{r['val_bpb']:.6f}" if r['val_bpb'] else "CRASH"
            print(f"   {icon} {bpb} — {r['description']}")
        print()
    
    # Query Engram for deeper patterns
    if mem is not None:
        print("🔍 Querying Engram for patterns...\n")
        
        # Successful patterns
        successes = mem.recall("successful experiments that improved val_bpb", limit=5)
        if successes:
            print("   💡 What worked:")
            for s in successes:
                print(f"      • {s['content'][:120]}")
            print()
        
        # Failed patterns  
        failures = mem.recall("failed experiments that made val_bpb worse", limit=3)
        if failures:
            print("   ⚠️  What didn't work:")
            for f in failures:
                print(f"      • {f['content'][:120]}")
            print()
        
        # Meta-patterns
        patterns = mem.recall("patterns and reflections about research direction", limit=3)
        if patterns:
            print("   🧬 Emerging patterns:")
            for p in patterns:
                print(f"      • {p['content'][:120]}")
            print()
    
    # Suggest what NOT to try
    if results:
        failed_keywords = set()
        for r in results:
            if r['status'] in ('discard', 'crash'):
                for word in r['description'].lower().split():
                    if len(word) > 3:
                        failed_keywords.add(word)
        
        if failed_keywords:
            print(f"   🚫 Avoid themes: {', '.join(list(failed_keywords)[:10])}")


def cmd_store(args):
    """Store an experiment result in Engram memory."""
    mem = get_memory()
    if mem is None:
        print("Engram not available. Result recorded in results.tsv only.")
        return
    
    status = args.status.upper()
    val_bpb = args.val_bpb
    description = args.description
    prev_bpb = args.prev_bpb
    
    # Calculate delta
    delta_str = ""
    if prev_bpb and val_bpb:
        delta = prev_bpb - val_bpb
        direction = "improvement" if delta > 0 else "regression"
        delta_str = f" ({direction}: {abs(delta):.6f})"
    
    # Determine importance based on status and magnitude
    if status == "KEEP":
        importance = 0.8
        if prev_bpb and val_bpb and (prev_bpb - val_bpb) > 0.005:
            importance = 0.95  # Big improvement
        memory_text = f"KEEP: {description}. val_bpb: {val_bpb:.6f}{delta_str}."
        memory_type = "episodic"
    elif status == "CRASH":
        importance = 0.6
        memory_text = f"CRASH: {description}. Error encountered."
        memory_type = "episodic"
    else:  # DISCARD
        importance = 0.4
        memory_text = f"DISCARD: {description}. val_bpb: {val_bpb:.6f}{delta_str}."
        memory_type = "episodic"
    
    mem.add(memory_text, type=memory_type, importance=importance)
    print(f"🧠 Stored in Engram: {memory_text[:80]}...")


def cmd_reflect(args):
    """Periodic reflection — analyze patterns across all experiments."""
    mem = get_memory()
    results = parse_results_tsv()
    
    if not results:
        print("No experiments to reflect on yet.")
        return
    
    n = len(results)
    kept = [r for r in results if r['status'] == 'keep' and r['val_bpb']]
    discarded = [r for r in results if r['status'] == 'discard']
    crashed = [r for r in results if r['status'] == 'crash']
    
    print(f"🔬 Reflection after {n} experiments\n")
    print(f"   Success rate: {len(kept)}/{n} ({100*len(kept)/n:.0f}%)")
    
    if kept:
        best = min(kept, key=lambda r: r['val_bpb'])
        worst_kept = max(kept, key=lambda r: r['val_bpb'])
        print(f"   Best val_bpb: {best['val_bpb']:.6f} ({best['description']})")
        print(f"   Range of kept: {best['val_bpb']:.6f} — {worst_kept['val_bpb']:.6f}")
    
    # Categorize experiments
    categories = {}
    for r in results:
        desc_lower = r['description'].lower()
        category = "other"
        if any(w in desc_lower for w in ['lr', 'learning rate', 'warmup', 'schedule']):
            category = "learning_rate"
        elif any(w in desc_lower for w in ['width', 'depth', 'heads', 'embed', 'dim', 'layer']):
            category = "architecture"
        elif any(w in desc_lower for w in ['optimizer', 'adam', 'muon', 'momentum', 'weight decay']):
            category = "optimizer"
        elif any(w in desc_lower for w in ['batch', 'gradient', 'accumulation']):
            category = "batch_size"
        elif any(w in desc_lower for w in ['dropout', 'norm', 'regulariz']):
            category = "regularization"
        elif any(w in desc_lower for w in ['attention', 'flash', 'rope', 'position']):
            category = "attention"
        
        if category not in categories:
            categories[category] = {'keep': 0, 'discard': 0, 'crash': 0}
        categories[category][r['status']] += 1
    
    print(f"\n   📊 Category breakdown:")
    for cat, counts in sorted(categories.items(), key=lambda x: sum(x[1].values()), reverse=True):
        total = sum(counts.values())
        success = counts.get('keep', 0)
        print(f"      {cat}: {success}/{total} succeeded ({100*success/total:.0f}%)")
    
    # Store reflection in Engram
    if mem is not None:
        reflection = (
            f"REFLECTION after {n} experiments: "
            f"Best val_bpb: {best['val_bpb']:.6f} ({best['description']}). "
            f"Success rate: {len(kept)}/{n} ({100*len(kept)/n:.0f}%). "
            f"Most effective category: {max(categories.items(), key=lambda x: x[1].get('keep', 0))[0]}. "
            f"Least effective: {min(categories.items(), key=lambda x: x[1].get('keep', 0))[0]}."
        )
        mem.add(reflection, type="semantic", importance=0.95)
        print(f"\n   🧠 Reflection stored in Engram")


def cmd_suggest(args):
    """Suggest next experiment based on memory."""
    mem = get_memory()
    results = parse_results_tsv()
    
    if not results:
        print("💡 No previous experiments. Start with the baseline: uv run train.py")
        return
    
    print("💡 Experiment suggestion based on memory:\n")
    
    # Analyze what's been tried
    kept = [r for r in results if r['status'] == 'keep' and r['val_bpb']]
    discarded = [r for r in results if r['status'] == 'discard']
    
    # Find the most successful category
    kept_descriptions = ' '.join(r['description'].lower() for r in kept)
    discarded_descriptions = ' '.join(r['description'].lower() for r in discarded)
    
    suggestions = []
    
    # If architecture changes worked, suggest combinations
    if 'width' in kept_descriptions or 'depth' in kept_descriptions:
        suggestions.append("Architecture changes have worked. Try combining: width + depth, or add skip connections.")
    
    # If LR changes worked, suggest finer tuning
    if 'lr' in kept_descriptions or 'learning rate' in kept_descriptions:
        suggestions.append("LR changes helped. Try cosine annealing or warmup + decay schedule.")
    
    # If nothing about attention has been tried
    if 'attention' not in kept_descriptions and 'attention' not in discarded_descriptions:
        suggestions.append("Attention mechanism hasn't been explored. Try multi-query attention or rotary embeddings.")
    
    # General suggestions
    if len(kept) > 5:
        suggestions.append(f"You have {len(kept)} successful changes. Try combining the top 2-3 in one experiment.")
    
    if len(discarded) > len(kept) * 2:
        suggestions.append("High failure rate. Consider smaller, more conservative changes.")
    
    # Query Engram for additional context
    if mem is not None:
        patterns = mem.recall("most effective experiment changes", limit=3)
        if patterns:
            suggestions.append(f"Engram pattern: {patterns[0]['content'][:100]}")
    
    for i, s in enumerate(suggestions, 1):
        print(f"   {i}. {s}")
    
    if not suggestions:
        print("   Try something radical — change the architecture fundamentally.")


def main():
    parser = argparse.ArgumentParser(
        description="Engram memory wrapper for autoresearch experiments"
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # recall
    subparsers.add_parser("recall", help="Recall memories before choosing an experiment")
    
    # store
    store_parser = subparsers.add_parser("store", help="Store an experiment result")
    store_parser.add_argument("--status", required=True, choices=["keep", "discard", "crash"])
    store_parser.add_argument("--val_bpb", type=float, default=0.0)
    store_parser.add_argument("--prev_bpb", type=float, default=None)
    store_parser.add_argument("--description", required=True)
    
    # reflect
    subparsers.add_parser("reflect", help="Periodic reflection on experiment patterns")
    
    # suggest
    subparsers.add_parser("suggest", help="Suggest next experiment based on memory")
    
    args = parser.parse_args()
    
    if args.command == "recall":
        cmd_recall(args)
    elif args.command == "store":
        cmd_store(args)
    elif args.command == "reflect":
        cmd_reflect(args)
    elif args.command == "suggest":
        cmd_suggest(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
