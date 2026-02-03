#!/usr/bin/env python3
"""Test the fixed load_all_graphs() method"""

from parquet_triple_store import ParquetTripleStoreWithIndex
from rdflib import Graph, URIRef

# Create a simple store
store = ParquetTripleStoreWithIndex()

# Add some triples
graph = Graph()
for i in range(100):
    graph.add(
        (
            URIRef(f"http://example.org/subject{i}"),
            URIRef("http://example.org/predicate"),
            URIRef(f"http://example.org/object{i}"),
        )
    )

print("Adding triples to store...")
store.store_graph(graph, "test_data.parquet")

# Try to load all graphs
print("\nLoading all graphs...")
df = store.load_all_graphs()

print(f"Loaded {len(df)} triples")
print(f"First triple: {df.iloc[0] if len(df) > 0 else 'No data'}")

# Try find_by_subject
print("\nTrying find_by_subject...")
try:
    result = store.find_by_subject("http://example.org/subject0")
    print(f"Found {len(result)} triples for subject0")
except Exception as e:
    print(f"Error: {e}")
