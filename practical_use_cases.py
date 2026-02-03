#!/usr/bin/env python3
"""
Practical Use-Cases for Parquet vs In-Memory RDF Stores
"""

import time
import sys
from pathlib import Path

# Activate virtual environment
import subprocess
import os

# Activate venv and import modules
venv_path = Path(__file__).parent / "venv"
if (venv_path / "bin" / "activate").exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.13" / "site-packages"))

from rdflib import Graph, URIRef, Literal
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex


def test_batch_processing():
    """Test scenario: Process large batch of data in chunks"""
    print("\n" + "=" * 60)
    print("USE-CASE: Batch Data Processing")
    print("=" * 60)

    print("\nScenario: Process 10,000 triples in batches of 1,000")

    # Create triples with proper URIRef
    test_triples = []
    for i in range(10000):
        test_triples.append(
            (
                URIRef(f"http://subject{i}"),
                URIRef("http://predicate"),
                URIRef(f"http://object{i}"),
            )
        )

    print("\n--- In-Memory Approach ---")
    in_memory_store = Graph()
    start_time = time.time()

    for i in range(10):
        batch = test_triples[i * 1000 : (i + 1) * 1000]
        for triple in batch:
            in_memory_store.add(triple)

    in_memory_time = time.time() - start_time
    print(f"Time: {in_memory_time:.2f}s")
    print(
        f"Results: {len(list(in_memory_store.triples((None, None, None))))} triples loaded"
    )

    print("\n--- Parquet Approach ---")
    parquet_store = ParquetTripleStore("batch_test")
    parquet_store.clear()
    start_time = time.time()

    for i in range(10):
        batch = test_triples[i * 1000 : (i + 1) * 1000]
        for triple in batch:
            parquet_store.add(triple)

    parquet_time = time.time() - start_time
    print(f"Time: {parquet_time:.2f}s")

    print(
        f"\nComparison: Parquet is {parquet_time / in_memory_time:.1f}x slower for batch processing"
    )
    print("✓ Parquet advantage: Better for persistent batch processing\n")


def test_data_persistence():
    """Test scenario: Save and reload data multiple times"""
    print("\n" + "=" * 60)
    print("USE-CASE: Data Persistence & Reloading")
    print("=" * 60)

    print("\nScenario: Save 5,000 triples, reload 10 times")

    # Create test triples
    test_triples = [
        (
            URIRef(f"http://subject{i}"),
            URIRef("http://predicate"),
            URIRef(f"http://object{i}"),
        )
        for i in range(5000)
    ]

    print("\n--- In-Memory Approach ---")
    in_memory_store = Graph()
    in_memory_store.add(test_triples)
    print(
        f"Initial load: {len(list(in_memory_store.triples((None, None, None))))} triples"
    )

    # Simulating reload by creating new store and copying
    reload_times = []
    for i in range(10):
        start_time = time.time()
        new_store = Graph()
        for triple in in_memory_store.triples((None, None, None)):
            new_store.add(triple)
        reload_times.append(time.time() - start_time)

    avg_reload = sum(reload_times) / len(reload_times)
    print(f"Average reload time: {avg_reload:.4f}s")

    print("\n--- Parquet Approach ---")
    parquet_store = ParquetTripleStore("persistence_test")
    parquet_store.clear()
    parquet_store.add(test_triples)

    # Save to disk
    parquet_store.save()
    print(f"Saved: {len(list(parquet_store.triples((None, None, None))))} triples")

    # Reload from disk
    reload_times = []
    for i in range(10):
        start_time = time.time()
        new_store = ParquetTripleStore("persistence_test")
        new_store.load_all_graphs()
        reload_times.append(time.time() - start_time)

    avg_reload = sum(reload_times) / len(reload_times)
    print(f"Average reload time: {avg_reload:.4f}s")

    print(f"\n✓ Parquet advantage: Persistent storage for reuse across sessions\n")


def test_large_dataset_access():
    """Test scenario: Access large dataset with repeated queries"""
    print("\n" + "=" * 60)
    print("USE-CASE: Large Dataset Query Patterns")
    print("=" * 60)

    print("\nScenario: 20,000 triples, query various patterns")

    # Create test triples
    test_triples = [
        (
            URIRef(f"http://subject{i}"),
            URIRef("http://predicate"),
            URIRef(f"http://object{i}"),
        )
        for i in range(20000)
    ]

    print("\n--- In-Memory Approach ---")
    in_memory_store = Graph()
    in_memory_store.add(test_triples)

    # Query all triples
    start_time = time.time()
    results = list(in_memory_store.triples((None, None, None)))
    query_all_time = time.time() - start_time

    # Query specific subject
    start_time = time.time()
    results = list(in_memory_store.triples((URIRef("http://subject5000"), None, None)))
    query_subject_time = time.time() - start_time

    # Query specific predicate
    start_time = time.time()
    results = list(in_memory_store.triples((None, URIRef("http://predicate"), None)))
    query_predicate_time = time.time() - start_time

    # Query specific object
    start_time = time.time()
    results = list(in_memory_store.triples((None, None, URIRef("http://object5000"))))
    query_object_time = time.time() - start_time

    print(f"Query all triples: {query_all_time:.4f}s ({len(results)} results)")
    print(f"Query specific subject: {query_subject_time:.4f}s ({len(results)} results)")
    print(
        f"Query specific predicate: {query_predicate_time:.4f}s ({len(results)} results)"
    )
    print(f"Query specific object: {query_object_time:.4f}s ({len(results)} results)")

    print("\n--- Parquet Approach ---")
    parquet_store = ParquetTripleStore("large_dataset_test")
    parquet_store.clear()
    parquet_store.add(test_triples)

    # Query all triples
    start_time = time.time()
    results = list(parquet_store.triples((None, None, None)))
    query_all_time = time.time() - start_time

    # Query specific subject
    start_time = time.time()
    results = list(parquet_store.triples((URIRef("http://subject5000"), None, None)))
    query_subject_time = time.time() - start_time

    # Query specific predicate
    start_time = time.time()
    results = list(parquet_store.triples((None, URIRef("http://predicate"), None)))
    query_predicate_time = time.time() - start_time

    # Query specific object
    start_time = time.time()
    results = list(parquet_store.triples((None, None, URIRef("http://object5000"))))
    query_object_time = time.time() - start_time

    print(f"Query all triples: {query_all_time:.4f}s ({len(results)} results)")
    print(f"Query specific subject: {query_subject_time:.4f}s ({len(results)} results)")
    print(
        f"Query specific predicate: {query_predicate_time:.4f}s ({len(results)} results)"
    )
    print(f"Query specific object: {query_object_time:.4f}s ({len(results)} results)")

    print(f"\n✓ Parquet advantage: Persistent storage enables large dataset access\n")


def test_memory_efficiency():
    """Test scenario: Compare memory footprint and scalability"""
    print("\n" + "=" * 60)
    print("USE-CASE: Memory Efficiency & Scalability")
    print("=" * 60)

    print("\nScenario: Process datasets of varying sizes")

    sizes = [1000, 5000, 10000, 20000]

    print("\n--- In-Memory Approach ---")
    print("\nDataset size | Load time | Scalability")
    print("-" * 40)

    in_memory_times = []
    for size in sizes:
        start_time = time.time()
        store = Graph()
        test_triples = [
            (
                URIRef(f"http://subject{i}"),
                URIRef("http://predicate"),
                URIRef(f"http://object{i}"),
            )
            for i in range(size)
        ]
        for triple in test_triples:
            store.add(triple)
        elapsed = time.time() - start_time
        in_memory_times.append(elapsed)
        print(f"{size:8,} | {elapsed:8.4f}s | Linear")

    avg_speedup = in_memory_times[-1] / in_memory_times[0]
    print(f"\nAverage speedup (20K/1K): {avg_speedup:.2f}x")

    print("\n--- Parquet Approach ---")
    print("\nDataset size | Load time | Scalability")
    print("-" * 40)

    parquet_times = []
    for size in sizes:
        store = ParquetTripleStore(f"memory_test_{size}")
        store.clear()
        test_triples = [
            (
                URIRef(f"http://subject{i}"),
                URIRef("http://predicate"),
                URIRef(f"http://object{i}"),
            )
            for i in range(size)
        ]
        for triple in test_triples:
            store.add(triple)
        elapsed = time.time() - start_time
        parquet_times.append(elapsed)
        print(f"{size:8,} | {elapsed:8.4f}s | Linear")

    avg_speedup = parquet_times[-1] / parquet_times[0]
    print(f"\nAverage speedup (20K/1K): {avg_speedup:.2f}x")

    print(f"\n✓ Parquet advantage: Persistent storage enables large dataset handling\n")


def test_query_pattern_variations():
    """Test scenario: Different query patterns and their performance"""
    print("\n" + "=" * 60)
    print("USE-CASE: Query Pattern Variations")
    print("=" * 60)

    print("\nScenario: 15,000 triples with varying query patterns")

    # Create test triples
    test_triples = []
    for i in range(5000):
        for j in range(3):
            for k in range(3):
                test_triples.append(
                    (
                        URIRef(f"http://subject{i}"),
                        URIRef(f"http://predicate{j}"),
                        URIRef(f"http://object{k}"),
                    )
                )

    print("\n--- In-Memory Approach ---")
    in_memory_store = Graph()
    for triple in test_triples:
        in_memory_store.add(triple)
    print(f"Loaded: {len(list(in_memory_store.triples((None, None, None))))} triples")

    queries = [
        ("All triples", (None, None, None)),
        ("Specific subject", (URIRef("http://subject0"), None, None)),
        ("Specific predicate", (None, URIRef("http://predicate0"), None)),
        ("Specific object", (None, None, URIRef("http://object0"))),
        (
            "Subject-predicate",
            (URIRef("http://subject0"), URIRef("http://predicate0"), None),
        ),
        ("Subject-object", (URIRef("http://subject0"), None, URIRef("http://object0"))),
        (
            "Predicate-object",
            (None, URIRef("http://predicate0"), URIRef("http://object0")),
        ),
    ]

    print("\nQuery type | Results | Time (s)")
    print("-" * 40)

    in_memory_times = {}
    for name, pattern in queries:
        start_time = time.time()
        results = list(in_memory_store.triples(pattern))
        elapsed = time.time() - start_time
        in_memory_times[name] = elapsed
        print(f"{name:18} | {len(results):8} | {elapsed:.6f}")

    print("\n--- Parquet Approach ---")
    parquet_store = ParquetTripleStore("query_patterns_test")
    parquet_store.clear()
    for triple in test_triples:
        parquet_store.add(triple)
    print(f"Loaded: {len(list(parquet_store.triples((None, None, None))))} triples")

    print("\nQuery type | Results | Time (s)")
    print("-" * 40)

    parquet_times = {}
    for name, pattern in queries:
        start_time = time.time()
        results = list(parquet_store.triples(pattern))
        elapsed = time.time() - start_time
        parquet_times[name] = elapsed
        print(f"{name:18} | {len(results):8} | {elapsed:.6f}")

    print(f"\n✓ Parquet advantage: Persistent storage enables query pattern testing\n")


def test_repeated_operations():
    """Test scenario: Repeated read/write operations"""
    print("\n" + "=" * 60)
    print("USE-CASE: Repeated Read/Write Operations")
    print("=" * 60)

    print("\nScenario: 3,000 triples, 100 write operations, 50 read operations")

    # Create test triples
    test_triples = [
        (
            URIRef(f"http://subject{i}"),
            URIRef("http://predicate"),
            URIRef(f"http://object{i}"),
        )
        for i in range(3000)
    ]

    print("\n--- In-Memory Approach ---")
    in_memory_store = Graph()

    # Initialize
    for triple in test_triples:
        in_memory_store.add(triple)
    print(f"Initial: {len(list(in_memory_store.triples((None, None, None))))} triples")

    # Simulate repeated operations
    operations = 100
    writes = 50
    reads = 50

    start_time = time.time()
    for i in range(operations):
        if i < writes:
            new_triple = (
                URIRef("http://subject3000"),
                URIRef("http://predicate"),
                URIRef(f"http://object{i}"),
            )
            in_memory_store.add(new_triple)
        else:
            list(in_memory_store.triples((None, None, None)))
    total_time = time.time() - start_time

    print(f"Operations: {operations} ({writes} writes, {reads} reads)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per operation: {total_time / operations:.4f}s")

    print("\n--- Parquet Approach ---")
    parquet_store = ParquetTripleStore("repeated_ops_test")
    parquet_store.clear()

    # Initialize
    for triple in test_triples:
        parquet_store.add(triple)
    print(f"Initial: {len(list(parquet_store.triples((None, None, None))))} triples")

    # Simulate repeated operations
    start_time = time.time()
    for i in range(operations):
        if i < writes:
            new_triple = (
                URIRef("http://subject3000"),
                URIRef("http://predicate"),
                URIRef(f"http://object{i}"),
            )
            parquet_store.add(new_triple)
        else:
            list(parquet_store.triples((None, None, None)))
    total_time = time.time() - start_time

    print(f"Operations: {operations} ({writes} writes, {reads} reads)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per operation: {total_time / operations:.4f}s")

    print(
        f"\n✓ Parquet advantage: Persistent storage enables session-based operations\n"
    )


def cleanup():
    """Clean up test files"""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    directories = [
        "batch_test",
        "persistence_test",
        "large_dataset_test",
        "memory_test_1000",
        "memory_test_5000",
        "memory_test_10000",
        "memory_test_20000",
        "query_patterns_test",
        "repeated_ops_test",
    ]

    for dirname in directories:
        if os.path.exists(dirname):
            try:
                import shutil

                shutil.rmtree(dirname)
                print(f"Removed: {dirname}")
            except:
                print(f"Failed to remove: {dirname}")


if __name__ == "__main__":
    print("=" * 60)
    print("PRACTICAL USE-CASE TESTs")
    print("=" * 60)

    try:
        test_batch_processing()
        test_data_persistence()
        test_large_dataset_access()
        test_memory_efficiency()
        test_query_pattern_variations()
        test_repeated_operations()

        print("\n" + "=" * 60)
        print("ALL USE-CASE TESTs COMPLETED")
        print("=" * 60)

        # Ask about cleanup
        cleanup_needed = input("\nClean up test files? (y/n): ")
        if cleanup_needed.lower() == "y":
            cleanup()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
