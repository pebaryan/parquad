#!/usr/bin/env python3
"""Generate synthetic Turtle + Parquet data and SPARQL benchmark queries."""

import argparse
import os
import random
from datetime import datetime, timedelta

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from parquet_triple_store import ParquetTripleStore


def make_uri(base, *parts):
    return URIRef("/".join([base.rstrip("/")] + [str(p).strip("/") for p in parts]))


def write_query(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")


def generate_data(
    out_dir, runs, tasks_per_run, events_per_run, seed, base_ns
):
    random.seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    g = Graph()
    ns = base_ns.rstrip("/")
    g.bind("ex", ns)

    process = make_uri(ns, "process", "main")
    g.add((process, RDF.type, make_uri(ns, "bpmn", "Process")))

    task_ids = [f"Task_{i}" for i in range(tasks_per_run)]
    for tid in task_ids:
        task = make_uri(ns, "task", tid)
        g.add((task, RDF.type, make_uri(ns, "bpmn", "Task")))
        g.add((process, make_uri(ns, "bpmn", "hasTask"), task))

    start_time = datetime(2024, 1, 1, 0, 0, 0)

    for run_id in range(runs):
        trace = make_uri(ns, "trace", run_id)
        g.add((trace, RDF.type, make_uri(ns, "bpmn", "Trace")))
        g.add((trace, make_uri(ns, "bpmn", "traceId"), Literal(run_id, datatype=XSD.integer)))

        run_start = start_time + timedelta(minutes=run_id)
        for ev_idx in range(events_per_run):
            event = make_uri(ns, "event", f"{run_id}_{ev_idx}")
            g.add((event, RDF.type, make_uri(ns, "bpmn", "Event")))
            g.add((trace, make_uri(ns, "bpmn", "hasEvent"), event))

            task = make_uri(ns, "task", random.choice(task_ids))
            g.add((event, make_uri(ns, "bpmn", "forTask"), task))
            g.add((event, make_uri(ns, "bpmn", "eventIndex"), Literal(ev_idx, datatype=XSD.integer)))

            ts = run_start + timedelta(seconds=ev_idx * random.randint(1, 10))
            g.add((event, make_uri(ns, "bpmn", "timestamp"), Literal(ts.isoformat(), datatype=XSD.dateTime)))

            duration_ms = random.randint(50, 2000)
            g.add((event, make_uri(ns, "bpmn", "durationMs"), Literal(duration_ms, datatype=XSD.integer)))

    turtle_path = os.path.join(out_dir, "synthetic_benchmark.ttl")
    g.serialize(destination=turtle_path, format="turtle")

    store = ParquetTripleStore({"storage_path": out_dir})
    parquet_path = store.store_graph(g, "synthetic_benchmark.parquet")

    return turtle_path, parquet_path


def generate_queries(out_dir, base_ns):
    ns = base_ns.rstrip("/")
    queries = {}

    queries["count_all.rq"] = f"""
SELECT (COUNT(?s) AS ?count)
WHERE {{
  ?s ?p ?o .
}}
"""

    queries["events_for_trace.rq"] = f"""
SELECT ?event
WHERE {{
  <{ns}/trace/0> <{ns}/bpmn/hasEvent> ?event .
}}
"""

    queries["events_by_task.rq"] = f"""
SELECT ?event
WHERE {{
  ?event <{ns}/bpmn/forTask> <{ns}/task/Task_0> .
}}
"""

    queries["avg_duration_by_task.rq"] = f"""
SELECT ?task (AVG(?d) AS ?avgDuration)
WHERE {{
  ?event <{ns}/bpmn/forTask> ?task .
  ?event <{ns}/bpmn/durationMs> ?d .
}}
GROUP BY ?task
"""

    queries["events_in_time_window.rq"] = f"""
SELECT ?event
WHERE {{
  ?event <{ns}/bpmn/timestamp> ?ts .
  FILTER(?ts >= "2024-01-01T00:10:00"^^xsd:dateTime &&
         ?ts <= "2024-01-01T00:20:00"^^xsd:dateTime)
}}
"""

    query_dir = os.path.join(out_dir, "queries")
    os.makedirs(query_dir, exist_ok=True)

    for name, text in queries.items():
        write_query(os.path.join(query_dir, name), text)

    return query_dir


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic Turtle + Parquet benchmark data and queries."
    )
    parser.add_argument("--out-dir", default="benchmark_data")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--tasks", type=int, default=25)
    parser.add_argument("--events-per-run", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-ns", default="http://example.org/bpmn")
    args = parser.parse_args()

    turtle_path, parquet_path = generate_data(
        args.out_dir,
        args.runs,
        args.tasks,
        args.events_per_run,
        args.seed,
        args.base_ns,
    )
    query_dir = generate_queries(args.out_dir, args.base_ns)

    print("Generated synthetic benchmark data:")
    print(f"- Turtle:  {turtle_path}")
    print(f"- Parquet: {parquet_path}")
    print(f"- Queries: {query_dir}")


if __name__ == "__main__":
    main()
