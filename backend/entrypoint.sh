#!/bin/sh
set -e

DATA_DIR="${DATA_DIR:-/app/data}"
MODEL_PATH="${MODEL_PATH:-$DATA_DIR/eta_model.joblib}"
GRAPH_PATH="${GRAPH_PATH:-$DATA_DIR/waterway_graph.pkl}"
OSM_CACHE="${OSM_CACHE:-$DATA_DIR/osm_waterways.json}"

mkdir -p "$DATA_DIR"

# Check if graph pickle exists and has at least one node
GRAPH_EMPTY=0
if [ ! -f "$GRAPH_PATH" ]; then
    GRAPH_EMPTY=1
elif ! python -c "import sys,pickle; g=pickle.load(open('$GRAPH_PATH','rb')); sys.exit(0 if g.number_of_nodes()>0 else 1)" 2>/dev/null; then
    GRAPH_EMPTY=1
fi

# Also re-init if OSM cache is missing (means last fetch failed)
OSM_MISSING=0
if [ ! -f "$OSM_CACHE" ]; then
    OSM_MISSING=1
fi

if [ ! -f "$MODEL_PATH" ] || [ "$GRAPH_EMPTY" = "1" ] || [ "$OSM_MISSING" = "1" ]; then
    echo "=== Initialising data (model/graph missing or empty) ==="
    python scripts/init_data.py
    echo "=== Data initialisation complete ==="
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
