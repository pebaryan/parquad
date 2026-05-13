"""Parquad: Parquet-backed RDF Triple Store.

A high-performance RDF triple store implementation using RDFLib and
Apache Parquet format for efficient disk-based storage and querying.
"""

__version__ = "0.1.0"

from parquad.store import ParquetTripleStore, ParquetTripleStoreWithIndex

__all__ = [
    "ParquetTripleStore",
    "ParquetTripleStoreWithIndex",
]
