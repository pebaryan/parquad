"""
Example usage of ParquetTripleStore with rdflib Store API integration
"""

from rdflib import Graph, URIRef, Literal, RDF, RDFS
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex
import pandas as pd

print("=== ParquetTripleStore with rdflib Store API ===\n")

# Initialize the store with configuration
config = {"storage_path": "parquet_examples"}
store = ParquetTripleStore(configuration=config)
print(f"Initialized ParquetTripleStore with storage path: {config['storage_path']}\n")

# Create a sample RDF graph using Store API
print("=== Creating Graph with Store API ===")
graph = Graph(store=store)

# Add some triples
print("Adding RDF triples...")
graph.add(
    (
        URIRef("http://example.org/person1"),
        RDF.type,
        URIRef("http://xmlns.com/foaf/0.1/Person"),
    )
)

graph.add(
    (
        URIRef("http://example.org/person1"),
        URIRef("http://xmlns.com/foaf/0.1/name"),
        Literal("Alice"),
    )
)

graph.add(
    (
        URIRef("http://example.org/person1"),
        URIRef("http://xmlns.com/foaf/0.1/knows"),
        URIRef("http://example.org/person2"),
    )
)

graph.add(
    (
        URIRef("http://example.org/person2"),
        RDF.type,
        URIRef("http://xmlns.com/foaf/0.1/Person"),
    )
)

graph.add(
    (
        URIRef("http://example.org/person2"),
        URIRef("http://xmlns.com/foaf/0.1/name"),
        Literal("Bob"),
    )
)

print(f"Added {len(graph)} triples to in-memory store\n")

# Store the graph to disk
print("=== Storing Graph to Disk ===")
filepath = store.store_graph(graph, "person_data")
print(f"Stored graph to: {filepath}\n")

# Load the graph back
print("=== Loading Graph from Disk ===")
loaded_graph = store.load_graph("person_data")
print(f"Loaded {len(loaded_graph)} triples from person_data\n")

# Create another graph
print("=== Creating Second Graph ===")
graph2 = Graph(store=store)
graph2.add(
    (
        URIRef("http://example.org/person2"),
        URIRef("http://xmlns.com/foaf/0.1/knows"),
        URIRef("http://example.org/person3"),
    )
)
graph2.add(
    (
        URIRef("http://example.org/person3"),
        RDF.type,
        URIRef("http://xmlns.com/foaf/0.1/Person"),
    )
)
graph2.add(
    (
        URIRef("http://example.org/person3"),
        URIRef("http://xmlns.com/foaf/0.1/name"),
        Literal("Charlie"),
    )
)
print(f"Added {len(graph2)} triples to in-memory store\n")

store.store_graph(graph2, "person_data_extended")
print(f"Stored second graph to person_data_extended\n")

# Load all graphs
print("=== Loading All Graphs ===")
all_triples = store.load_all_graphs()
print(f"Total triples across all files: {len(all_triples)}\n")

# Get statistics
print("=== Statistics ===")
stats = store.get_statistics()
print("Statistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")

# Export to Turtle
print("\n=== Exporting to Turtle ===")
turtle_file = store.export_to_turtle("output.ttl")
print(f"Exported to: {turtle_file}")

# Export in-memory triples to Turtle
print("\n=== Exporting In-Memory Triples ===")
turtle_file_in_memory = store.export_to_turtle_in_memory("output_in_memory.ttl")
print(f"Exported in-memory triples to: {turtle_file_in_memory}")

# Using indexed store for faster queries
print("\n=== Using Indexed Store ===")
indexed_store = ParquetTripleStoreWithIndex(
    configuration={"storage_path": "indexed_examples"}
)

# Store and load graphs with indexed store
indexed_store.store_graph(graph, "indexed_person1")
indexed_store.store_graph(graph2, "indexed_person2")
indexed_store.load_all_graphs()

# Query by subject
print("\n=== Indexed Store Queries ===")
results = indexed_store.find_by_subject("http://example.org/person1")
print(f"Triples about person1: {len(results)}")

results = indexed_store.find_by_predicate("http://xmlns.com/foaf/0.1/knows")
print(f"Triples with foaf:knows predicate: {len(results)}")

# Find all triples with criteria
results = indexed_store.find_triples(
    subject="http://example.org/person1", predicate="http://xmlns.com/foaf/0.1/name"
)
print(f"Person1's name: {len(results)} triple(s)")

# Merge graphs
merged_file = indexed_store.merge_graphs("indexed_person1", "indexed_person2")
print(f"\nMerged graphs saved to: {merged_file}")

# Get merged statistics
merged_stats = indexed_store.get_statistics()
print(f"\nMerged statistics: {merged_stats['total_triples']} total triples")

print("\n=== Example Complete ===")
