import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Smart Waterway Routing API – route planning on inland waterways.",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    # --- Load or build the waterway graph ---
    from app.data_pipeline.graph_builder import WaterwayGraphBuilder
    from app.routing.engine import RoutingEngine

    builder = WaterwayGraphBuilder()
    graph = builder.load_graph(settings.GRAPH_CACHE_FILE)

    if graph is None:
        logger.info("No cached graph found – attempting OSM fetch…")
        from app.data_pipeline.osm_fetcher import WaterwayFetcher
        import networkx as nx

        fetcher = WaterwayFetcher()
        osm_data = None

        # Try loading from OSM cache first
        if os.path.exists(settings.OSM_CACHE_FILE):
            osm_data = fetcher.load_from_file(settings.OSM_CACHE_FILE)

        if osm_data is None or not osm_data.get("elements"):
            logger.info("Fetching OSM data for area: %s", settings.OSM_AREA)
            osm_data = fetcher.fetch_waterways(settings.OSM_AREA)
            if osm_data.get("elements"):
                fetcher.save_to_file(osm_data, settings.OSM_CACHE_FILE)

        if osm_data and osm_data.get("elements"):
            graph = builder.build_graph(osm_data)
            builder.save_graph(graph, settings.GRAPH_CACHE_FILE)
        else:
            logger.warning(
                "OSM fetch returned no data – starting with empty graph. "
                "Call POST /api/graph/reload to retry."
            )
            import networkx as nx
            graph = nx.DiGraph()

    app.state.graph = graph
    app.state.routing_engine = RoutingEngine(graph)
    logger.info(
        "Waterway graph ready: %d nodes, %d edges",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )

    # --- Load ML model ---
    from app.ml.eta_model import ETAModel

    eta_model = ETAModel()
    eta_model.load(settings.MODEL_PATH)
    app.state.eta_model = eta_model

    if eta_model.is_loaded():
        logger.info("ETA model loaded from %s", settings.MODEL_PATH)
    else:
        logger.warning(
            "ETA model not found at %s – formula fallback will be used. "
            "Run scripts/init_data.py to train the model.",
            settings.MODEL_PATH,
        )


# ---------------------------------------------------------------------------
# Health check (root-level convenience alias)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    graph = getattr(app.state, "graph", None)
    model = getattr(app.state, "eta_model", None)
    return {
        "status": "ok",
        "graph_loaded": graph is not None and graph.number_of_nodes() > 0,
        "model_loaded": model is not None and model.is_loaded(),
    }
