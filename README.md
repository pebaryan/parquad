# Parquet Triple Store Implementation

A high-performance RDF triple store implementation using RDFLib and Apache Parquet format.

## Features

- **Storage**: Store RDF graphs as Parquet files for efficient disk usage
- **Loading**: Load RDF graphs from Parquet files
- **Batch Operations**: Store and load multiple graphs
- **Querying**: Basic SPARQL query support
- **Indexing**: Optional indexed storage for faster subject/predicate queries
- **Merging**: Merge multiple RDF graphs into a single dataset
- **Export**: Export triples to Turtle format

## Installation

```bash
cd parquad
pip install -r requirements.txt
```

Required packages:
- rdflib >= 6.4.0
- pyarrow >= 14.0.0
- pandas >= 2.0.0

## Basic Usage

### Creating a Triple Store

```python
from parquet_triple_store import ParquetTripleStore

# Initialize the store
store = ParquetTripleStore(storage_path="my_triple_store")
```

### Storing RDF Graphs

```python
from rdflib import Graph, URIRef, Literal, RDF
from parquet_triple_store import ParquetTripleStore

graph = Graph()

# Add some triples
graph.add((URIRef("http://example.org/person1"), RDF.type, URIRef("http://xmlns.com/foaf/0.1/Person")))
graph.add((URIRef("http://example.org/person1"), 
            URIRef("http://xmlns.com/foaf/0.1/name"), 
            Literal("Alice")))

# Store the graph
filepath = store.store_graph(graph, "my_data")
```

### Loading RDF Graphs

```python
# Load a specific graph
loaded_graph = store.load_graph("my_data")

# Load all graphs
all_triples = store.load_all_graphs()
```

### Querying

```python
# Get statistics
stats = store.get_statistics()
print(f"Total triples: {stats['total_triples']}")

# Export to Turtle
store.export_to_turtle("output.ttl")
```

### Using Indexed Store

For faster queries by subject or predicate:

```python
from parquet_triple_store import ParquetTripleStoreWithIndex

# Initialize indexed store
indexed_store = ParquetTripleStoreWithIndex()

# Store and load graphs
indexed_store.store_graph(graph, "indexed_data")
indexed_store.load_all_graphs()

# Query by subject
results = indexed_store.find_by_subject("http://example.org/person1")

# Find triples with criteria
results = indexed_store.find_triples(
    subject="http://example.org/person1",
    predicate="http://xmlns.com/foaf/0.1/name"
)
```

### Batch Operations

```python
from rdflib import Graph
from parquet_triple_store import ParquetTripleStore

# Store multiple graphs
graphs_to_store = [
    ("dataset1", graph1),
    ("dataset2", graph2),
    ("dataset3", graph3)
]

filenames = store.batch_store(graphs_to_store)
```

### Merging Graphs

```python
# Merge two graphs
merged_file = store.merge_graphs("dataset1", "dataset2")
```

## API Reference

### ParquetTripleStore

#### `__init__(storage_path: str)`

Initialize the triple store with a storage directory.

#### `store_graph(graph: Graph, filename: str = None) -> str`

Store an RDF graph as a Parquet file.

#### `load_graph(filename: str) -> Graph`

Load an RDF graph from a Parquet file.

#### `batch_store(graphs: List[Tuple[str, Graph]]) -> List[str]`

Store multiple graphs at once.

#### `load_all_graphs() -> pd.DataFrame`

Load all Parquet files and return as a DataFrame.

#### `get_statistics() -> dict`

Get statistics about stored triples.

#### `export_to_turtle(filename: str = "output.ttl") -> str`

Export triples to Turtle format.

#### `merge_graphs(filename1: str, filename2: str) -> str`

Merge two graphs and store as new file.

#### `delete_file(filename: str) -> bool`

Delete a specific Parquet file.

### ParquetTripleStoreWithIndex

Extends ParquetTripleStore with additional indexing capabilities.

#### `find_by_subject(subject_uri: str) -> pd.DataFrame`

Find all triples with a specific subject.

#### `find_by_predicate(predicate_uri: str) -> pd.DataFrame`

Find all triples with a specific predicate.

#### `find_triples(subject: str = None, predicate: str = None, object: str = None) -> pd.DataFrame`

Find triples matching given criteria.

## Performance Considerations

- Parquet format provides excellent compression and fast reading
- Indexed store is recommended for frequent subject/predicate queries
- For large datasets, consider loading only necessary data
- SPARQL queries require `sparqlwrapper` package

## Example Usage

See `usage_example.py` for comprehensive examples.

## License

MIT
