"""
Benchmark script to compare performance between rdflib memory store,
Parquet store, and Parquet store with index.

This script measures:
1. Adding triples performance
2. Querying performance
3. Memory usage
4. Storage efficiency
"""

import time
import tracemalloc
import pandas as pd
from rdflib import Graph, URIRef, Literal, RDF
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex
import os
import shutil
import gc

# Setup test data
NUM_TRIPLES = 10000
BASE_URI = "http://example.org/resource/"
PREDICATE = RDF.type

print("=" * 80)
print("RDF Triple Store Benchmark")
print("=" * 80)
print(f"Test dataset size: {NUM_TRIPLES} triples")
print("=" * 80)

# Clean up previous test data
for folder in ["benchmark_memory", "benchmark_parquet", "benchmark_indexed"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# Generate test data
print("\n=== Generating Test Data ===")
test_triples = []
subjects = [f"{BASE_URI}s{i}" for i in range(100)]
predicates = [f"{BASE_URI}p{i}" for i in range(10)]
objects = [f"{BASE_URI}o{i}" for i in range(20)]

print(f"Generated {NUM_TRIPLES} test triples")
print(
    f"Subjects: {len(subjects)}, Predicates: {len(predicates)}, Objects: {len(objects)}"
)
print()

# Test 1: rdflib memory store
print("=" * 80)
print("TEST 1: rdflib Memory Store")
print("=" * 80)

# Reset memory tracking
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

graph_memory = Graph()
print("Adding triples to memory store...")
for i in range(NUM_TRIPLES):
    subject = URIRef(subjects[i % len(subjects)])
    predicate = URIRef(predicates[i % len(predicates)])
    object = URIRef(objects[i % len(objects)])
    graph_memory.add((subject, predicate, object))

    if (i + 1) % 1000 == 0:
        print(f"  Added {i + 1}/{NUM_TRIPLES} triples...")

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

mem_used = end_mem - start_mem
time_used = end_time - start_time

print(f"\nResults:")
print(f"  Time: {time_used:.4f} seconds")
print(f"  Memory used: {mem_used / 1024 / 1024:.2f} MB")
print(f"  Throughput: {NUM_TRIPLES / time_used:.0f} triples/second")

# Query performance
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

# Query by subject
query_subject = URIRef(subjects[0])
results = list(graph_memory.triples((query_subject, None, None)))

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

query_time = end_time - start_time
query_mem = end_mem - start_mem

print(f"\nQuery performance:")
print(f"  Query: Find all triples with subject '{query_subject}'")
print(f"  Time: {query_time:.4f} seconds")
print(f"  Memory: {query_mem / 1024 / 1024:.2f} MB")
print(f"  Results: {len(results)} triples")

# Test 2: Parquet store
print("\n" + "=" * 80)
print("TEST 2: Parquet Store")
print("=" * 80)

gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

store_parquet = ParquetTripleStore(configuration={"storage_path": "benchmark_parquet"})
print("Adding triples to Parquet store...")
for i in range(NUM_TRIPLES):
    subject = URIRef(subjects[i % len(subjects)])
    predicate = URIRef(predicates[i % len(predicates)])
    object = URIRef(objects[i % len(objects)])
    store_parquet.add((subject, predicate, object))

    if (i + 1) % 1000 == 0:
        print(f"  Added {i + 1}/{NUM_TRIPLES} triples...")

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

mem_used = end_mem - start_mem
time_used = end_time - start_time

print(f"\nResults:")
print(f"  Time: {time_used:.4f} seconds")
print(f"  Memory used: {mem_used / 1024 / 1024:.2f} MB")
print(f"  Throughput: {NUM_TRIPLES / time_used:.0f} triples/second")

# Store graphs
print("\nStoring graphs to disk...")
graph_to_store = Graph()
for i in range(NUM_TRIPLES):
    subject = URIRef(subjects[i % len(subjects)])
    predicate = URIRef(predicates[i % len(predicates)])
    object = URIRef(objects[i % len(objects)])
    graph_to_store.add((subject, predicate, object))

    if (i + 1) % 1000 == 0:
        print(f"  Prepared {i + 1}/{NUM_TRIPLES} triples...")

timestamp = time.time()
filename = f"benchmark_data_{timestamp:.0f}.parquet"
filepath = store_parquet.store_graph(graph_to_store, filename)
print(f"  Stored to: {filepath}")

# Load all graphs
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

print("\nLoading all graphs...")
loaded_df = store_parquet.load_all_graphs()

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

load_time = end_time - start_time
load_mem = end_mem - start_mem

print(f"\nLoad results:")
print(f"  Time: {load_time:.4f} seconds")
print(f"  Memory: {load_mem / 1024 / 1024:.2f} MB")
print(f"  Triples loaded: {len(loaded_df)}")

# Query performance
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

# Query by subject - use triples method
query_subject = URIRef(query_subject)
results = list(store_parquet.triples((query_subject, None, None)))

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

query_time = end_time - start_time
query_mem = end_mem - start_mem

print(f"\nQuery performance:")
print(f"  Query: Find all triples with subject '{query_subject}'")
print(f"  Time: {query_time:.4f} seconds")
print(f"  Memory: {query_mem / 1024 / 1024:.2f} MB")
print(f"  Results: {len(results)} triples")

# Test 3: Parquet store with index
print("\n" + "=" * 80)
print("TEST 3: Parquet Store with Index")
print("=" * 80)

gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

store_indexed = ParquetTripleStoreWithIndex(
    configuration={"storage_path": "benchmark_indexed"}
)
print("Adding triples to indexed store...")
for i in range(NUM_TRIPLES):
    subject = URIRef(subjects[i % len(subjects)])
    predicate = URIRef(predicates[i % len(predicates)])
    object = URIRef(objects[i % len(objects)])
    store_indexed.add((subject, predicate, object))

    if (i + 1) % 1000 == 0:
        print(f"  Added {i + 1}/{NUM_TRIPLES} triples...")

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

mem_used = end_mem - start_mem
time_used = end_time - start_time

print(f"\nResults:")
print(f"  Time: {time_used:.4f} seconds")
print(f"  Memory used: {mem_used / 1024 / 1024:.2f} MB")
print(f"  Throughput: {NUM_TRIPLES / time_used:.0f} triples/second")

# Store graphs
print("\nStoring graphs to disk...")
graph_to_store = Graph()
for i in range(NUM_TRIPLES):
    subject = URIRef(subjects[i % len(subjects)])
    predicate = URIRef(predicates[i % len(predicates)])
    object = URIRef(objects[i % len(objects)])
    graph_to_store.add((subject, predicate, object))

    if (i + 1) % 1000 == 0:
        print(f"  Prepared {i + 1}/{NUM_TRIPLES} triples...")

timestamp = time.time()
filename = f"benchmark_data_{timestamp:.0f}.parquet"
filepath = store_indexed.store_graph(graph_to_store, filename)
print(f"  Stored to: {filepath}")

# Load all graphs
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

print("\nLoading all graphs and creating indexes...")
loaded_df = store_indexed.load_all_graphs()

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

load_time = end_time - start_time
load_mem = end_mem - start_mem

print(f"\nLoad results:")
print(f"  Time: {load_time:.4f} seconds")
print(f"  Memory: {load_mem / 1024 / 1024:.2f} MB")
print(f"  Triples loaded: {len(loaded_df)}")

# Query performance
gc.collect()
tracemalloc.start()

start_time = time.time()
start_mem = tracemalloc.get_traced_memory()[0]

# Query by subject
query_subject = URIRef(query_subject)
results = list(store_indexed.triples((query_subject, None, None)))

end_time = time.time()
end_mem = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

query_time = end_time - start_time
query_mem = end_mem - start_mem

print(f"\nQuery performance:")
print(f"  Query: Find all triples with subject '{query_subject}'")
print(f"  Time: {query_time:.4f} seconds")
print(f"  Memory: {query_mem / 1024 / 1024:.2f} MB")
print(f"  Results: {len(results)} triples")

# Summary
print("\n" + "=" * 80)
print("BENCHMARK SUMMARY")
print("=" * 80)

print("\n1. ADD PERFORMANCE (triples/second):")
print("-" * 80)
memory_throughput = NUM_TRIPLES / time_used if time_used > 0 else 0
parquet_throughput = NUM_TRIPLES / time_used if time_used > 0 else 0
indexed_throughput = NUM_TRIPLES / time_used if time_used > 0 else 0

print(f"  Memory Store:     {memory_throughput:8.0f} triples/sec")
print(f"  Parquet Store:    {parquet_throughput:8.0f} triples/sec")
print(f"  Indexed Store:    {indexed_throughput:8.0f} triples/sec")

print("\n2. QUERY PERFORMANCE (seconds):")
print("-" * 80)
print(f"  Memory Store:     {query_time:8.4f}s")
print(f"  Parquet Store:    {query_time:8.4f}s")
print(f"  Indexed Store:    {query_time:8.4f}s")

print("\n3. MEMORY USAGE (MB):")
print("-" * 80)
print(f"  Memory Store:     {mem_used / 1024 / 1024:8.2f} MB")
print(f"  Parquet Store:    {mem_used / 1024 / 1024:8.2f} MB")
print(f"  Indexed Store:    {mem_used / 1024 / 1024:8.2f} MB")

print("\n4. STORAGE EFFICIENCY:")
print("-" * 80)
file_size = os.path.getsize(filepath) if "filepath" in locals() else 0
print(f"  Disk usage:       {file_size / 1024 / 1024:8.2f} MB")

print("\n" + "=" * 80)
print("Benchmark Complete")
print("=" * 80)

# Clean up
print("\nCleaning up test data...")
for folder in ["benchmark_memory", "benchmark_parquet", "benchmark_indexed"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
print("Cleanup complete.")
