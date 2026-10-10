"""
lambda_function.py
Jal-Drishti — Serverless Brain
Runtime: Python 3.12 | AWS Lambda Powertools v3
"""

from __future__ import annotations

import base64
import json
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, InternalServerError
from aws_lambda_powertools.utilities.typing import LambdaContext

# ── Powertools Bootstrap ────────────────────────────────────────────────────────
logger = Logger(service="jal-drishti", level="INFO")
tracer = Tracer(service="jal-drishti")
app = APIGatewayHttpResolver()

# ── AWS Clients ─────────────────────────────────────────────────────────────────
s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))

# ── Environment ─────────────────────────────────────────────────────────────────
S3_BUCKET = os.environ.get("S3_BUCKET", "jal-drishti-vault-prod")
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
OPENSEARCH_INDEX = "urban_water_kiosks"

# ── Flood Status Thresholds (cm) ────────────────────────────────────────────────
THRESHOLD_SAFE = 10.0
THRESHOLD_RISKY = 22.0

# ── Canopy Shaded Route Corridors (static GeoJSON LineStrings near CP, Delhi) ───
CANOPY_ROUTES = [
    {
        "route_id": "CR-001",
        "name": "Lodhi Garden Canopy Corridor",
        "shade_reduction_celsius": 4.2,
        "coordinates": [
            [77.2195, 28.5931], [77.2210, 28.5945],
            [77.2230, 28.5960], [77.2245, 28.5975]
        ]
    },
    {
        "route_id": "CR-002",
        "name": "Rajpath Tree-Lined Avenue",
        "shade_reduction_celsius": 3.8,
        "coordinates": [
            [77.2090, 28.6129], [77.2120, 28.6140],
            [77.2150, 28.6150], [77.2180, 28.6160]
        ]
    }
]


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 1: POST /api/monsoon/report
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/monsoon/report")
@tracer.capture_method
def monsoon_report() -> dict:
    """
    Accepts a street image (base64) + GPS coordinates.
    Stores image to S3, invokes Claude 3.5 Sonnet for flood depth analysis,
    persists telemetry, and returns structured assessment.
    """
    body: dict = app.current_event.json_body
    if not body:
        raise BadRequestError("Request body is required")

    # ── Validate inputs ─────────────────────────────────────────────────────
    image_b64: str = body.get("image_base64", "")
    latitude: float = body.get("latitude")
    longitude: float = body.get("longitude")

    if not image_b64:
        raise BadRequestError("image_base64 is required")
    if latitude is None or longitude is None:
        raise BadRequestError("latitude and longitude are required")

    report_id = f"RPT-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info("Monsoon report received", extra={
        "report_id": report_id,
        "latitude": latitude,
        "longitude": longitude,
        "image_size_chars": len(image_b64)
    })

    # ── Step 1: Decode and store image to S3 ───────────────────────────────
    image_bytes = _decode_and_store_image(image_b64, report_id)

    # ── Step 2: Invoke Bedrock VLM for flood depth analysis ────────────────
    vision_result = _invoke_bedrock_vision(image_b64, report_id)

    # ── Step 3: Determine flood pin color ──────────────────────────────────
    depth_cm: float = vision_result.get("depth_cm", 0.0)
    pin_color = _classify_flood_pin(depth_cm)

    # ── Step 4: Persist telemetry to S3 ────────────────────────────────────
    telemetry = {
        "report_id": report_id,
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "vision_analysis": vision_result,
        "pin_color": pin_color,
        "s3_image_key": f"raw-photos/{report_id}.jpg"
    }
    _store_telemetry(telemetry, report_id)

    # ── Step 5: Build bypass detour path ───────────────────────────────────
    bypass_path = _generate_bypass_path(latitude, longitude, depth_cm)

    response = {
        "report_id": report_id,
        "timestamp": timestamp,
        "location": {"latitude": latitude, "longitude": longitude},
        "flood_assessment": vision_result,
        "pin_color": pin_color,
        "bypass_detour": bypass_path,
        "s3_image_url": f"s3://{S3_BUCKET}/raw-photos/{report_id}.jpg",
        "telemetry_url": f"s3://{S3_BUCKET}/telemetry/{report_id}.json"
    }

    logger.info("Monsoon report processed", extra={
        "report_id": report_id,
        "depth_cm": depth_cm,
        "status": vision_result.get("status"),
        "pin_color": pin_color
    })

    return response


@tracer.capture_method
def _decode_and_store_image(image_b64: str, report_id: str) -> bytes:
    """Decode base64 image and upload to S3."""
    # Strip data URI prefix if present (e.g., "data:image/jpeg;base64,...")
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception as e:
        logger.error("Base64 decode failed", extra={"report_id": report_id, "error": str(e)})
        raise BadRequestError("Invalid base64 image data")

    s3_key = f"raw-photos/{report_id}.jpg"
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/jpeg",
            ServerSideEncryption="AES256",
            Metadata={"report_id": report_id}
        )
        logger.info("Image stored to S3", extra={"s3_key": s3_key, "size_bytes": len(image_bytes)})
    except Exception as e:
        logger.error("S3 upload failed", extra={"report_id": report_id, "error": str(e)})
        raise InternalServerError("Failed to store image")

    return image_bytes


@tracer.capture_method
def _invoke_bedrock_vision(image_b64: str, report_id: str) -> dict:
    """
    Invoke Claude 3.5 Sonnet with the flood image.
    Returns strict JSON with depth_cm, status, anchor_used, reasoning.
    """
    # Strip data URI prefix
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    system_prompt = """You are an expert urban flood assessment engineer with deep knowledge of 
Indian city infrastructure. Analyze street flood images using physical anchor points to estimate 
water depth with engineering precision. Always respond with ONLY valid JSON — no markdown, no 
explanation outside the JSON structure."""

    user_prompt = """Analyze this street flood image and estimate water depth using visible urban 
physical anchors. Use these calibrated reference points:
- Sidewalk curb height: ~15 cm
- Motorcycle exhaust pipe height: ~22 cm  
- Car hub cap center: ~30 cm
- Motorcycle footrest: ~18 cm
- Full car tire submersion: ~60 cm
- Doorstep threshold: ~10 cm

Respond with ONLY this exact JSON structure (no other text):
{
  "depth_cm": <float: estimated water depth in centimeters>,
  "status": "<SAFE|RISKY_FOR_BIKES|BLOCKED>",
  "anchor_used": "<brief description of the physical reference point observed>",
  "reasoning": "<2-3 sentence engineering rationale explaining the depth calculation>"
}

Classification rules:
- SAFE: depth_cm < 10
- RISKY_FOR_BIKES: 10 <= depth_cm <= 22  
- BLOCKED: depth_cm > 22"""

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.1,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    }

    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        raw_text = response_body["content"][0]["text"].strip()

        # Parse strict JSON response
        vision_data = json.loads(raw_text)

        # Validate required fields
        required_fields = ["depth_cm", "status", "anchor_used", "reasoning"]
        for field in required_fields:
            if field not in vision_data:
                raise ValueError(f"Missing field: {field}")

        # Enforce valid status values
        valid_statuses = {"SAFE", "RISKY_FOR_BIKES", "BLOCKED"}
        if vision_data["status"] not in valid_statuses:
            vision_data["status"] = _classify_status(float(vision_data["depth_cm"]))

        vision_data["depth_cm"] = float(vision_data["depth_cm"])
        logger.info("Bedrock vision analysis complete", extra={
            "report_id": report_id,
            "depth_cm": vision_data["depth_cm"],
            "status": vision_data["status"]
        })
        return vision_data

    except json.JSONDecodeError as e:
        logger.warning("Bedrock JSON parse failed, using fallback", extra={"error": str(e)})
        return {
            "depth_cm": 0.0,
            "status": "SAFE",
            "anchor_used": "Analysis unavailable",
            "reasoning": "Could not parse model response. Manual assessment recommended."
        }
    except Exception as e:
        logger.error("Bedrock invocation failed", extra={"report_id": report_id, "error": str(e)})
        raise InternalServerError("Vision analysis service unavailable")


@tracer.capture_method
def _store_telemetry(telemetry: dict, report_id: str) -> None:
    """Persist telemetry JSON to S3."""
    s3_key = f"telemetry/{report_id}.json"
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(telemetry, indent=2).encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256"
        )
        logger.info("Telemetry stored", extra={"s3_key": s3_key})
    except Exception as e:
        logger.warning("Telemetry storage failed (non-fatal)", extra={"error": str(e)})


def _classify_flood_pin(depth_cm: float) -> str:
    if depth_cm < THRESHOLD_SAFE:
        return "GREEN"
    elif depth_cm <= THRESHOLD_RISKY:
        return "AMBER"
    return "RED"


def _classify_status(depth_cm: float) -> str:
    if depth_cm < THRESHOLD_SAFE:
        return "SAFE"
    elif depth_cm <= THRESHOLD_RISKY:
        return "RISKY_FOR_BIKES"
    return "BLOCKED"


def _generate_bypass_path(lat: float, lon: float, depth_cm: float) -> dict:
    """
    Generate a simple bypass detour path around a flooded point.
    Offsets the route by ~200m north and east to avoid the flood zone.
    """
    if depth_cm < THRESHOLD_SAFE:
        return {"required": False, "path": []}

    offset_deg = 0.002  # ~200m
    bypass_coords = [
        [lon, lat],
        [lon + offset_deg, lat],
        [lon + offset_deg, lat + offset_deg],
        [lon, lat + offset_deg],
        [lon, lat]
    ]
    return {
        "required": True,
        "detour_distance_m": 800,
        "path": bypass_coords,
        "reason": f"Flood depth {depth_cm:.1f}cm — bypass recommended"
    }


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 2: GET /api/summer/coolers
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/summer/coolers")
@tracer.capture_method
def summer_coolers() -> dict:
    """
    Returns verified drinking water kiosks within radius of user's GPS pin.
    Falls back to Haversine calculation if OpenSearch is unavailable.
    """
    params = app.current_event.query_string_parameters or {}

    try:
        lat = float(params.get("lat", 28.6315))
        lon = float(params.get("lon", 77.2167))
        radius = int(params.get("radius", 800))
    except (ValueError, TypeError) as e:
        raise BadRequestError(f"Invalid query parameters: {e}")

    radius = min(max(radius, 100), 5000)  # Clamp: 100m – 5km

    logger.info("Summer cooler query", extra={
        "latitude": lat, "longitude": lon, "radius_m": radius
    })

    # ── Query OpenSearch ────────────────────────────────────────────────────
    kiosks = _query_opensearch_kiosks(lat, lon, radius)

    # ── Surface temperature estimate (simulated from time-of-day) ──────────
    surface_temp = _estimate_surface_temperature()

    # ── Canopy routes within radius ─────────────────────────────────────────
    nearby_canopy = _get_nearby_canopy_routes(lat, lon, radius)

    response = {
        "query_location": {"latitude": lat, "longitude": lon},
        "radius_m": radius,
        "surface_temperature": surface_temp,
        "kiosks_found": len(kiosks),
        "kiosks": kiosks,
        "canopy_routes": nearby_canopy,
        "heat_advisory": _heat_advisory(surface_temp["asphalt_celsius"])
    }

    logger.info("Summer cooler response", extra={
        "kiosks_found": len(kiosks),
        "surface_temp_c": surface_temp["asphalt_celsius"]
    })

    return response


@tracer.capture_method
def _query_opensearch_kiosks(lat: float, lon: float, radius_m: int) -> list[dict]:
    """Query OpenSearch geo_distance filter, fallback to Haversine on error."""
    if not OPENSEARCH_ENDPOINT:
        logger.warning("OpenSearch endpoint not configured, using Haversine fallback")
        return _haversine_fallback(lat, lon, radius_m)

    import urllib.request as urlreq

    query = {
        "size": 20,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"operational": True}},
                    {
                        "geo_distance": {
                            "distance": f"{radius_m}m",
                            "location": {"lat": lat, "lon": lon}
                        }
                    }
                ]
            }
        },
        "sort": [
            {
                "_geo_distance": {
                    "location": {"lat": lat, "lon": lon},
                    "order": "asc",
                    "unit": "m"
                }
            }
        ]
    }

    url = f"{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_search"
    data = json.dumps(query).encode("utf-8")
    req = urlreq.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlreq.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            hits = result.get("hits", {}).get("hits", [])
            kiosks = []
            for hit in hits:
                src = hit["_source"]
                distance_m = hit.get("sort", [None])[0]
                src["distance_m"] = round(distance_m, 1) if distance_m else None
                kiosks.append(src)
            return kiosks
    except Exception as e:
        logger.warning("OpenSearch query failed, using Haversine fallback", extra={"error": str(e)})
        return _haversine_fallback(lat, lon, radius_m)


def _haversine_fallback(lat: float, lon: float, radius_m: int) -> list[dict]:
    """
    Haversine distance calculation against in-memory seed data.
    Used when OpenSearch is unavailable.
    """
    SEED_KIOSKS_FALLBACK = [
        {"kiosk_id": "KSK-001", "name": "Hanuman Mandir Piau — Connaught Place",
         "type": "TEMPLE_PIAU", "location": {"lat": 28.6329, "lon": 77.2195},
         "operational": True, "water_quality": "POTABLE", "shade_available": True,
         "open_hours": "05:00-22:00", "citizen_confirms": 47},
        {"kiosk_id": "KSK-002", "name": "IOCL Petrol Pump RO Cooler — Janpath",
         "type": "PETROL_PUMP", "location": {"lat": 28.6268, "lon": 77.2197},
         "operational": True, "water_quality": "FILTERED", "shade_available": False,
         "open_hours": "06:00-23:00", "citizen_confirms": 31},
        {"kiosk_id": "KSK-003", "name": "NDMC Municipal Tap — Minto Road",
         "type": "MUNICIPAL_TAP", "location": {"lat": 28.6352, "lon": 77.2312},
         "operational": True, "water_quality": "POTABLE", "shade_available": False,
         "open_hours": "00:00-23:59", "citizen_confirms": 19},
        {"kiosk_id": "KSK-004", "name": "Gurudwara Bangla Sahib Langar Water Point",
         "type": "TEMPLE_PIAU", "location": {"lat": 28.6258, "lon": 77.2090},
         "operational": True, "water_quality": "POTABLE", "shade_available": True,
         "open_hours": "00:00-23:59", "citizen_confirms": 112},
        {"kiosk_id": "KSK-005", "name": "HP Petrol Pump RO Cooler — Barakhamba Road",
         "type": "PETROL_PUMP", "location": {"lat": 28.6315, "lon": 77.2250},
         "operational": True, "water_quality": "FILTERED", "shade_available": False,
         "open_hours": "06:00-22:00", "citizen_confirms": 28},
        {"kiosk_id": "KSK-006", "name": "Palika Bazaar Underground Market Cooler",
         "type": "MUNICIPAL_TAP", "location": {"lat": 28.6315, "lon": 77.2167},
         "operational": True, "water_quality": "FILTERED", "shade_available": True,
         "open_hours": "10:00-21:00", "citizen_confirms": 55},
    ]

    R = 6371000  # Earth radius in meters
    results = []
    for kiosk in SEED_KIOSKS_FALLBACK:
        klat = kiosk["location"]["lat"]
        klon = kiosk["location"]["lon"]
        dlat = math.radians(klat - lat)
        dlon = math.radians(klon - lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat)) * math.cos(math.radians(klat)) *
             math.sin(dlon / 2) ** 2)
        dist_m = 2 * R * math.asin(math.sqrt(a))
        if dist_m <= radius_m:
            kiosk["distance_m"] = round(dist_m, 1)
            results.append(kiosk)

    results.sort(key=lambda x: x["distance_m"])
    return results


def _estimate_surface_temperature() -> dict:
    """
    Estimate surface temperature based on UTC hour (simulates Delhi summer conditions).
    Asphalt can reach 55-65°C at peak afternoon.
    """
    hour_utc = datetime.now(timezone.utc).hour
    hour_ist = (hour_utc + 5) % 24 + (1 if (hour_utc + 30) % 60 >= 30 else 0)

    # Sinusoidal model: peak at 14:00 IST
    base_air = 38.0
    peak_asphalt = 58.0
    angle = math.pi * (hour_ist - 6) / 12 if 6 <= hour_ist <= 18 else 0
    air_temp = base_air + 6 * math.sin(angle)
    asphalt_temp = peak_asphalt * math.sin(angle) if angle > 0 else 28.0
    asphalt_temp = max(28.0, min(asphalt_temp, 62.0))

    return {
        "air_celsius": round(air_temp, 1),
        "asphalt_celsius": round(asphalt_temp, 1),
        "feels_like_celsius": round(air_temp + 4.5, 1),
        "uv_index": round(8 * math.sin(angle), 1) if angle > 0 else 0.0,
        "measurement_time_ist": f"{hour_ist:02d}:00 IST"
    }


def _get_nearby_canopy_routes(lat: float, lon: float, radius_m: int) -> list[dict]:
    """Return canopy routes whose start point is within radius."""
    R = 6371000
    nearby = []
    for route in CANOPY_ROUTES:
        start = route["coordinates"][0]
        rlon, rlat = start[0], start[1]
        dlat = math.radians(rlat - lat)
        dlon = math.radians(rlon - lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat)) * math.cos(math.radians(rlat)) *
             math.sin(dlon / 2) ** 2)
        dist_m = 2 * R * math.asin(math.sqrt(a))
        if dist_m <= radius_m * 3:  # Wider search for canopy routes
            route_copy = dict(route)
            route_copy["distance_to_start_m"] = round(dist_m, 1)
            nearby.append(route_copy)
    return nearby


def _heat_advisory(asphalt_temp: float) -> dict:
    if asphalt_temp >= 55:
        return {"level": "EXTREME", "color": "RED",
                "message": "Extreme heat. Seek shade immediately. Hydrate every 15 minutes."}
    elif asphalt_temp >= 45:
        return {"level": "HIGH", "color": "ORANGE",
                "message": "High heat stress. Use shaded canopy routes. Carry water."}
    elif asphalt_temp >= 35:
        return {"level": "MODERATE", "color": "AMBER",
                "message": "Moderate heat. Stay hydrated. Prefer morning/evening travel."}
    return {"level": "LOW", "color": "GREEN", "message": "Comfortable conditions."}


# ══════════════════════════════════════════════════════════════════════════════
# Lambda Handler Entry Point
# ══════════════════════════════════════════════════════════════════════════════

@logger.inject_lambda_context(correlation_id_path="requestContext.requestId")
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
