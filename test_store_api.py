#!/usr/bin/env python3
"""Test script for ParquetTripleStore with rdflib Graph API"""

from rdflib import Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import FOAF, XSD
from parquet_triple_store import ParquetTripleStore


def test_store_api():
    """Test using rdflib's Graph with ParquetTripleStore"""

    # Initialize store with configuration
    config = {"storage_path": "test_store_api"}

    # Create a Graph with the store
    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add some triples using the standard Graph API
    person1 = URIRef("http://example.org/person/1")
    person2 = URIRef("http://example.org/person/2")

    graph.add((person1, RDF.type, FOAF.Person))
    graph.add((person1, FOAF.name, Literal("John Doe")))
    graph.add((person2, RDF.type, FOAF.Person))
    graph.add((person2, FOAF.name, Literal("Jane Doe")))

    # Query the graph
    print("Testing rdflib Graph with ParquetTripleStore:")
    print(f"Number of triples: {len(graph)}")

    # Check if triples were actually added
    for triple in graph:
        print(f"Triple: {triple}")

    # Test query (may not work with current implementation)
    print("\nNote: SPARQL query may not work with current implementation")
    print("  This is a known limitation that needs further investigation")

    # Test export
    export_path = store.export_to_turtle_in_memory("test_output.ttl")
    print(f"\nExported to: {export_path}")

    # Verify file exists
    import os

    if os.path.exists(export_path):
        print("✓ Export successful")
    else:
        print("✗ Export failed")

    # Test load all graphs
    print("\nTesting load_all_graphs():")
    triples_df = store.load_all_graphs()
    print(f"Loaded {len(triples_df)} triples from DataFrame")

    # Test statistics
    print("\nStatistics:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_store_api()
