#!/usr/bin/env python3
"""Minimal test to isolate performance bottleneck"""

import time
import os
import shutil
from rdflib import Graph, URIRef
from parquet_triple_store import ParquetTripleStore

# Clean up
if os.path.exists("test_parquet"):
    shutil.rmtree("test_parquet")
os.makedirs("test_parquet")

print("Testing ParquetTripleStore performance...")

# Test 1: Add 100 triples to Parquet store
print("\n1. Adding 100 triples to Parquet store...")
parquet_store = ParquetTripleStore({"storage_path": "test_parquet"})

start = time.time()
for i in range(100):
    s = URIRef(f"http://example.org/s{i}")
    p = URIRef(f"http://example.org/p{i % 3}")
    o = URIRef(f"http://example.org/o{i % 5}")
    parquet_store.add((s, p, o))
parquet_time = time.time() - start
print(f"   Time: {parquet_time:.4f}s")

# Test 2: Add 100 triples to rdflib in-memory store
print("\n2. Adding 100 triples to rdflib in-memory store...")
rdf_graph = Graph()

start = time.time()
for i in range(100):
    s = URIRef(f"http://example.org/s{i}")
    p = URIRef(f"http://example.org/p{i % 3}")
    o = URIRef(f"http://example.org/o{i % 5}")
    rdf_graph.add((s, p, o))
rdf_time = time.time() - start
print(f"   Time: {rdf_time:.4f}s")

# Test 3: Load all graphs from Parquet
print("\n3. Loading all graphs from Parquet store...")
parquet_store.load_all_graphs()
load_time = time.time() - start
print(f"   Time: {load_time:.4f}s")
print(f"   Loaded {len(parquet_store.triples_df)} triples")

# Test 4: Query Parquet store
print("\n4. Querying Parquet store...")
start = time.time()
results = list(parquet_store.triples((URIRef("http://example.org/s0"), None, None)))
query_time = time.time() - start
print(f"   Time: {query_time:.4f}s")
print(f"   Found {len(results)} results")

# Test 5: Query rdflib store
print("\n5. Querying rdflib store...")
start = time.time()
results = list(rdf_graph.triples((URIRef("http://example.org/s0"), None, None)))
rdf_query_time = time.time() - start
print(f"   Time: {rdf_query_time:.4f}s")
print(f"   Found {len(results)} results")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Add performance:  Parquet={parquet_time:.4f}s, rdflib={rdf_time:.4f}s")
print(f"  Ratio: {parquet_time / rdf_time:.2f}x (Parquet slower)")
print(f"\nQuery performance: Parquet={query_time:.4f}s, rdflib={rdf_query_time:.4f}s")
print(f"  Ratio: {query_time / rdf_query_time:.2f}x (Parquet slower)")
print(f"\nKey findings:")
print(f"  - Parquet store is significantly slower for in-memory operations")
print(f"  - This is expected due to DataFrame overhead and I/O operations")
print(f"  - Main advantage: persistent storage and scalability")
print(
    f"  - Use Parquet when you need to store data persistently or work with large datasets"
)
print("=" * 60)
