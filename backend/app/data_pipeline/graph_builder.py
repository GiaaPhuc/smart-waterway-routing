import logging
import math
import os
import pickle
from typing import Dict, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in metres between two WGS-84 points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Waterway types that are generally navigable
_NAVIGABLE_TYPES = {"river", "canal", "drain"}


class WaterwayGraphBuilder:
    def build_graph(self, osm_data: dict) -> nx.DiGraph:
        """Build a directed NetworkX graph from raw Overpass API JSON.

        Nodes carry ``lat`` and ``lon`` attributes.
        Directed edges carry ``length`` (m), ``name``, ``waterway_type``,
        ``navigable``, and ``width`` (if available from OSM tags).
        """
        elements = osm_data.get("elements", [])

        # Index nodes by OSM id
        node_index: Dict[int, dict] = {}
        for el in elements:
            if el["type"] == "node":
                node_index[el["id"]] = el

        G = nx.DiGraph()

        ways = [el for el in elements if el["type"] == "way"]
        logger.info("Building graph from %d nodes and %d ways", len(node_index), len(ways))

        for way in ways:
            tags = way.get("tags", {})
            waterway_type = tags.get("waterway", "unknown")
            name = tags.get("name", "")
            navigable = waterway_type in _NAVIGABLE_TYPES
            width_str = tags.get("width", None)
            width: Optional[float] = None
            if width_str:
                try:
                    width = float(width_str)
                except ValueError:
                    pass

            node_refs = way.get("nodes", [])
            for n_id in node_refs:
                if n_id in node_index:
                    n = node_index[n_id]
                    if not G.has_node(n_id):
                        G.add_node(n_id, lat=n["lat"], lon=n["lon"])

            for i in range(len(node_refs) - 1):
                u_id = node_refs[i]
                v_id = node_refs[i + 1]
                if u_id not in node_index or v_id not in node_index:
                    continue
                u = node_index[u_id]
                v = node_index[v_id]
                length = _haversine_m(u["lat"], u["lon"], v["lat"], v["lon"])
                edge_attrs = {
                    "length": length,
                    "name": name,
                    "waterway_type": waterway_type,
                    "navigable": navigable,
                    "width": width,
                }
                G.add_edge(u_id, v_id, **edge_attrs)
                # Add reverse edge for bidirectional waterways (rivers/canals)
                G.add_edge(v_id, u_id, **edge_attrs)

        logger.info(
            "Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges()
        )
        return G

    def save_graph(self, graph: nx.DiGraph, filepath: str) -> None:
        """Persist the graph as a pickle file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "wb") as fh:
            pickle.dump(graph, fh, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(
            "Saved graph (%d nodes, %d edges) to %s",
            graph.number_of_nodes(),
            graph.number_of_edges(),
            filepath,
        )

    def load_graph(self, filepath: str) -> Optional[nx.DiGraph]:
        """Load a pickled graph from disk. Returns None if the file is absent."""
        if not os.path.exists(filepath):
            logger.warning("Graph cache file not found: %s", filepath)
            return None
        with open(filepath, "rb") as fh:
            graph = pickle.load(fh)
        logger.info(
            "Loaded graph (%d nodes, %d edges) from %s",
            graph.number_of_nodes(),
            graph.number_of_edges(),
            filepath,
        )
        return graph

    def get_nearest_node(
        self, graph: nx.DiGraph, lat: float, lon: float
    ) -> Optional[int]:
        """Return the node id whose position is closest to (lat, lon)."""
        if graph.number_of_nodes() == 0:
            return None
        best_id = None
        best_dist = float("inf")
        for node_id, data in graph.nodes(data=True):
            d = _haversine_m(lat, lon, data["lat"], data["lon"])
            if d < best_dist:
                best_dist = d
                best_id = node_id
        return best_id
