import logging
import os
from datetime import datetime

import pandas as pd
from rdflib import Graph, Literal, URIRef
from rdflib.store import Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParquetTripleStore(Store):
    def __init__(self, configuration=None):
        Store.__init__(self, configuration)
        self.storage_path = (
            configuration.get("storage_path", "parquet_triples")
            if configuration
            else "parquet_triples"
        )
        self.triples_df = None
        self._ensure_storage_structure()

    def _ensure_storage_structure(self):
        """Create necessary directories for storage"""
        os.makedirs(self.storage_path, exist_ok=True)

    def _rdf_to_dataframe(self, graph: Graph) -> pd.DataFrame:
        """Convert RDF graph to Parquet-compatible DataFrame"""
        triples = []
        for s, p, o in graph:
            triples.append(
                {
                    "s": str(s),
                    "p": str(p),
                    "o": str(o),
                    "object_type": self._get_rdf_type(o),
                }
            )
        return pd.DataFrame(triples)

    def _get_rdf_type(self, obj):
        """Determine RDF type of object"""
        if isinstance(obj, URIRef):
            return "uri"
        elif isinstance(obj, Literal):
            return "literal"
        else:
            return "unknown"

    def _dataframe_to_rdf(self, df: pd.DataFrame) -> Graph:
        """Convert DataFrame back to RDF graph"""
        graph = Graph()
        for _, row in df.iterrows():
            subject = URIRef(row["s"])
            predicate = URIRef(row["p"])

            if row["object_type"] == "literal":
                obj = Literal(row["o"])
            else:
                obj = URIRef(row["o"])

            graph.add((subject, predicate, obj))
        return graph

    def add(self, triple, context=None, quoted=False):
        """Add a triple to the store"""
        s, p, o = triple
        new_triple = {
            "s": str(s),
            "p": str(p),
            "o": str(o),
            "object_type": self._get_rdf_type(o),
            "source_file": "in_memory_store",
        }

        if self.triples_df is None:
            self.triples_df = pd.DataFrame([new_triple])
        else:
            self.triples_df = pd.concat(
                [self.triples_df, pd.DataFrame([new_triple])], ignore_index=True
            )

    def remove(self, triple, context=None):
        """Remove a triple from the store"""
        if self.triples_df is None:
            return

        s, p, o = triple
        mask = pd.Series(True, index=self.triples_df.index)

        if s is not None:
            mask &= self.triples_df["s"] == str(s)
        if p is not None:
            mask &= self.triples_df["p"] == str(p)
        if o is not None:
            mask &= self.triples_df["o"] == str(o)

        self.triples_df = self.triples_df[~mask]

    def clear(self):
        """Clear all triples from the store"""
        self.triples_df = None
        logger.info("Cleared all triples from store")

    def save(self, filename=None):
        """Save current triples to Parquet file"""
        if self.triples_df is None or self.triples_df.empty:
            logger.warning("No triples to save")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"triples_{timestamp}.parquet"

        filepath = os.path.join(self.storage_path, filename)
        self.triples_df.to_parquet(filepath, engine="pyarrow", index=False)
        logger.info(f"Saved {len(self.triples_df)} triples to {filepath}")
        return filepath

    def triples(self, triple_pattern, context=None):
        """Iterate over triples in the store"""
        if self.triples_df is None:
            self.load_all_graphs()

        if self.triples_df.empty:
            return

        for _, row in self.triples_df.iterrows():
            if (
                (triple_pattern[0] is None or row["s"] == str(triple_pattern[0]))
                and (triple_pattern[1] is None or row["p"] == str(triple_pattern[1]))
                and (triple_pattern[2] is None or row["o"] == str(triple_pattern[2]))
            ):
                obj = (
                    Literal(row["o"])
                    if row.get("object_type") == "literal"
                    else URIRef(row["o"])
                )
                triple = (URIRef(row["s"]), URIRef(row["p"]), obj)
                yield triple, context

    def query(
        self, query, initBindings=None, initNs=None, queryGraph=None, DEBUG=False, **kwargs
    ):
        """Execute SPARQL query - returns a Result object (simplified)"""
        # Note: This is a simplified implementation that returns all triples.
        from rdflib.query import Result
        from rdflib.term import Variable

        if self.triples_df is None:
            self.load_all_graphs()

        result = Result(type_="SELECT")
        result.vars = [Variable("s"), Variable("p"), Variable("o")]
        result.bindings = []

        if self.triples_df is not None and not self.triples_df.empty:
            for _, row in self.triples_df.iterrows():
                obj = (
                    Literal(row["o"])
                    if row.get("object_type") == "literal"
                    else URIRef(row["o"])
                )
                result.bindings.append(
                    {
                        Variable("s"): URIRef(row["s"]),
                        Variable("p"): URIRef(row["p"]),
                        Variable("o"): obj,
                    }
                )

        return result

    def __len__(self, context=None):
        """Return the number of triples in the store"""
        if self.triples_df is None:
            self.load_all_graphs()
        return len(self.triples_df)

    def store_graph(self, graph: Graph, filename: str = None) -> str:
        """Store an RDF graph as Parquet file"""
        df = self._rdf_to_dataframe(graph)
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"triples_{timestamp}.parquet"

        filepath = os.path.join(self.storage_path, filename)
        df.to_parquet(filepath, engine="pyarrow", index=False)
        logger.info(f"Stored {len(df)} triples to {filepath}")
        return filepath

    def load_graph(self, filename: str) -> Graph:
        """Load an RDF graph from Parquet file"""
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        df = pd.read_parquet(filepath, engine="pyarrow")
        graph = self._dataframe_to_rdf(df)
        logger.info(f"Loaded {len(df)} triples from {filename}")
        return graph

    def batch_store(self, graphs: list[tuple[str, Graph]]) -> list[str]:
        """Store multiple graphs"""
        filenames = []
        for name, graph in graphs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.parquet"
            filepath = self.store_graph(graph, filename)
            filenames.append(filepath)
        return filenames

    def load_all_graphs(self) -> pd.DataFrame:
        """Load all Parquet files in storage and include in-memory triples"""
        all_dfs = []

        for filename in os.listdir(self.storage_path):
            if filename.endswith(".parquet") or filename.startswith(
                ("person_data", "indexed_person")
            ):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    df = pd.read_parquet(filepath, engine="pyarrow")
                    df["source_file"] = filename
                    all_dfs.append(df)
                except Exception as e:
                    logger.warning(f"Could not load {filename}: {e}")

        if all_dfs:
            df_list = all_dfs + (
                [self.triples_df] if self.triples_df is not None else []
            )
            self.triples_df = pd.concat(df_list, ignore_index=True)
            logger.info(
                f"Loaded {len(self.triples_df)} total triples from {len(all_dfs)} files"
                + f" and {len(self.triples_df) - sum(len(df) for df in all_dfs)} in-memory triples"
            )
        elif self.triples_df is not None and not self.triples_df.empty:
            logger.info(f"Using {len(self.triples_df)} in-memory triples")
        else:
            self.triples_df = pd.DataFrame()
            logger.info("No data loaded")

        return self.triples_df

    def get_statistics(self) -> dict:
        """Get statistics about stored triples"""
        if self.triples_df is None or self.triples_df.empty:
            return {"status": "no data loaded"}

        stats = {
            "total_triples": len(self.triples_df),
            "unique_subjects": self.triples_df["s"].nunique(),
            "unique_predicates": self.triples_df["p"].nunique(),
            "unique_objects": self.triples_df["o"].nunique(),
            "object_types": self.triples_df["object_type"].value_counts().to_dict(),
        }
        return stats

    def export_to_turtle(self, filename: str = "output.ttl") -> str:
        """Export loaded triples to Turtle format"""
        if self.triples_df is None or self.triples_df.empty:
            raise ValueError("No data to export")

        graph = self._dataframe_to_rdf(self.triples_df)
        filepath = os.path.join(self.storage_path, filename)
        graph.serialize(filepath, format="turtle")
        logger.info(f"Exported to {filepath}")
        return filepath

    def export_to_turtle_in_memory(self, filename: str = "output.ttl") -> str:
        """Export in-memory triples to Turtle format"""
        if self.triples_df is None or self.triples_df.empty:
            raise ValueError("No data to export")

        graph = self._dataframe_to_rdf(self.triples_df)
        filepath = os.path.join(self.storage_path, filename)
        graph.serialize(filepath, format="turtle")
        logger.info(f"Exported to {filepath}")
        return filepath

    def merge_graphs(self, filename1: str, filename2: str) -> str:
        """Merge two graphs and store as new file"""
        graph1 = self.load_graph(filename1)
        graph2 = self.load_graph(filename2)

        merged_graph = graph1 + graph2
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"merged_{timestamp}.parquet"
        return self.store_graph(merged_graph, new_filename)

    def delete_file(self, filename: str) -> bool:
        """Delete a specific Parquet file"""
        filepath = os.path.join(self.storage_path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted {filename}")
            return True
        return False


class ParquetTripleStoreWithIndex(ParquetTripleStore):
    """Extended version with indexing for faster queries"""

    def __init__(self, configuration=None):
        ParquetTripleStore.__init__(self, configuration)
        self.subject_index = None
        self.predicate_index = None
        self.o_index = None

    def triples(self, triple, context=None):
        """Iterate over triples in the store using index"""
        if self.triples_df is None:
            self.load_all_graphs()

        for _, row in self.triples_df.iterrows():
            if (
                (triple[0] is None or row["s"] == str(triple[0]))
                and (triple[1] is None or row["p"] == str(triple[1]))
                and (triple[2] is None or row["o"] == str(triple[2]))
            ):
                obj = (
                    Literal(row["o"])
                    if row.get("object_type") == "literal"
                    else URIRef(row["o"])
                )
                yield (URIRef(row["s"]), URIRef(row["p"]), obj), context

    def _create_indexes(self):
        """Create indexes for faster queries"""
        if self.triples_df is not None:
            self.subject_index = self.triples_df.set_index("s")
            self.predicate_index = self.triples_df.set_index("p")
            self.o_index = self.triples_df.set_index("o")

    def find_by_subject(self, subject_uri: str) -> pd.DataFrame:
        """Find all triples with a specific subject"""
        if self.triples_df is None:
            self.load_all_graphs()
        if self.subject_index is None:
            self._create_indexes()

        return self.subject_index.loc[[subject_uri]]

    def find_by_predicate(self, predicate_uri: str) -> pd.DataFrame:
        """Find all triples with a specific predicate"""
        if self.triples_df is None:
            self.load_all_graphs()
        if self.predicate_index is None:
            self._create_indexes()

        return self.predicate_index.loc[[predicate_uri]]

    def find_triples(
        self, subject: str = None, predicate: str = None, object: str = None
    ) -> pd.DataFrame:
        """Find triples matching given criteria"""
        if self.triples_df is None:
            self.load_all_graphs()

        mask = pd.Series(True, index=self.triples_df.index)

        if subject is not None:
            mask &= self.triples_df["s"] == subject
        if predicate is not None:
            mask &= self.triples_df["p"] == predicate
        if object is not None:
            mask &= self.triples_df["o"] == object

        return self.triples_df[mask]

    def load_all_graphs(self):
        """Load all graphs and create indexes"""
        df = super().load_all_graphs()
        if df is not None and not df.empty:
            self._create_indexes()
        return df
