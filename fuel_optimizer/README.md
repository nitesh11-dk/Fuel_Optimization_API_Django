# 🛣️ Fuel Optimization API

## 🎯 PROJECT OVERVIEW

This project is a robust **Django REST API** built to perform intelligent route optimization and fuel cost minimization. Mimicking enterprise-grade logistics systems, it calculates the most cost-effective fueling strategy for a given journey across the United States.

The API performs the following operations:
* Accepts a `start` and `end` location via HTTP POST.
* Fetches the **real driving route** and road geometry using the OpenRouteService API.
* Calculates optimal fuel stops along the exact path of the route.
* Minimizes total fuel costs by analyzing real fuel price data from a provided CSV dataset.
* Strictly adheres to the following vehicle constraints:
  * **Mileage**: 10 miles per gallon.
  * **Tank Capacity**: 50 gallons.
  * **Maximum Range**: ~500 miles per tank.

---

## ⚙️ TECHNOLOGIES USED

* **Django & Django REST Framework (DRF)**: The core backend framework, providing a structured, scalable, and secure API environment.
* **OpenRouteService API**: An external mapping service used to geocode city names and retrieve real-world driving distances and polyline geometry.
* **Pandas**: Utilized for extremely fast, in-memory processing and filtering of the large fuel station CSV dataset.
* **Haversine Formula**: Pure mathematical implementation used to accurately calculate the great-circle geographic distance between coordinates (route segments and fuel stations).

---

## 📁 PROJECT STRUCTURE

A clean, service-oriented architecture ensures modularity and testability.

```text
fuel_optimizer/
│
├── fuel_optimizer/
│   ├── settings.py           # Core Django settings, installed apps, and environment configurations.
│   └── urls.py               # Main URL routing and endpoint registrations.
│
├── apps/routing/
│   ├── views.py              # API entry point; handles request parsing, service orchestration, and response generation.
│   ├── serializers/          # DRF serializers for validating incoming JSON payloads.
│   │
│   ├── services/
│   │   ├── route_service.py         # Interfaces with OpenRouteService API to fetch directions and geometry.
│   │   ├── fuel_service.py          # Singleton service that loads, cleans, and caches the fuel CSV data.
│   │   ├── optimization_service.py  # The core algorithm handling segment generation and fuel stop selection.
│   │   └── cost_service.py          # Handles the mathematical computation of fuel usage and final billing.
│   │
│   ├── utils/
│   │   └── geo_utils.py             # Pure functions, including the Haversine distance calculation.
│   │
│   └── data/
│       └── fuel_prices.csv          # The raw dataset of US fuel stations and retail prices.
```

---

## 🔌 THIRD-PARTY API

This project integrates with the **OpenRouteService (ORS) API** to construct realistic driving paths. 
* **Efficiency**: Only **ONE** external API call is made per routing request to fetch directions.
* **Payload**: The API returns the comprehensive `total distance` and the `route geometry` (a massive list of geographical coordinates outlining the actual roads).
* **Extraction**: Geometry is extracted directly from the GeoJSON response structure using `features[0].geometry.coordinates`.

---

## 🧠 CORE WORKING LOGIC (STEP-BY-STEP)

The optimization engine follows a strict procedural flow:

1. **User Request**: The client sends a JSON payload with the start and end destinations:
   ```json
   {
       "start": "New York",
       "end": "Los Angeles"
   }
   ```
2. **API Fetch**: The system calls OpenRouteService API and retrieves the cumulative route distance and real road geometry.
3. **Distance Calculation**: The system isolates the `total_distance` of the trip.
4. **Fuel Computation**: Computes raw fuel requirement: `fuel_needed = total_distance / mileage`.
5. **Short-Circuit Check**: 
   * **IF** `total_distance <= max_range` (500 miles), the vehicle does not need to refuel. The API immediately returns empty stops.
6. **Segmentation**: If the route is long, the route geometry is mathematically divided into driving segments (~500 miles).
7. **Station Selection**: For each segment window:
   * The system isolates a subset of the route coordinates.
   * It finds all available fuel stations within a 50-mile radius of that specific segment of the highway.
   * It selects the absolute **cheapest** station available.
   * It verifies the station has not been selected previously to avoid duplicates.
8. **Progression Validation**: The system strictly enforces forward progression, ensuring the vehicle doesn't route backwards for fuel.
9. **Cost Finalization**: Calculates total trip cost based on the weighted averages of the selected stations.
10. **Response**: Returns a structured JSON response to the client.

---

## 📊 CALCULATIONS EXPLAINED

* **Haversine Distance**: Used to calculate the strict point-to-point radius between a route coordinate and a fuel station's longitude/latitude.
* **Fuel Needed**: Evaluated linearly using `total_distance / 10` (since the vehicle gets 10 mpg).
* **Maximum Range**: Evaluated as `10 mpg × 50 gallons = 500 miles` per tank.
* **Expected Stops**: Mathematically estimated using `ceil(total_distance / 500)`.

---

## 🗺️ STEP-BY-STEP FLOW DIAGRAM (TEXT FORMAT)

```text
[User Request]
      ↓
[Route API Call]
      ↓
[Route Geometry + Distance]
      ↓
[Distance Check: <= 500 miles?]
      ├─ YES → Return no stops
      ↓
      NO → Segment Route into 500-mile windows
      ↓
[Find Nearby Fuel Stations (Haversine 50mi)]
      ↓
[Pick Cheapest Station per Segment]
      ↓
[Calculate Total Fuel Cost]
      ↓
[Return JSON Response]
```

---

## 🧪 EXAMPLE WALKTHROUGH

Let's trace a cross-country trip:
```json
{
    "start": "New York",
    "end": "Los Angeles"
}
```
1. **Total Distance**: ORS returns a driving distance of roughly **2,800 miles**.
2. **Fuel Needed**: 2,800 miles / 10 mpg = **~280 gallons** required.
3. **Segments**: The engine determines that `ceil(2800 / 500) = 6` refueling stops are expected.
4. **Selection**: The algorithm walks the geometry, selecting 5 to 6 optimal stops seamlessly distributed across states like Pennsylvania, Iowa, and Utah.
5. **Cost Calculation**: The 280 gallons are billed against the average price of the selected premium stops, generating the total cost.

---

## 📦 API RESPONSE FORMAT

**Success Response (200 OK)**
```json
{
    "route": {
        "start": "New York",
        "end": "Los Angeles"
    },
    "total_distance": 2797.3,
    "fuel_needed": 279.73,
    "total_cost": 889.82,
    "fuel_stops": [
        {
            "sequence": 1,
            "location": "York, PA",
            "price": 3.259,
            "truckstop_name": "RUTTER'S #73",
            "address": "14 West Pennsylvania Ave"
        },
        ...
    ]
}
```

---

## ⚡ PERFORMANCE CONSIDERATIONS

* **Minimal API Overhead**: External requests are expensive. The app only calls the OpenRouteService API exactly once per request.
* **Memory Optimization**: The `fuel_prices.csv` is loaded into memory as a Pandas DataFrame exactly once via a singleton pattern at startup, eliminating disk I/O latency on subsequent requests.
* **Algorithmic Filtering**: Instead of brute-force checking 8,000+ stations against 20,000+ route points, the algorithm uses bounding-box segmentation and geometric downsampling to solve massive routes in < 2 seconds.

---

## 🚫 EDGE CASE HANDLING

* **Short Routes**: Trips under 500 miles bypass the optimization loop entirely and return an empty stop list.
* **Geocoding Failures**: If poor GPS data causes an empty search radius, the system features an absolute fallback algorithm that guarantees a station is found to prevent silent failures.
* **Duplicate Stops**: The algorithm maintains a `used_station_ids` cache during the loop to guarantee the vehicle never stops at the same station twice.

---

## 🚀 FINAL SUMMARY

This backend application successfully mimics real-world enterprise navigation systems. It leverages scalable backend architecture, sophisticated geographical math, and highly optimized data pipelines to deliver accurate, cost-minimized routing.
