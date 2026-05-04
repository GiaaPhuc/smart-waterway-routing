import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RouteRequest(BaseModel):
    start_lat: float = Field(..., ge=-90, le=90, description="Start latitude")
    start_lon: float = Field(..., ge=-180, le=180, description="Start longitude")
    end_lat: float = Field(..., ge=-90, le=90, description="End latitude")
    end_lon: float = Field(..., ge=-180, le=180, description="End longitude")
    algorithm: Literal["astar", "dijkstra"] = "astar"
    vessel_type: Literal[0, 1, 2] = Field(
        0, description="0=small, 1=medium, 2=large"
    )
    speed_knots: float = Field(7.0, gt=0, le=30, description="Vessel speed in knots")


class Waypoint(BaseModel):
    lat: float
    lon: float


class RouteInfo(BaseModel):
    waypoints: List[Waypoint]
    total_distance_km: float
    segments: int


class ETAInfo(BaseModel):
    minutes: float
    hours: float
    arrival_time: str


class RouteResponse(BaseModel):
    route: RouteInfo
    eta: ETAInfo


class GraphInfoResponse(BaseModel):
    nodes: int
    edges: int
    area: str
    loaded: bool


class HealthResponse(BaseModel):
    status: str
    graph_loaded: bool
    model_loaded: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None or graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=503,
            detail="Waterway graph is not loaded. Please call POST /api/graph/reload first.",
        )
    return graph


def _get_engine(request: Request):
    engine = getattr(request.app.state, "routing_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Routing engine is not available.",
        )
    return engine


def _get_model(request: Request):
    return getattr(request.app.state, "eta_model", None)


def _reload_graph_background(app_state, settings):
    """Background task: fetch OSM data, rebuild graph, persist to disk."""
    import os

    from app.data_pipeline.graph_builder import WaterwayGraphBuilder
    from app.data_pipeline.osm_fetcher import WaterwayFetcher
    from app.routing.engine import RoutingEngine

    logger.info("Background graph reload started")
    fetcher = WaterwayFetcher()
    builder = WaterwayGraphBuilder()

    osm_cache = settings.OSM_CACHE_FILE
    graph_cache = settings.GRAPH_CACHE_FILE

    data = fetcher.fetch_waterways(settings.OSM_AREA)
    if not data.get("elements"):
        cached = fetcher.load_from_file(osm_cache)
        data = cached if cached else data

    fetcher.save_to_file(data, osm_cache)
    graph = builder.build_graph(data)
    builder.save_graph(graph, graph_cache)

    app_state.graph = graph
    app_state.routing_engine = RoutingEngine(graph)
    logger.info("Background graph reload complete: %d nodes", graph.number_of_nodes())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/route", response_model=RouteResponse)
async def compute_route(body: RouteRequest, request: Request) -> RouteResponse:
    """Compute the shortest waterway route between two coordinates."""
    _get_graph(request)  # raises 503 if not loaded
    engine = _get_engine(request)
    model = _get_model(request)

    try:
        route = engine.find_route_by_coords(
            body.start_lat, body.start_lon,
            body.end_lat, body.end_lon,
            algorithm=body.algorithm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    stats = engine.get_route_stats(route)
    distance_km = stats["total_distance_km"]
    num_segments = stats["segment_count"]

    now = datetime.now(timezone.utc)
    hour = now.hour

    if model and model.is_loaded():
        features = {
            "distance_km": distance_km,
            "vessel_type": body.vessel_type,
            "speed_knots": body.speed_knots,
            "num_segments": num_segments,
            "time_of_day": hour,
            "season": _month_to_season(now.month),
        }
        eta_minutes = model.predict(features)
    else:
        # Physics fallback
        speed_kmh = body.speed_knots * 1.852
        vessel_factor = {0: 1.0, 1: 1.1, 2: 1.2}.get(body.vessel_type, 1.0)
        eta_minutes = (distance_km / max(speed_kmh, 0.1)) * 60.0 * vessel_factor

    arrival_dt = now + timedelta(minutes=eta_minutes)
    arrival_str = arrival_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    waypoints = [Waypoint(lat=wp["lat"], lon=wp["lon"]) for wp in route["waypoints"]]

    return RouteResponse(
        route=RouteInfo(
            waypoints=waypoints,
            total_distance_km=distance_km,
            segments=num_segments,
        ),
        eta=ETAInfo(
            minutes=round(eta_minutes, 2),
            hours=round(eta_minutes / 60, 3),
            arrival_time=arrival_str,
        ),
    )


@router.get("/graph/info", response_model=GraphInfoResponse)
async def graph_info(request: Request) -> GraphInfoResponse:
    """Return basic statistics about the loaded waterway graph."""
    from app.core.config import settings

    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        return GraphInfoResponse(nodes=0, edges=0, area=settings.OSM_AREA, loaded=False)
    return GraphInfoResponse(
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        area=settings.OSM_AREA,
        loaded=graph.number_of_nodes() > 0,
    )


@router.post("/graph/reload")
async def reload_graph(
    request: Request, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Trigger a background re-fetch of OSM data and graph rebuild."""
    from app.core.config import settings

    background_tasks.add_task(
        _reload_graph_background, request.app.state, settings
    )
    return {"status": "reload started", "message": "Graph reload triggered in background."}


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    graph = getattr(request.app.state, "graph", None)
    model = getattr(request.app.state, "eta_model", None)
    return HealthResponse(
        status="ok",
        graph_loaded=graph is not None and graph.number_of_nodes() > 0,
        model_loaded=model is not None and model.is_loaded(),
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _month_to_season(month: int) -> int:
    """Map calendar month (1-12) to season (1-4)."""
    return {
        12: 1, 1: 1, 2: 1,  # Winter
        3: 2, 4: 2, 5: 2,   # Spring
        6: 3, 7: 3, 8: 3,   # Summer
        9: 4, 10: 4, 11: 4, # Autumn
    }.get(month, 1)
