#!/usr/bin/env python
"""
init_data.py
------------
Bootstrap script for the Smart Waterway Routing backend.

Steps:
  1. Fetch OSM waterway data for the Mekong Delta region via Overpass API.
  2. Build a NetworkX directed graph from the OSM data.
  3. Train an ETA prediction model on synthetic data.
  4. Save all artefacts to the backend/data/ directory.
  5. Print summary statistics.

Usage (from the backend/ directory):
    python scripts/init_data.py
"""

import logging
import os
import sys
import time

# Make sure the backend/ package is importable when running the script directly.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OSM_CACHE_FILE = os.path.join(DATA_DIR, "osm_waterways.json")
GRAPH_CACHE_FILE = os.path.join(DATA_DIR, "waterway_graph.pkl")
MODEL_PATH = os.path.join(DATA_DIR, "eta_model.joblib")

# Mekong Delta bounding box
BBOX = {
    "north": 11.5,
    "south": 9.0,
    "east": 106.8,
    "west": 104.5,
}


def step_fetch_osm() -> dict:
    from app.data_pipeline.osm_fetcher import WaterwayFetcher

    logger.info("=" * 60)
    logger.info("STEP 1 – Fetching OSM waterway data (Mekong Delta)")
    logger.info("  BBox: N=%.1f S=%.1f E=%.1f W=%.1f", BBOX["north"], BBOX["south"], BBOX["east"], BBOX["west"])

    fetcher = WaterwayFetcher(timeout=180)
    t0 = time.time()

    # Use cache if fresh (< 24 h old) to avoid hammering Overpass
    if os.path.exists(OSM_CACHE_FILE):
        age_h = (time.time() - os.path.getmtime(OSM_CACHE_FILE)) / 3600
        if age_h < 24:
            logger.info("  Cache is %.1f h old – loading from disk", age_h)
            data = fetcher.load_from_file(OSM_CACHE_FILE)
            if data and data.get("elements"):
                logger.info("  Loaded %d elements from cache", len(data["elements"]))
                return data

    data = fetcher.fetch_waterways_bbox(**BBOX)
    elapsed = time.time() - t0

    if not data.get("elements"):
        logger.warning("  Overpass returned no data (%.1f s). Trying cache…", elapsed)
        cached = fetcher.load_from_file(OSM_CACHE_FILE)
        if cached and cached.get("elements"):
            logger.info("  Loaded %d elements from stale cache", len(cached["elements"]))
            return cached
        logger.warning("  No cache available either – proceeding with empty dataset")
        return data

    nodes = [e for e in data["elements"] if e["type"] == "node"]
    ways = [e for e in data["elements"] if e["type"] == "way"]
    logger.info(
        "  Fetched %d nodes, %d ways in %.1f s",
        len(nodes), len(ways), elapsed,
    )

    fetcher.save_to_file(data, OSM_CACHE_FILE)
    logger.info("  Saved to %s", OSM_CACHE_FILE)
    return data


def step_build_graph(osm_data: dict):
    import networkx as nx
    from app.data_pipeline.graph_builder import WaterwayGraphBuilder

    logger.info("=" * 60)
    logger.info("STEP 2 – Building waterway graph")

    builder = WaterwayGraphBuilder()
    t0 = time.time()
    graph = builder.build_graph(osm_data)
    elapsed = time.time() - t0

    logger.info(
        "  Graph: %d nodes, %d edges (%.2f s)",
        graph.number_of_nodes(), graph.number_of_edges(), elapsed,
    )

    builder.save_graph(graph, GRAPH_CACHE_FILE)
    logger.info("  Saved to %s", GRAPH_CACHE_FILE)

    # Extra stats
    if graph.number_of_nodes() > 0:
        wcc = nx.number_weakly_connected_components(graph)
        logger.info("  Weakly connected components: %d", wcc)

    return graph


def step_train_model():
    from app.ml.trainer import train_eta_model

    logger.info("=" * 60)
    logger.info("STEP 3 – Training ETA model")

    t0 = time.time()
    model, metrics = train_eta_model(model_path=MODEL_PATH)
    elapsed = time.time() - t0

    logger.info("  MAE  = %.3f min", metrics["mae"])
    logger.info("  RMSE = %.3f min", metrics["rmse"])
    logger.info("  Saved to %s (%.1f s)", MODEL_PATH, elapsed)
    return model, metrics


def print_summary(graph, metrics):
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("  Graph nodes  : %d", graph.number_of_nodes())
    logger.info("  Graph edges  : %d", graph.number_of_edges())
    logger.info("  ETA model MAE : %.3f min", metrics["mae"])
    logger.info("  ETA model RMSE: %.3f min", metrics["rmse"])
    logger.info("  Data directory: %s", DATA_DIR)
    logger.info("=" * 60)
    logger.info("Initialisation complete. You can now start the API server:")
    logger.info("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    osm_data = step_fetch_osm()
    graph = step_build_graph(osm_data)
    model, metrics = step_train_model()
    print_summary(graph, metrics)


if __name__ == "__main__":
    main()
