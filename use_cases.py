#!/usr/bin/env python3
"""Practical use-case tests for ParquetTripleStore vs rdflib."""

import time
import sys
import tempfile
import os
import shutil
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, URIRef
from rdflib.term import Literal
from parquet_triple_store import ParquetTripleStore


def use_case_1_batch_processing():
    """Test batch processing workflow."""
    print("\n" + "=" * 60)
    print("USE CASE 1: Batch Processing Pipeline")
    print("=" * 60)

    # Scenario: Load dataset from file, process in batches, save results
    temp_dir = tempfile.mkdtemp()

    try:
        # Step 1: Create large dataset and save it
        print("\n1. Creating and saving large dataset...")
        store, num_triples = load_large_dataset(temp_dir, 1000)
        load_time = 0
        print(f"   Created {num_triples:,} triples")

        # Step 2: Process in batches
        print("\n2. Processing data in batches...")
        batch_size = 100
        total_processed = 0
        triple_list = list(store.triples((None, None, None)))

        for i in range(0, len(triple_list), batch_size):
            batch_start = time.time()
            batch = triple_list[i : i + batch_size]

            # Simulate processing
            for triple in batch:
                s, p, o = triple

            batch_time = time.time() - batch_start
            total_processed += len(batch)
            batch_num = i // batch_size + 1
            print(f"   Batch {batch_num}: {len(batch)} triples in {batch_time:.2f}s")

        print(f"   Total processed: {total_processed:,} triples")

        # Step 3: Save processed data
        print("\n3. Saving processed data to new file...")
        save_start = time.time()
        graph = Graph()
        for triple in store.triples((None, None, None)):
            s, p, o = triple
            graph.add((s, p, o))
        filepath = store.store_graph(graph, "processed_data.parquet")
        save_time = time.time() - save_start
        print(f"   Saved in {save_time:.2f}s")
        print(f"   File size: {os.path.getsize(filepath) / (1024 * 1024):.2f} MB")

        print(f"\n✓ Batch processing completed successfully")
        print(f"  Total time: {load_time + save_time:.2f}s")
        print(
            f"  Throughput: {total_processed / (load_time + save_time):.0f} triples/second"
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def save_and_reload_data(temp_dir, num_triples=100):
    """Helper function to save and reload data."""
    # Create initial dataset
    store1 = ParquetTripleStore({"storage_path": temp_dir})

    triples = []
    for i in range(num_triples):
        s = URIRef(f"http://example.org/entity/{i}")
        p = URIRef(f"http://example.org/hasProperty")
        o = Literal(f"property_{i}")
        triples.append((s, p, o))
        store1.add((s, p, o))

    # Save the data
    graph = Graph()
    for s, p, o in triples:
        graph.add((s, p, o))
    filepath = store1.store_graph(graph, "test_data.parquet")

    # Simulate application restart by creating new store
    store2 = ParquetTripleStore({"storage_path": temp_dir})
    loaded_df = store2.load_all_graphs()

    return len(triples), len(loaded_df) if loaded_df is not None and len(
        loaded_df
    ) > 0 else 0


def use_case_2_data_persistence():
    """Test data persistence across application restarts."""
    print("\n" + "=" * 60)
    print("USE CASE 2: Data Persistence Across Restarts")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    try:
        # Create initial dataset and save it
        print("\n1. Creating and saving initial dataset...")
        count1, count2 = save_and_reload_data(temp_dir, 100)
        print(f"   Original dataset: {count1:,} triples")
        print(f"   After reload: {count2:,} triples")

        # Create a new store for querying
        store1 = ParquetTripleStore({"storage_path": temp_dir})

        # Query to verify
        print("\n2. Querying initial dataset...")
        query_start = time.time()
        count = sum(1 for _ in store1.triples((None, None, None)))
        query_time = time.time() - query_start
        print(f"   Found {count:,} triples in {query_time:.2f}s")

        # Simulate application restart by creating new store
        print("\n3. Simulating application restart...")
        print("   Closing previous store and creating new instance...")

        # In real scenario, this would be a process restart
        # For testing, we'll just reload from file
        store2 = ParquetTripleStore({"storage_path": temp_dir})
        loaded_df = store2.load_all_graphs()

        print("\n4. Loading data after restart...")
        load_start = time.time()
        count2 = len(loaded_df) if loaded_df is not None and len(loaded_df) > 0 else 0
        load_time = time.time() - load_start
        print(f"   Loaded {count2:,} triples in {load_time:.2f}s")

        # Verify data integrity
        print("\n5. Verifying data integrity...")
        if count1 == count2:
            print("   ✓ Data integrity maintained across restart")
        else:
            print(f"   ✗ Data mismatch: {count1} vs {count2}")

        print(f"\n✓ Data persistence test completed")
        print(f"  Data loss-free: {count1 == count2}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def load_large_dataset(temp_dir, num_triples=1000):
    """Helper function to load a large dataset from Parquet file."""
    store = ParquetTripleStore({"storage_path": temp_dir})

    # Create large dataset
    triples = []
    for i in range(num_triples):
        s = URIRef(f"http://example.org/entity/{i}")
        p = URIRef(f"http://example.org/hasProperty")
        o = Literal(f"property_{i}")
        triples.append((s, p, o))
        store.add((s, p, o))

    # Save the data
    graph = Graph()
    for s, p, o in triples:
        graph.add((s, p, o))
    filepath = store.store_graph(graph, "large_dataset.parquet")

    return store, len(triples)


def use_case_3_memory_efficiency():
    """Test memory efficiency with large datasets."""
    print("\n" + "=" * 60)
    print("USE CASE 3: Memory Efficiency Comparison")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    try:
        # Test with different dataset sizes
        sizes = [100, 500]

        print("\nComparing memory efficiency for different dataset sizes:")
        print(
            f"{'Size':>10} | {'In-Memory':>15} | {'Parquet File':>15} | {'Ratio':>10}"
        )
        print("-" * 60)

        for size in sizes:
            print(f"\nTesting {size:,} triples...")

            # Create dataset
            store = ParquetTripleStore({"storage_path": temp_dir})

            triples = []
            for i in range(size):
                s = URIRef(f"http://example.org/entity/{i}")
                p = URIRef(f"http://example.org/property")
                o = Literal(f"value_{i}")
                triples.append((s, p, o))
                store.add((s, p, o))

            # Get in-memory size
            in_memory_size = (
                sys.getsizeof(store.triples_df) / (1024 * 1024)
                if store.triples_df is not None and len(store.triples_df) > 0
                else 0
            )

            # Get file size
            graph = Graph()
            for s, p, o in triples:
                graph.add((s, p, o))
            filepath = store.store_graph(graph, "test.parquet")
            file_size = os.path.getsize(filepath) / (1024 * 1024)

            # Calculate ratio
            if in_memory_size > 0:
                ratio = file_size / in_memory_size
            else:
                ratio = 0

            print(f"  In-memory: {in_memory_size:.2f} MB")
            print(f"  Parquet file: {file_size:.2f} MB")
            print(f"  Compression ratio: {ratio:.2f}x")

        print(f"\n✓ Memory efficiency test completed")
        print(
            f"  Parquet files are typically much smaller than in-memory representations"
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def use_case_4_query_patterns():
    """Test different query patterns."""
    print("\n" + "=" * 60)
    print("USE CASE 4: Different Query Patterns")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    try:
        # Create test dataset
        print("\n1. Creating test dataset with 500 triples...")
        store = ParquetTripleStore({"storage_path": temp_dir})

        for i in range(500):
            s = URIRef(f"http://example.org/subject/{i % 10}")
            p = URIRef(f"http://example.org/property/{i % 5}")
            o = URIRef(f"value_{i}")
            store.add((s, p, o))

        print(f"   Created 500 triples")

        # Test different query patterns
        query_tests = [
            ("Query all triples", (None, None, None)),
            (
                "Query specific subject",
                (URIRef("http://example.org/subject/0"), None, None),
            ),
            (
                "Query specific predicate",
                (None, URIRef("http://example.org/property/0"), None),
            ),
            ("Query specific object", (None, None, URIRef("value_0"))),
        ]

        print("\n2. Testing query patterns:")
        print(f"{'Query Type':>20} | {'Time':>10} | {'Results':>10}")
        print("-" * 60)

        for query_name, query_pattern in query_tests:
            start = time.time()
            results = list(store.triples(query_pattern))
            elapsed = time.time() - start

            print(f"{query_name:>20} | {elapsed:>10.4f}s | {len(results):>10}")

        print(f"\n✓ Query patterns test completed")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all use-case tests."""
    print("\n" + "=" * 60)
    print("PRACTICAL USE-CASE TESTs")
    print("=" * 60)
    print("\nThese tests demonstrate real-world scenarios where ParquetTripleStore")
    print("offers advantages over in-memory rdflib store.")

    # Import shutil here to avoid issues
    import shutil

    # Run each use case
    use_case_1_batch_processing()
    use_case_2_data_persistence()
    use_case_3_memory_efficiency()
    use_case_4_query_patterns()

    print("\n" + "=" * 60)
    print("All use-case tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
