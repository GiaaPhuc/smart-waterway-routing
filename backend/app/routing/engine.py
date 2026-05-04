import logging
import math
from typing import Any, Dict, List, Optional

import networkx as nx

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two WGS-84 points."""
    R = 6_371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return _haversine_km(lat1, lon1, lat2, lon2) * 1000.0


class RoutingEngine:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _astar_heuristic(self, u: int, v: int) -> float:
        """Haversine distance (metres) used as A* heuristic."""
        u_data = self.graph.nodes[u]
        v_data = self.graph.nodes[v]
        return _haversine_m(u_data["lat"], u_data["lon"], v_data["lat"], v_data["lon"])

    def _nearest_node(self, lat: float, lon: float) -> Optional[int]:
        best_id = None
        best_dist = float("inf")
        for node_id, data in self.graph.nodes(data=True):
            d = _haversine_m(lat, lon, data["lat"], data["lon"])
            if d < best_dist:
                best_dist = d
                best_id = node_id
        return best_id

    def _build_route_dict(self, path: List[int]) -> Dict[str, Any]:
        """Convert a node-id path into the standard route response dict."""
        waypoints: List[Dict[str, float]] = []
        edges: List[Dict[str, Any]] = []
        total_distance_m = 0.0

        for node_id in path:
            data = self.graph.nodes[node_id]
            waypoints.append({"lat": data["lat"], "lon": data["lon"]})

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            edge_data = self.graph.edges[u, v]
            length = edge_data.get(
                "length",
                _haversine_m(u_data["lat"], u_data["lon"], v_data["lat"], v_data["lon"]),
            )
            total_distance_m += length
            edges.append(
                {
                    "from": u,
                    "to": v,
                    "lat": u_data["lat"],
                    "lon": u_data["lon"],
                    "length": length,
                    "name": edge_data.get("name", ""),
                    "waterway_type": edge_data.get("waterway_type", "unknown"),
                    "navigable": edge_data.get("navigable", False),
                }
            )

        return {
            "path": path,
            "edges": edges,
            "total_distance": total_distance_m,
            "waypoints": waypoints,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_route(
        self,
        start_node: int,
        end_node: int,
        algorithm: str = "astar",
    ) -> Dict[str, Any]:
        """Find a route between two graph nodes.

        Returns a dict with keys: path, edges, total_distance, waypoints.
        Raises ValueError if no path exists.
        """
        if self.graph.number_of_nodes() == 0:
            raise ValueError("Graph is empty – no route possible.")

        try:
            if algorithm == "dijkstra":
                path = nx.dijkstra_path(self.graph, start_node, end_node, weight="length")
            else:
                path = nx.astar_path(
                    self.graph,
                    start_node,
                    end_node,
                    heuristic=self._astar_heuristic,
                    weight="length",
                )
        except nx.NetworkXNoPath:
            raise ValueError(
                f"No waterway path found between nodes {start_node} and {end_node}."
            )
        except nx.NodeNotFound as exc:
            raise ValueError(str(exc))

        logger.info(
            "Route found via %s: %d nodes, algorithm=%s",
            start_node,
            len(path),
            algorithm,
        )
        return self._build_route_dict(path)

    def find_route_by_coords(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        algorithm: str = "astar",
    ) -> Dict[str, Any]:
        """Find a route between two geographic coordinates."""
        start_node = self._nearest_node(start_lat, start_lon)
        end_node = self._nearest_node(end_lat, end_lon)

        if start_node is None or end_node is None:
            raise ValueError("Could not find nearest nodes for the given coordinates.")

        logger.info(
            "Routing (%.5f, %.5f) -> (%.5f, %.5f) | nearest nodes: %s -> %s",
            start_lat, start_lon, end_lat, end_lon, start_node, end_node,
        )
        return self.find_route(start_node, end_node, algorithm=algorithm)

    def get_route_stats(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary statistics for a route dict."""
        edges = route.get("edges", [])
        total_distance_m = route.get("total_distance", 0.0)

        waterway_types: Dict[str, int] = {}
        navigable_count = 0
        for edge in edges:
            wt = edge.get("waterway_type", "unknown")
            waterway_types[wt] = waterway_types.get(wt, 0) + 1
            if edge.get("navigable"):
                navigable_count += 1

        return {
            "total_distance_km": round(total_distance_m / 1000, 3),
            "total_distance_m": round(total_distance_m, 1),
            "segment_count": len(edges),
            "waypoint_count": len(route.get("waypoints", [])),
            "waterway_types": waterway_types,
            "navigable_segments": navigable_count,
        }
