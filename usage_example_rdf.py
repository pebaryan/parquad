"""
Example usage of ParquetTripleStore implementation with rdflib Store API
"""

from rdflib import Graph, URIRef, Literal, RDF, RDFS
from parquet_triple_store import ParquetTripleStore, ParquetTripleStoreWithIndex

# Initialize the store with configuration
store = ParquetTripleStore(configuration={"storage_path": "parquet_examples"})

# Create a sample RDF graph
graph = Graph()

# Add some triples
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

# Store the graph using the Store API
graph.serialize(destination="person_data", format="turtle")
store.store_graph(graph, "person_data")
print(f"Stored graph to: {store.storage_path}/person_data")

# Load the graph back using rdflib's query interface
loaded_graph = Graph(store=store)
loaded_graph.parse("person_data", format="turtle")
print(f"\nLoaded {len(loaded_graph)} triples")

# Store another graph
graph2 = Graph()
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

# Store and load using Store API
graph2.serialize(destination="person_data_extended", format="turtle")
store.store_graph(graph2, "person_data_extended")

# Load all graphs
all_triples = store.load_all_graphs()
print(f"\nTotal triples across all files: {len(all_triples)}")

# Get statistics
stats = store.get_statistics()
print("\nStatistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")

# Export to Turtle
turtle_file = store.export_to_turtle("output.ttl")
print(f"\nExported to: {turtle_file}")

# Using indexed store for faster queries
indexed_store = ParquetTripleStoreWithIndex(
    configuration={"storage_path": "parquet_triples_indexed"}
)

# Store and load graphs
indexed_store.store_graph(graph, "indexed_person1")
indexed_store.store_graph(graph2, "indexed_person2")
indexed_store.load_all_graphs()

# Query by subject using rdflib's query interface
query = """
SELECT ?s ?p ?o
WHERE {
    ?s ?p ?o .
    FILTER(?s = <http://example.org/person1>)
}
"""
results = list(indexed_store.query(query))
print(f"\nTriples about person1: {len(results)}")

# Query by predicate
query = """
SELECT ?s ?o
WHERE {
    ?s <http://xmlns.com/foaf/0.1/knows> ?o .
}
"""
results = list(indexed_store.query(query))
print(f"Triples with foaf:knows predicate: {len(results)}")

# Find all triples with criteria
query = """
SELECT ?name
WHERE {
    <http://example.org/person1> <http://xmlns.com/foaf/0.1/name> ?name .
}
"""
results = list(indexed_store.query(query))
print(f"Person1's name: {len(results)} triple(s)")

# Merge graphs
merged_file = indexed_store.merge_graphs("indexed_person1", "indexed_person2")
print(f"\nMerged graphs saved to: {merged_file}")

# Get merged statistics
merged_stats = indexed_store.get_statistics()
print(f"\nMerged statistics: {merged_stats['total_triples']} total triples")
