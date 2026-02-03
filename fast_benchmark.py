#!/usr/bin/env python3
"""
Fast benchmark comparing ParquetTripleStore vs in-memory rdflib store.
Tests core operations with minimal overhead.
"""

import time
import os
import shutil
from rdflib import Graph, URIRef
from parquet_triple_store import ParquetTripleStore

# Setup storage paths
PARQUET_PATH = "benchmark_parquet_triples"
MEMORY_PATH = "benchmark_memory_triples"

# Clean up any previous benchmark data
if os.path.exists(PARQUET_PATH):
    shutil.rmtree(PARQUET_PATH)
if os.path.exists(MEMORY_PATH):
    shutil.rmtree(MEMORY_PATH)

os.makedirs(PARQUET_PATH, exist_ok=True)

# Dataset sizes to test
DATASET_SIZES = [100, 1000, 10000]


def generate_triples(n):
    """Generate n random triples"""
    triples = []
    for i in range(n):
        subject = URIRef(f"http://example.org/subject{i}")
        predicate = URIRef("http://example.org/predicate")
        object_ = URIRef(f"http://example.org/object{i}")
        triples.append((subject, predicate, object_))
    return triples


def benchmark_add_triples(store, triples):
    """Benchmark adding triples to a store"""
    start_time = time.time()
    for triple in triples:
        store.add(triple)
    elapsed = time.time() - start_time
    return elapsed


def benchmark_query_triples(store, subject_uri):
    """Benchmark querying triples by subject"""
    start_time = time.time()
    results = list(store.triples((subject_uri, None, None)))
    elapsed = time.time() - start_time
    return elapsed, len(results)


def benchmark_get_length(store):
    """Benchmark getting store length"""
    start_time = time.time()
    length = len(store)
    elapsed = time.time() - start_time
    return elapsed, length


def print_comparison(name, time_parquet, time_rdf, ratio):
    """Print comparison results"""
    print(
        f"{name:30} | Parquet: {time_parquet:8.4f}s | rdflib: {time_rdf:8.4f}s | Ratio: {ratio:8.2f}x"
    )


def run_benchmarks():
    """Run comprehensive benchmarks"""
    print("=" * 100)
    print("FAST BENCHMARK: ParquetTripleStore vs rdflib in-memory")
    print("=" * 100)

    print(
        f"\n{'Operation':<30} | {'Parquet (s)':<12} | {'rdflib (s)':<12} | {'Ratio':<12}"
    )
    print("-" * 100)

    # Test 1: Adding triples
    print("\n1. Adding triples:")
    for size in DATASET_SIZES:
        print(f"\n  Dataset size: {size:,} triples")
        triples = generate_triples(size)

        # Parquet store
        parquet_store = ParquetTripleStore({"storage_path": PARQUET_PATH})
        time_parquet = benchmark_add_triples(parquet_store, triples)

        # rdflib in-memory
        rdf_graph = Graph()
        time_rdf = benchmark_add_triples(rdf_graph, triples)

        ratio = time_parquet / time_rdf if time_rdf > 0 else float("inf")
        print_comparison(f"  Add {size:,} triples", time_parquet, time_rdf, ratio)

    # Test 2: Querying triples
    print("\n2. Querying by subject:")
    for size in DATASET_SIZES:
        print(f"\n  Dataset size: {size:,} triples")
        triples = generate_triples(size)

        # Parquet store
        parquet_store = ParquetTripleStore({"storage_path": PARQUET_PATH})
        for triple in triples:
            parquet_store.add(triple)
        parquet_store.load_all_graphs()

        # rdflib graph
        rdf_graph = Graph()
        for triple in triples:
            rdf_graph.add(triple)

        # Query
        query_subject = URIRef("http://example.org/subject0")
        time_parquet, count_parquet = benchmark_query_triples(
            parquet_store, query_subject
        )
        time_rdf, count_rdf = benchmark_query_triples(rdf_graph, query_subject)

        ratio = time_parquet / time_rdf if time_rdf > 0 else float("inf")
        print_comparison(f"  Query subject0", time_parquet, time_rdf, ratio)
        print(f"  Results: Parquet={count_parquet}, rdflib={count_rdf}")

    # Test 3: Getting store length
    print("\n3. Getting store length:")
    for size in DATASET_SIZES:
        print(f"\n  Dataset size: {size:,} triples")
        triples = generate_triples(size)

        # Parquet store
        parquet_store = ParquetTripleStore({"storage_path": PARQUET_PATH})
        for triple in triples:
            parquet_store.add(triple)

        # rdflib graph
        rdf_graph = Graph()
        for triple in triples:
            rdf_graph.add(triple)

        # Get length
        time_parquet, length_parquet = benchmark_get_length(parquet_store)
        time_rdf, length_rdf = benchmark_get_length(rdf_graph)

        ratio = time_parquet / time_rdf if time_rdf > 0 else float("inf")
        print_comparison(f"  Get length", time_parquet, time_rdf, ratio)
        print(f"  Length: Parquet={length_parquet}, rdflib={length_rdf}")

    # Test 4: Storage efficiency
    print("\n4. Storage efficiency:")
    storage_size = 0
    for filename in os.listdir(PARQUET_PATH):
        if filename.endswith(".parquet"):
            filepath = os.path.join(PARQUET_PATH, filename)
            storage_size += os.path.getsize(filepath)

    total_triples = sum(DATASET_SIZES)
    storage_size_mb = storage_size / (1024 * 1024)
    storage_efficiency = storage_size_mb / total_triples

    print(f"\n  Total triples: {total_triples:,}")
    print(f"  Storage size: {storage_size_mb:.2f} MB")
    print(f"  Efficiency: {storage_efficiency:.6f} MB per triple")
    print(f"  Ratio: {storage_size_mb / total_triples * 1000:.3f} KB per 1000 triples")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    avg_add_ratio = sum(
        [results[f"add_{size}"]["ratio"] for size in DATASET_SIZES]
    ) / len(DATASET_SIZES)
    avg_query_ratio = sum(
        [results[f"query_{size}"]["ratio"] for size in DATASET_SIZES]
    ) / len(DATASET_SIZES)
    avg_length_ratio = sum(
        [results[f"length_{size}"]["ratio"] for size in DATASET_SIZES]
    ) / len(DATASET_SIZES)

    print(f"\nAverage performance ratios:")
    print(f"  Adding triples:    {avg_add_ratio:.2f}x (Parquet slower)")
    print(f"  Querying:          {avg_query_ratio:.2f}x (Parquet slower)")
    print(f"  Getting length:    {avg_length_ratio:.2f}x (Parquet slower)")

    print(f"\nKey findings:")
    print(
        f"  • Parquet store is slower for in-memory operations (due to DataFrame overhead)"
    )
    print(f"  • Main advantage: persistent storage and scalability")
    print(
        f"  • Storage efficiency: {storage_size_mb:.2f} MB for {total_triples:,} triples"
    )
    print(
        f"  • Use Parquet when: you need persistence, large datasets, or want to avoid memory limits"
    )
    print(
        f"  • Use rdflib when: you need maximum performance for small datasets in memory"
    )

    print("\n" + "=" * 100)


if __name__ == "__main__":
    run_benchmarks()
