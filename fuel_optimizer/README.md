# Fuel Price Optimization System

A professional Django REST API for optimizing fuel costs along routes by finding the cheapest fuel stations.

## 🏗️ Architecture

This project follows clean architecture principles with a clear separation of concerns:

- **Service Layer**: Business logic separated from views
- **Integration Layer**: External API integrations (OpenRouteService)
- **Utility Layer**: Reusable helper functions
- **Serializer Layer**: Data validation and serialization

## 📁 Project Structure

```
fuel_optimizer/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── fuel_optimizer/          # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   └── routing/             # Core routing app
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── serializers/
│       │   └── route_serializer.py
│       ├── services/        # Business logic layer
│       │   ├── route_service.py
│       │   ├── fuel_service.py
│       │   ├── optimization_service.py
│       │   └── cost_service.py
│       ├── integrations/    # External APIs
│       │   └── map_provider.py
│       ├── utils/           # Helper functions
│       │   ├── geo_utils.py
│       │   ├── distance_utils.py
│       │   └── cache_utils.py
│       ├── data/
│       │   └── fuel_prices.csv
│       └── tests/
│           └── test_route_api.py
│
├── core/                    # Shared system logic
│   ├── config.py
│   ├── constants.py
│   ├── exceptions.py
│   └── logging.py
│
└── scripts/                 # Utility scripts
    └── load_fuel_data.py
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9+
- pip

### Installation

1. **Clone the repository**
   ```bash
   cd fuel_optimizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenRouteService API key:
   ```
   OPENROUTESERVICE_API_KEY=your-api-key-here
   ```
   
   Get a free API key from: https://openrouteservice.org/

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Validate fuel data** (optional)
   ```bash
   python scripts/load_fuel_data.py
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000`

## 📡 API Usage

### Route Optimization Endpoint

**Endpoint:** `POST /api/route/`

**Request Body:**
```json
{
  "start": "New York",
  "end": "Los Angeles"
}
```

**Response:**
```json
{
  "total_distance": 2800.5,
  "fuel_stops": [
    {
      "location": "Big Cabin, OK",
      "price": 3.01,
      "truckstop_name": "WOODSHED OF BIG CABIN",
      "address": "I-44, EXIT 283 & US-69"
    }
  ],
  "total_cost": 870.15,
  "fuel_needed": 280.05
}
```

### Example using cURL

```bash
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "New York", "end": "Los Angeles"}'
```

### Example using Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/route/',
    json={'start': 'New York', 'end': 'Los Angeles'}
)

print(response.json())
```

## 🔧 Core Features

### 1. Route Fetching
- Geocodes location names to coordinates
- Fetches optimal route from OpenRouteService API
- Calculates total distance in miles

### 2. Fuel Optimization
- Splits route into 500-mile segments (max range)
- Finds cheapest fuel stations for each segment
- Minimizes total fuel cost

### 3. Cost Calculation
- Formula: `fuel_needed = total_distance / 10` (10 MPG efficiency)
- `total_cost = fuel_needed * average_fuel_price`

### 4. Performance Optimizations
- Fuel data loaded into memory at startup
- In-memory caching for repeated queries
- Single external API call per route request
- Efficient data filtering

## 🧪 Testing

Run the test suite:

```bash
python manage.py test apps.routing.tests
```

## 📊 Technology Stack

- **Backend**: Django 4.2+
- **API Framework**: Django REST Framework
- **Data Processing**: pandas
- **Routing API**: OpenRouteService
- **HTTP Client**: requests
- **Environment Management**: python-dotenv

## 🎯 Key Design Decisions

### Service-Based Architecture
- Business logic isolated in service layer
- Easy to test and maintain
- Clear separation of concerns

### Fuel Data Strategy
- CSV data loaded into memory at startup
- Pre-computed location identifiers for fast lookup
- Sorted by price for efficient optimization

### Optimization Logic
- Route broken into 500-mile segments
- Cheapest stations selected per segment
- Simple but effective cost minimization

## 🔐 Security Notes

- Never commit `.env` file with real API keys
- Use environment variables for sensitive configuration
- API keys should be rotated regularly in production

## 📝 Future Enhancements

- Add Mapbox as alternative routing provider
- Implement geospatial filtering for nearby stations
- Add user authentication
- Implement rate limiting
- Add caching for route results
- Support for multiple vehicles with different MPG
- Real-time fuel price updates

## 📄 License

This project is for assessment purposes.

## 👤 Author

Built for Backend Django Engineer Assessment
