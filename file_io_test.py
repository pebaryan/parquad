#!/usr/bin/env python3
"""Test file I/O operations and storage efficiency."""

import time
import sys
import shutil
import os
import tempfile
from pathlib import Path

# Activate virtual environment
import venv

sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, URIRef
from parquet_triple_store import ParquetTripleStore
import pandas as pd


def create_test_graph(count):
    """Create test graph with RDF triples."""
    graph = Graph()
    for i in range(count):
        s = URIRef(f"http://example.org/subject/{i}")
        p = URIRef(f"http://example.org/property/{i % 10}")
        o = URIRef(f"http://example.org/object/{i}")
        graph.add((s, p, o))
    return graph


def benchmark_file_operations(count, temp_dir):
    """Benchmark file I/O operations."""
    print(f"\n{'=' * 60}")
    print(f"File I/O Operations: {count:,} triples")
    print("=" * 60)

    # Test 1: Store to file
    print(f"\nTest 1: Store graph to Parquet file")
    graph = create_test_graph(count)

    start = time.time()
    store = ParquetTripleStore({"storage_path": temp_dir})
    filename = f"test_data_{count}.parquet"
    filepath = store.store_graph(graph, filename)
    store_time = time.time() - start

    # Get file size
    file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB

    print(f"  Time: {store_time:.4f}s")
    print(f"  File size: {file_size:.2f} MB")
    print(f"  File path: {filepath}")

    # Test 2: Load from file
    print(f"\nTest 2: Load graph from Parquet file")

    start = time.time()
    loaded_graph = store.load_graph(filename)
    load_time = time.time() - start

    print(f"  Time: {load_time:.4f}s")
    print(f"  Triples loaded: {len(loaded_graph)}")

    # Test 3: Load all graphs
    print(f"\nTest 3: Load all graphs from directory")

    start = time.time()
    loaded_df = store.load_all_graphs()
    load_all_time = time.time() - start

    print(f"  Time: {load_all_time:.4f}s")
    print(f"  Triples loaded: {len(loaded_df)}")

    # Test 4: Query loaded data
    print(f"\nTest 4: Query loaded data")

    start = time.time()
    result_count = 0
    for _ in store.triples((None, None, None)):
        result_count += 1
    query_time = time.time() - start

    print(f"  Time: {query_time:.4f}s")
    print(f"  Results: {result_count:,}")

    # Test 5: Memory comparison
    print(f"\nTest 5: Memory comparison")

    graph_memory = sys.getsizeof(graph) / (1024 * 1024)  # MB
    df_memory = sys.getsizeof(loaded_df) / (1024 * 1024)  # MB

    print(f"  In-memory Graph: {graph_memory:.2f} MB")
    print(f"  In-memory DataFrame: {df_memory:.2f} MB")
    print(f"  File size: {file_size:.2f} MB")
    print(f"  Compression ratio: {file_size / max(graph_memory, df_memory):.2f}x")

    return {
        "store_time": store_time,
        "load_time": load_time,
        "load_all_time": load_all_time,
        "query_time": query_time,
        "file_size": file_size,
        "graph_memory": graph_memory,
        "df_memory": df_memory,
    }


def main():
    """Run file I/O benchmarks."""
    sizes = [1000, 10000, 50000, 100000]

    print("\n" + "=" * 60)
    print("FILE I/O OPERATIONS BENCHMARK")
    print("=" * 60)

    results = {}

    for size in sizes:
        print(f"\n{'#' * 60}")
        print(f"# Dataset size: {size:,} triples")
        print(f"{'#' * 60}")

        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            result = benchmark_file_operations(size, temp_dir)
            results[size] = result
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
    print(f"{'Size':>12} | {'Store Time':>12} | {'Load Time':>12} | {'File Size':>10}")
    print("-" * 60)

    for size, res in results.items():
        print(
            f"{size:>12,} | {res['store_time']:>12.4f} | {res['load_time']:>12.4f} | {res['file_size']:>10.2f} MB"
        )

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    # Check if file operations scale well
    store_times = [results[size]["store_time"] for size in results]
    load_times = [results[size]["load_time"] for size in results]

    avg_store_time = sum(store_times) / len(store_times)
    avg_load_time = sum(load_times) / len(load_times)

    print(f"\nAverage Store Time: {avg_store_time:.4f}s")
    print(f"Average Load Time: {avg_load_time:.4f}s")

    # Calculate throughput
    sizes = list(results.keys())
    print(f"\nThroughput: {sum(sizes) / sum(store_times):.0f} triples/second (store)")

    print("\nKey observations:")
    print("• File I/O operations should scale well for large datasets")
    print("• Parquet format provides efficient compression")
    print(
        "• File operations are typically much faster than in-memory DataFrame operations"
    )
    print("• Storage efficiency improves with larger datasets")


if __name__ == "__main__":
    main()
