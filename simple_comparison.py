"""
Simple performance comparison between rdflib memory store and Parquet store
"""

import time
import tracemalloc
from rdflib import Graph, URIRef, Literal, RDF
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex
import gc
import shutil
import os
import pandas as pd

NUM_TRIPLES = 10000
BASE_URI = "http://example.org/resource/"

print("=" * 80)
print("Simple Performance Comparison")
print("=" * 80)
print(f"Test dataset: {NUM_TRIPLES} triples")
print("=" * 80)

# Clean up
for folder in ["test_memory", "test_parquet"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# Generate test data
print("\n1. Generating test data...")
subjects = [f"{BASE_URI}s{i}" for i in range(100)]
predicates = [f"{BASE_URI}p{i}" for i in range(10)]
objects = [f"{BASE_URI}o{i}" for i in range(20)]
test_triples = []
for i in range(NUM_TRIPLES):
    test_triples.append(
        (
            URIRef(subjects[i % len(subjects)]),
            URIRef(predicates[i % len(predicates)]),
            URIRef(objects[i % len(objects)]),
        )
    )
print(f"   Created {len(test_triples)} triples")

# Test 1: rdflib memory store
print("\n2. Testing rdflib memory store...")
gc.collect()

start_time = time.time()
graph = Graph()
for triple in test_triples:
    graph.add(triple)
end_time = time.time()

mem_used = end_time - start_time
print(f"   Time: {mem_used:.4f} seconds")
print(f"   Throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")

# Query test
gc.collect()
start_time = time.time()
query_subject = URIRef(subjects[0])
results = list(graph.triples((query_subject, None, None)))
end_time = time.time()

query_time = end_time - start_time
print(f"   Query time (subject lookup): {query_time:.4f} seconds")
print(f"   Results: {len(results)} triples")

# Test 2: Parquet store
print("\n3. Testing Parquet store...")
gc.collect()

start_time = time.time()
store_parquet = ParquetTripleStore(configuration={"storage_path": "test_parquet"})
for triple in test_triples:
    store_parquet.add(triple)
end_time = time.time()

mem_used = end_time - start_time
print(f"   Time: {mem_used:.4f} seconds")
print(f"   Throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")

# Store to disk
print("\n4. Storing to disk...")
graph_to_store = Graph()
for triple in test_triples:
    graph_to_store.add(triple)
filepath = store_parquet.store_graph(graph_to_store, "test_data.parquet")
file_size = os.path.getsize(filepath) / 1024 / 1024
print(f"   File size: {file_size:.2f} MB")

# Load test
print("\n5. Loading from disk...")
gc.collect()
start_time = time.time()
loaded_df = store_parquet.load_all_graphs()
end_time = time.time()

load_time = end_time - start_time
print(f"   Load time: {load_time:.4f} seconds")
print(f"   Triples loaded: {len(loaded_df)}")

# Query test
print("\n6. Querying Parquet store...")
gc.collect()
start_time = time.time()
query_subject = URIRef(subjects[0])
results = list(store_parquet.triples((query_subject, None, None)))
end_time = time.time()

query_time = end_time - start_time
print(f"   Query time: {query_time:.4f} seconds")
print(f"   Results: {len(results)} triples")

# Test 3: Parquet store with index
print("\n7. Testing Parquet store with index...")
gc.collect()

start_time = time.time()
store_indexed = ParquetTripleStoreWithIndex(
    configuration={"storage_path": "test_parquet_indexed"}
)
for triple in test_triples:
    store_indexed.add(triple)
end_time = time.time()

mem_used = end_time - start_time
print(f"   Time: {mem_used:.4f} seconds")
print(f"   Throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")

# Load and index
print("\n8. Loading and indexing...")
gc.collect()
start_time = time.time()
loaded_df = store_indexed.load_all_graphs()
end_time = time.time()

load_time = end_time - start_time
print(f"   Load+Index time: {load_time:.4f} seconds")
print(f"   Triples loaded: {len(loaded_df)}")

# Query test
print("\n9. Querying indexed store...")
gc.collect()
start_time = time.time()
query_subject = URIRef(subjects[0])
results = list(store_indexed.triples((query_subject, None, None)))
end_time = time.time()

query_time = end_time - start_time
print(f"   Query time: {query_time:.4f} seconds")
print(f"   Results: {len(results)} triples")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"1. Memory store throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")
print(f"2. Parquet store throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")
print(f"3. Indexed store throughput: {NUM_TRIPLES / mem_used:.0f} triples/second")
print(f"\n4. Memory store query time: {query_time:.4f}s")
print(f"5. Parquet store query time: {query_time:.4f}s")
print(f"6. Indexed store query time: {query_time:.4f}s")

# Cleanup
print("\nCleaning up...")
for folder in ["test_memory", "test_parquet", "test_parquet_indexed"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
print("Done.")
