"""
seed_opensearch.py
Jal-Drishti — OpenSearch Index Initializer & Urban Water Kiosk Seeder
Centered near Connaught Place, New Delhi: 28.6315°N, 77.2167°E
"""

import json
import time
import urllib.request
import urllib.parse
import hmac
import hashlib
import datetime
import os
from typing import Any

# ── Configuration ──────────────────────────────────────────────────────────────
OPENSEARCH_ENDPOINT = os.environ.get(
    "OPENSEARCH_ENDPOINT",
    "https://search-jal-drishti-search-XXXX.ap-southeast-2.es.amazonaws.com"
)
INDEX_NAME = "urban_water_kiosks"
REGION = "ap-southeast-2"

# ── Index Mapping ───────────────────────────────────────────────────────────────
INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "kiosk_id":        {"type": "keyword"},
            "name":            {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "type":            {"type": "keyword"},  # RO_COOLER | MUNICIPAL_TAP | TEMPLE_PIAU | PETROL_PUMP
            "location":        {"type": "geo_point"},
            "address":         {"type": "text"},
            "operational":     {"type": "boolean"},
            "verified_at":     {"type": "date"},
            "citizen_confirms":{"type": "integer"},
            "water_quality":   {"type": "keyword"},  # POTABLE | FILTERED | UNTESTED
            "shade_available": {"type": "boolean"},
            "open_hours":      {"type": "keyword"},
            "last_updated":    {"type": "date"}
        }
    }
}

# ── Seed Data: Verified Urban Water Locations near CP, New Delhi ────────────────
SEED_KIOSKS = [
    {
        "kiosk_id": "KSK-001",
        "name": "Hanuman Mandir Piau — Connaught Place",
        "type": "TEMPLE_PIAU",
        "location": {"lat": 28.6329, "lon": 77.2195},
        "address": "Baba Kharak Singh Marg, Connaught Place, New Delhi",
        "operational": True,
        "verified_at": "2025-06-01T08:00:00Z",
        "citizen_confirms": 47,
        "water_quality": "POTABLE",
        "shade_available": True,
        "open_hours": "05:00-22:00",
        "last_updated": "2025-06-01T08:00:00Z"
    },
    {
        "kiosk_id": "KSK-002",
        "name": "IOCL Petrol Pump RO Cooler — Janpath",
        "type": "PETROL_PUMP",
        "location": {"lat": 28.6268, "lon": 77.2197},
        "address": "Janpath Road, Near Janpath Hotel, New Delhi",
        "operational": True,
        "verified_at": "2025-05-28T10:30:00Z",
        "citizen_confirms": 31,
        "water_quality": "FILTERED",
        "shade_available": False,
        "open_hours": "06:00-23:00",
        "last_updated": "2025-05-28T10:30:00Z"
    },
    {
        "kiosk_id": "KSK-003",
        "name": "NDMC Municipal Tap — Minto Road",
        "type": "MUNICIPAL_TAP",
        "location": {"lat": 28.6352, "lon": 77.2312},
        "address": "Minto Road, Near Minto Bridge, New Delhi",
        "operational": True,
        "verified_at": "2025-06-03T07:15:00Z",
        "citizen_confirms": 19,
        "water_quality": "POTABLE",
        "shade_available": False,
        "open_hours": "00:00-23:59",
        "last_updated": "2025-06-03T07:15:00Z"
    },
    {
        "kiosk_id": "KSK-004",
        "name": "Gurudwara Bangla Sahib Langar Water Point",
        "type": "TEMPLE_PIAU",
        "location": {"lat": 28.6258, "lon": 77.2090},
        "address": "Ashoka Road, Connaught Place, New Delhi",
        "operational": True,
        "verified_at": "2025-06-05T09:00:00Z",
        "citizen_confirms": 112,
        "water_quality": "POTABLE",
        "shade_available": True,
        "open_hours": "00:00-23:59",
        "last_updated": "2025-06-05T09:00:00Z"
    },
    {
        "kiosk_id": "KSK-005",
        "name": "HP Petrol Pump RO Cooler — Barakhamba Road",
        "type": "PETROL_PUMP",
        "location": {"lat": 28.6315, "lon": 77.2250},
        "address": "Barakhamba Road, Connaught Place, New Delhi",
        "operational": True,
        "verified_at": "2025-05-30T11:00:00Z",
        "citizen_confirms": 28,
        "water_quality": "FILTERED",
        "shade_available": False,
        "open_hours": "06:00-22:00",
        "last_updated": "2025-05-30T11:00:00Z"
    },
    {
        "kiosk_id": "KSK-006",
        "name": "Palika Bazaar Underground Market Cooler",
        "type": "MUNICIPAL_TAP",
        "location": {"lat": 28.6315, "lon": 77.2167},
        "address": "Palika Bazaar, Connaught Place, New Delhi",
        "operational": True,
        "verified_at": "2025-06-02T14:00:00Z",
        "citizen_confirms": 55,
        "water_quality": "FILTERED",
        "shade_available": True,
        "open_hours": "10:00-21:00",
        "last_updated": "2025-06-02T14:00:00Z"
    }
]


def make_request(method: str, path: str, body: dict | None = None) -> dict:
    """Simple HTTPS request to OpenSearch (uses IAM SigV4 in production via boto3)."""
    url = f"{OPENSEARCH_ENDPOINT}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  HTTP {e.code}: {error_body}")
        return {"error": error_body, "status": e.code}


def create_index() -> None:
    print(f"\n[1/3] Creating index '{INDEX_NAME}'...")
    # Delete if exists (idempotent re-run)
    result = make_request("DELETE", f"/{INDEX_NAME}")
    print(f"  Delete existing: {result.get('acknowledged', result.get('error', 'not found'))}")
    time.sleep(1)

    result = make_request("PUT", f"/{INDEX_NAME}", INDEX_MAPPING)
    if result.get("acknowledged"):
        print(f"  Index created successfully with geo_point mapping.")
    else:
        print(f"  Warning: {result}")


def seed_documents() -> None:
    print(f"\n[2/3] Seeding {len(SEED_KIOSKS)} water kiosk documents...")
    for kiosk in SEED_KIOSKS:
        doc_id = kiosk["kiosk_id"]
        result = make_request("PUT", f"/{INDEX_NAME}/_doc/{doc_id}", kiosk)
        status = result.get("result", result.get("error", "unknown"))
        print(f"  {doc_id} — {kiosk['name'][:45]:<45} → {status}")
        time.sleep(0.2)  # Avoid throttling


def verify_index() -> None:
    print(f"\n[3/3] Verifying index...")
    time.sleep(2)  # Allow indexing to complete
    result = make_request("GET", f"/{INDEX_NAME}/_count")
    count = result.get("count", "unknown")
    print(f"  Document count: {count}")

    # Test geo_distance query
    test_query = {
        "query": {
            "bool": {
                "filter": {
                    "geo_distance": {
                        "distance": "800m",
                        "location": {"lat": 28.6315, "lon": 77.2167}
                    }
                }
            }
        }
    }
    result = make_request("POST", f"/{INDEX_NAME}/_search", test_query)
    hits = result.get("hits", {}).get("total", {}).get("value", 0)
    print(f"  Geo-distance test (800m from CP): {hits} kiosks found")
    print("\n  Sample kiosk names:")
    for hit in result.get("hits", {}).get("hits", [])[:3]:
        src = hit.get("_source", {})
        print(f"    • {src.get('name')} [{src.get('type')}]")


if __name__ == "__main__":
    print("=" * 60)
    print("  Jal-Drishti — OpenSearch Seeder")
    print(f"  Endpoint: {OPENSEARCH_ENDPOINT}")
    print("=" * 60)
    create_index()
    seed_documents()
    verify_index()
    print("\n✓ Seeding complete.")
