import json
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# bbox order for Overpass QL is (south,west,north,east)
WATERWAY_QUERY_BBOX = """\
[out:json][timeout:{timeout}];
(
  way["waterway"~"river|canal|stream|drain|creek"]({south},{west},{north},{east});
  >;
);
out body;
"""

WATERWAY_QUERY_AREA = """\
[out:json][timeout:{timeout}];
area["name"="{area_name}"]->.searchArea;
(
  way["waterway"~"river|canal|stream|drain|creek"](area.searchArea);
  >;
);
out body;
"""

_REQUEST_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "SmartWaterwayRouting/1.0",
}


class WaterwayFetcher:
    def __init__(self, api_url: str = OVERPASS_MIRRORS[0], timeout: int = 120):
        self.api_url = api_url
        self.timeout = timeout

    def fetch_waterways(self, area_name: str) -> dict:
        """Fetch waterway data for a named area via Overpass API."""
        query = WATERWAY_QUERY_AREA.format(area_name=area_name, timeout=self.timeout)
        logger.info("Fetching waterways for area: %s", area_name)
        return self._execute_query(query)

    def fetch_waterways_bbox(
        self, north: float, south: float, east: float, west: float
    ) -> dict:
        """Fetch waterway data within a bounding box via Overpass API."""
        query = WATERWAY_QUERY_BBOX.format(
            north=north, south=south, east=east, west=west, timeout=self.timeout
        )
        logger.info(
            "Fetching waterways for bbox: N=%.4f S=%.4f E=%.4f W=%.4f",
            north, south, east, west,
        )
        return self._execute_query(query)

    def _execute_query(self, query: str) -> dict:
        """Execute an Overpass QL query, trying each mirror in turn."""
        mirrors = [self.api_url] + [m for m in OVERPASS_MIRRORS if m != self.api_url]
        for mirror in mirrors:
            result = self._try_mirror(mirror, query)
            if result.get("elements"):
                return result
            logger.warning("Mirror %s returned no data, trying next…", mirror)
        logger.error("All Overpass mirrors exhausted – returning empty dataset")
        return self._empty_result()

    def _try_mirror(self, url: str, query: str) -> dict:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers=_REQUEST_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            elements = data.get("elements", [])
            nodes = [e for e in elements if e["type"] == "node"]
            ways = [e for e in elements if e["type"] == "way"]
            logger.info(
                "Fetched %d nodes and %d ways from %s",
                len(nodes), len(ways), url,
            )
            return data
        except requests.exceptions.Timeout:
            logger.warning("Overpass mirror %s timed out after %d s", url, self.timeout)
            return self._empty_result()
        except requests.exceptions.RequestException as exc:
            logger.warning("Overpass mirror %s failed: %s", url, exc)
            return self._empty_result()
        except (ValueError, KeyError) as exc:
            logger.warning("Failed to parse response from %s: %s", url, exc)
            return self._empty_result()

    @staticmethod
    def _empty_result() -> dict:
        return {"version": 0.6, "elements": []}

    def save_to_file(self, data: dict, filepath: str) -> None:
        """Persist OSM data to a JSON file for caching."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        logger.info("Saved OSM data to %s", filepath)

    def load_from_file(self, filepath: str) -> Optional[dict]:
        """Load cached OSM data from a JSON file. Returns None if missing."""
        if not os.path.exists(filepath):
            logger.warning("OSM cache file not found: %s", filepath)
            return None
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        elements = data.get("elements", [])
        logger.info("Loaded %d OSM elements from %s", len(elements), filepath)
        return data
