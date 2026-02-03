#!/usr/bin/env python3
"""Simple test to demonstrate what we've implemented"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parquet_triple_store import ParquetTripleStore
from rdflib import Graph, URIRef, Literal


def test_basic_functionality():
    """Test basic functionality of the store"""
    print("Testing basic ParquetTripleStore functionality...")

    # Create store configuration
    config = {"storage_path": "test_basic"}

    # Remove existing test directory if it exists
    if os.path.exists(config["storage_path"]):
        import shutil

        shutil.rmtree(config["storage_path"])

    # Create store and graph
    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add some test triples
    person = URIRef("http://example.org/person/1")
    name = Literal("John Doe")

    graph.add((person, URIRef("http://xmlns.com/foaf/0.1/name"), name))

    print(f"Added triples: {len(graph)}")

    # Test triples iteration
    count = 0
    for triple in graph:
        count += 1
        print(f"Triple: {triple}")

    print(f"Iterated through {count} triples")

    # Test the query method - this is what we've fixed
    try:
        # This should not crash anymore
        result = graph.query("SELECT ?p ?o WHERE { ?s ?p ?o }")
        print("✓ Query method works without crashing")

        # Try to iterate through results
        result_list = list(result)
        print(f"✓ Query returned {len(result_list)} results")

    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("✓ Basic functionality test passed!")
    return True


if __name__ == "__main__":
    test_basic_functionality()
