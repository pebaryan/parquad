#!/usr/bin/env python3
"""Test SPARQL query functionality with ParquetTripleStore"""

from rdflib import Graph, URIRef, Literal
from parquet_triple_store import ParquetTripleStore
import os


def test_basic_query():
    """Test basic SPARQL query with in-memory triples"""
    print("Testing basic SPARQL query...")

    config = {"storage_path": "test_query_storage"}

    if os.path.exists(config["storage_path"]):
        import shutil

        shutil.rmtree(config["storage_path"])

    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add some triples
    person = URIRef("http://example.org/person/1")
    name = Literal("John Doe")
    age = Literal(30)

    graph.add(
        (
            person,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            Literal("Person"),
        )
    )
    graph.add((person, URIRef("http://xmlns.com/foaf/0.1/name"), name))
    graph.add((person, URIRef("http://xmlns.com/foaf/0.1/age"), age))

    print(f"Added {len(graph)} triples")

    # Try to query
    try:
        query_result = graph.query(
            "SELECT ?p ?o WHERE { ?person ?p ?o . FILTER(?person = <http://example.org/person/1>) }"
        )

        print(f"Query executed successfully!")
        print(f"Number of results: {len(list(query_result))}")

        for row in query_result:
            print(f"  {row}")

        print("✅ Basic query test PASSED")
        return True
    except Exception as e:
        print(f"❌ Basic query test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_select_all():
    """Test SELECT * query"""
    print("\nTesting SELECT * query...")

    config = {"storage_path": "test_select_storage"}

    if os.path.exists(config["storage_path"]):
        import shutil

        shutil.rmtree(config["storage_path"])

    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add triples
    person = URIRef("http://example.org/person/2")
    graph.add(
        (
            person,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            Literal("Person"),
        )
    )
    graph.add((person, URIRef("http://xmlns.com/foaf/0.1/name"), Literal("Jane Smith")))

    print(f"Added {len(graph)} triples")

    # Query all triples
    try:
        query_result = graph.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")

        print(f"Query executed successfully!")
        print(f"Number of results: {len(list(query_result))}")

        for row in query_result:
            print(f"  {row}")

        print("✅ SELECT * test PASSED")
        return True
    except Exception as e:
        print(f"❌ SELECT * test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_count_query():
    """Test COUNT query"""
    print("\nTesting COUNT query...")

    config = {"storage_path": "test_count_storage"}

    if os.path.exists(config["storage_path"]):
        import shutil

        shutil.rmtree(config["storage_path"])

    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add triples
    for i in range(5):
        person = URIRef(f"http://example.org/person/{i}")
        graph.add(
            (
                person,
                URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                Literal("Person"),
            )
        )

    print(f"Added {len(graph)} triples")

    # Count query
    try:
        query_result = graph.query("SELECT (COUNT(?s) AS ?count) WHERE { ?s a ?type }")

        print(f"Query executed successfully!")

        for row in query_result:
            print(f"  Count: {row}")

        print("✅ COUNT query test PASSED")
        return True
    except Exception as e:
        print(f"❌ COUNT query test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_result_serialization():
    """Test serializing query results"""
    print("\nTesting result serialization...")

    config = {"storage_path": "test_serialize_storage"}

    if os.path.exists(config["storage_path"]):
        import shutil

        shutil.rmtree(config["storage_path"])

    store = ParquetTripleStore(config)
    graph = Graph(store=store)

    # Add triples
    person = URIRef("http://example.org/person/3")
    graph.add(
        (
            person,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            Literal("Person"),
        )
    )

    print(f"Added {len(graph)} triples")

    # Query and serialize
    try:
        query_result = graph.query("SELECT ?p ?o WHERE { ?s ?p ?o }")

        # Try to serialize
        serialized = query_result.serialize(format="json")
        print(f"Serialization successful! Length: {len(serialized)}")

        print("✅ Serialization test PASSED")
        return True
    except Exception as e:
        print(f"❌ Serialization test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SPARQL Query Tests for ParquetTripleStore")
    print("=" * 60)

    tests = [
        test_basic_query,
        test_select_all,
        test_count_query,
        test_result_serialization,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
