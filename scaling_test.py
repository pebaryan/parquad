#!/usr/bin/env python3
"""Test performance scaling with larger datasets."""

import time
import sys
import shutil
from pathlib import Path

# Activate virtual environment
import subprocess
import os

# Activate venv and import modules
venv_path = Path(__file__).parent / "venv"
if (venv_path / "bin" / "activate").exists():
    source_activate = f"source {venv_path}/bin/activate && "
    sys.path.insert(0, str(venv_path / "lib" / "python3.13" / "site-packages"))

from rdflib import Graph
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex
from rdflib import URIRef, Literal


def create_test_triples(count):
    """Create test triples for benchmarking."""
    triples = []
    for i in range(count):
        s = URIRef(f"http://example.org/subject/{i}")
        p = URIRef(f"http://example.org/property/{i % 10}")
        o = URIRef(f"http://example.org/object/{i}")
        triples.append((s, p, o))
    return triples


def benchmark_in_memory(count):
    """Benchmark rdflib in-memory store."""
    print(f"\n{'=' * 60}")
    print(f"In-Memory (rdflib) Benchmark: {count:,} triples")
    print("=" * 60)

    g = Graph()
    start = time.time()

    triples = create_test_triples(count)
    for s, p, o in triples:
        g.add((s, p, o))

    elapsed = time.time() - start
    print(f"Add operation: {elapsed:.4f}s")

    # Query performance
    start = time.time()
    results = list(g.triples((None, None, None)))
    elapsed = time.time() - start
    print(f"Query all triples: {elapsed:.4f}s ({len(results):,} results)")

    # Query specific subject
    start = time.time()
    results = list(g.triples((URIRef(f"http://example.org/subject/0"), None, None)))
    elapsed = time.time() - start
    print(f"Query specific subject: {elapsed:.4f}s ({len(results):,} results)")

    return elapsed


def benchmark_parquet(count, temp_dir):
    """Benchmark ParquetTripleStore."""
    print(f"\n{'=' * 60}")
    print(f"Parquet (Persistent) Benchmark: {count:,} triples")
    print("=" * 60)

    # Test adding
    store = ParquetTripleStore({"storage_path": temp_dir})
    start = time.time()

    triples = create_test_triples(count)
    for s, p, o in triples:
        store.add((s, p, o))

    elapsed = time.time() - start
    print(f"Add operation: {elapsed:.4f}s")

    # Query performance
    start = time.time()
    result_count = 0
    for _ in store.triples((None, None, None)):
        result_count += 1
    elapsed = time.time() - start
    print(f"Query all triples: {elapsed:.4f}s ({result_count:,} results)")

    # Query specific subject
    start = time.time()
    subject_count = 0
    for _ in store.triples((URIRef(f"http://example.org/subject/0"), None, None)):
        subject_count += 1
    elapsed = time.time() - start
    print(f"Query specific subject: {elapsed:.4f}s ({subject_count:,} results)")

    return elapsed


def main():
    """Run scaling benchmarks."""
    import tempfile
    import os

    sizes = [100, 1000, 5000, 10000]

    print("\n" + "=" * 60)
    print("PERFORMANCE SCALING TEST")
    print("=" * 60)

    results = {}

    for size in sizes:
        print(f"\n{'#' * 60}")
        print(f"# Dataset size: {size:,} triples")
        print(f"{'#' * 60}")

        temp_dir = None
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()

            # Test in-memory
            mem_time = benchmark_in_memory(size)

            # Test Parquet
            parquet_time = benchmark_parquet(size, temp_dir)

            # Calculate speedup
            speedup = parquet_time / mem_time if mem_time > 0 else 0

            results[size] = {
                "memory": mem_time,
                "parquet": parquet_time,
                "speedup": speedup,
            }

            print(f"\nSpeedup (Parquet/InMemory): {speedup:.2f}x")
            print(f"Parquet is {speedup:.2f}x slower")

        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Size':>10} | {'Memory':>12} | {'Parquet':>12} | {'Speedup':>10}")
    print("-" * 60)

    for size, res in results.items():
        print(
            f"{size:>10,} | {res['memory']:>12.4f} | {res['parquet']:>12.4f} | {res['speedup']:>10.2f}x"
        )

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    # Check if speedup scales
    initial_speedup = results[100]["speedup"]
    final_speedup = results[10000]["speedup"]

    if final_speedup > initial_speedup * 2:
        print("\n⚠️ Performance gap EXPANDS with dataset size")
        print("Parquet may offer advantages at larger scales")
    elif final_speedup < initial_speedup / 2:
        print("\n⚠️ Performance gap SHRINKS with dataset size")
        print("In-memory store remains significantly faster")
    else:
        print("\n✓️ Performance gap remains relatively constant")
        print("In-memory store is consistently faster")

    print("\nRecommendations:")
    print("• Use Parquet for: Large, persistent datasets")
    print("• Use In-Memory for: Small, frequently accessed datasets")
    print("• Consider hybrid: In-memory for hot data, Parquet for cold data")


if __name__ == "__main__":
    main()
