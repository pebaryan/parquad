#!/usr/bin/env python3
"""Validate indexing functionality in ParquetTripleStore."""

import sys
import time

sys.path.insert(0, str(__file__))

from rdflib import URIRef

from parquad.store import ParquetTripleStoreWithIndex


def test_indexing():
    """Test indexing methods in ParquetTripleStoreWithIndex."""
    print("\n" + "=" * 60)
    print("VALIDATING INDEXING FUNCTIONality")
    print("=" * 60)

    temp_dir = "/tmp/index_test"

    try:
        # Create test dataset
        print("\n1. Creating test dataset with 1000 triples...")
        store = ParquetTripleStoreWithIndex({"storage_path": temp_dir})

        for i in range(1000):
            s = URIRef(f"http://example.org/subject/{i % 50}")
            p = URIRef(f"http://example.org/property/{i % 20}")
            o = URIRef(f"value_{i}")
            store.add((s, p, o))

        print("   Created 1000 triples")
        print(f"   Unique subjects: {store.get_statistics()['unique_subjects']}")
        print(f"   Unique predicates: {store.get_statistics()['unique_predicates']}")

        # Test find_by_subject
        print("\n2. Testing find_by_subject()...")
        subject_uri = URIRef("http://example.org/subject/0")
        start = time.time()
        results = store.find_by_subject(str(subject_uri))
        elapsed = time.time() - start
        print(f"   Found {len(results)} triples for subject {subject_uri}")
        print(f"   Time: {elapsed:.4f}s")

        # Compare with regular query
        print("\n3. Comparing with regular triples() query...")
        start = time.time()
        query_results = list(store.triples((subject_uri, None, None)))
        elapsed_query = time.time() - start
        print(f"   Query found {len(query_results)} triples")
        print(f"   Query time: {elapsed_query:.4f}s")

        # Test find_by_predicate
        print("\n4. Testing find_by_predicate()...")
        predicate_uri = URIRef("http://example.org/property/0")
        start = time.time()
        results = store.find_by_predicate(str(predicate_uri))
        elapsed = time.time() - start
        print(f"   Found {len(results)} triples for predicate {predicate_uri}")
        print(f"   Time: {elapsed:.4f}s")

        # Test find_triples with multiple criteria
        print("\n5. Testing find_triples() with multiple criteria...")
        start = time.time()
        results = store.find_triples(
            subject=str(subject_uri), predicate=str(predicate_uri)
        )
        elapsed = time.time() - start
        print(f"   Found {len(results)} matching triples")
        print(f"   Time: {elapsed:.4f}s")

        # Performance comparison
        print("\n6. Performance comparison (100 iterations)...")
        iterations = 100

        # find_by_subject
        start = time.time()
        for _ in range(iterations):
            store.find_by_subject(str(subject_uri))
        elapsed = time.time() - start
        avg_time = elapsed / iterations
        print(f"   find_by_subject(): {avg_time:.4f}s per call")

        # Regular query
        start = time.time()
        for _ in range(iterations):
            list(store.triples((subject_uri, None, None)))
        elapsed_query = time.time() - start
        avg_time_query = elapsed_query / iterations
        print(f"   triples() query: {avg_time_query:.4f}s per call")

        if avg_time < avg_time_query:
            speedup = avg_time_query / avg_time
            print(f"   ✓ Indexing is {speedup:.2f}x faster")
        else:
            print("   ✗ Indexing is slower")

        # Test find_triples
        print("\n7. Testing find_triples() performance...")
        start = time.time()
        for _ in range(iterations):
            store.find_triples(subject=str(subject_uri), predicate=str(predicate_uri))
        elapsed = time.time() - start
        avg_time = elapsed / iterations
        print(f"   find_triples(): {avg_time:.4f}s per call")

        print("\n✓ Indexing validation completed")

    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_indexing()
