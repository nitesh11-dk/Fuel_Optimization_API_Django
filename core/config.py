import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENROUTESERVICE_API_KEY = os.getenv('OPENROUTESERVICE_API_KEY', '')
MAX_RANGE_MILES = 500
FUEL_EFFICIENCY_MPG = 10
FUEL_DATA_PATH = BASE_DIR / 'apps' / 'routing' / 'data' / 'fuel_prices.csv'
