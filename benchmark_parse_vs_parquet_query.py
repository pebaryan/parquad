#!/usr/bin/env python3
"""Benchmark: parse Turtle vs load Parquet then run SPARQL query."""

import argparse
import os
import statistics
import time
import tempfile

from rdflib import Graph

from parquet_triple_store import ParquetTripleStore
from generate_synthetic_benchmark_data import generate_data, generate_queries


def read_query(args):
    if args.query_file:
        with open(args.query_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if args.query:
        return args.query
    return "SELECT (COUNT(?s) AS ?count) WHERE { ?s ?p ?o }"


def time_once(fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    return elapsed, result


def parse_and_query(turtle_path, query_str):
    g = Graph()
    g.parse(turtle_path, format="turtle")
    results = list(g.query(query_str))
    return len(results)


def load_parquet_and_query(store, parquet_filename, query_str):
    g = store.load_graph(parquet_filename)
    results = list(g.query(query_str))
    return len(results)


def run_benchmark(turtle_path, query_str, runs, parquet_path):
    results = {
        "parse_query_times": [],
        "parquet_query_times": [],
        "parse_query_counts": [],
        "parquet_query_counts": [],
    }

    # Prepare Parquet file if not provided.
    if parquet_path is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ParquetTripleStore({"storage_path": temp_dir})
            graph = Graph()
            graph.parse(turtle_path, format="turtle")
            parquet_filepath = store.store_graph(graph, "benchmark_data.parquet")
            parquet_filename = os.path.basename(parquet_filepath)
            store = ParquetTripleStore({"storage_path": temp_dir})

            for _ in range(runs):
                t_parse, c_parse = time_once(
                    lambda: parse_and_query(turtle_path, query_str)
                )
                t_parquet, c_parquet = time_once(
                    lambda: load_parquet_and_query(
                        store, parquet_filename, query_str
                    )
                )
                results["parse_query_times"].append(t_parse)
                results["parquet_query_times"].append(t_parquet)
                results["parse_query_counts"].append(c_parse)
                results["parquet_query_counts"].append(c_parquet)
    else:
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
        storage_dir = os.path.dirname(parquet_path) or "."
        parquet_filename = os.path.basename(parquet_path)
        store = ParquetTripleStore({"storage_path": storage_dir})

        for _ in range(runs):
            t_parse, c_parse = time_once(lambda: parse_and_query(turtle_path, query_str))
            t_parquet, c_parquet = time_once(
                lambda: load_parquet_and_query(store, parquet_filename, query_str)
            )
            results["parse_query_times"].append(t_parse)
            results["parquet_query_times"].append(t_parquet)
            results["parse_query_counts"].append(c_parse)
            results["parquet_query_counts"].append(c_parquet)

    return results


def summarize(label, times):
    return {
        "label": label,
        "avg": statistics.mean(times),
        "min": min(times),
        "max": max(times),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark parsing Turtle vs loading Parquet before SPARQL query."
    )
    parser.add_argument(
        "turtle",
        nargs="?",
        help="Path to Turtle (.ttl) file (omit when using --generate)",
    )
    parser.add_argument(
        "--parquet",
        help="Optional existing Parquet file to load instead of creating one",
        default=None,
    )
    parser.add_argument(
        "--query",
        help="SPARQL query string (default: COUNT all triples)",
        default=None,
    )
    parser.add_argument(
        "--query-file",
        help="Path to file containing SPARQL query",
        default=None,
    )
    parser.add_argument(
        "--runs",
        help="Number of runs (default: 5)",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--generate",
        help="Generate synthetic data and queries before running benchmark",
        action="store_true",
    )
    parser.add_argument("--out-dir", default="benchmark_data")
    parser.add_argument("--gen-runs", type=int, default=100)
    parser.add_argument("--gen-tasks", type=int, default=25)
    parser.add_argument("--gen-events-per-run", type=int, default=50)
    parser.add_argument("--gen-seed", type=int, default=42)
    parser.add_argument("--gen-base-ns", default="http://example.org/bpmn")
    args = parser.parse_args()

    if args.generate:
        turtle_path, parquet_path = generate_data(
            args.out_dir,
            args.gen_runs,
            args.gen_tasks,
            args.gen_events_per_run,
            args.gen_seed,
            args.gen_base_ns,
        )
        generate_queries(args.out_dir, args.gen_base_ns)
        if args.turtle is None:
            args.turtle = turtle_path
        if args.parquet is None:
            args.parquet = parquet_path

    if args.turtle is None:
        raise SystemExit("Turtle file is required (or use --generate).")

    query_str = read_query(args)
    results = run_benchmark(args.turtle, query_str, args.runs, args.parquet)

    parse_summary = summarize("Parse Turtle + Query", results["parse_query_times"])
    parquet_summary = summarize("Load Parquet + Query", results["parquet_query_times"])

    print("\n" + "=" * 70)
    print("Benchmark: Parse Turtle vs Load Parquet then Query")
    print("=" * 70)
    print(f"Turtle file: {args.turtle}")
    if args.parquet:
        print(f"Parquet file: {args.parquet}")
    else:
        print("Parquet file: generated from Turtle for this run")
    print(f"Runs: {args.runs}")
    print(f"Query: {query_str}")

    print("\nResults (seconds):")
    print(
        f"- {parse_summary['label']}: avg {parse_summary['avg']:.4f}, "
        f"min {parse_summary['min']:.4f}, max {parse_summary['max']:.4f}"
    )
    print(
        f"- {parquet_summary['label']}: avg {parquet_summary['avg']:.4f}, "
        f"min {parquet_summary['min']:.4f}, max {parquet_summary['max']:.4f}"
    )

    if results["parse_query_counts"] and results["parquet_query_counts"]:
        print(
            f"\nResult counts (last run): parse={results['parse_query_counts'][-1]}, "
            f"parquet={results['parquet_query_counts'][-1]}"
        )

    ratio = parse_summary["avg"] / parquet_summary["avg"]
    print(f"\nAvg ratio (parse/parquet): {ratio:.2f}x")
    print("=" * 70)


if __name__ == "__main__":
    main()
