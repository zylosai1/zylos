"""
Open-Meteo based weather tool.
Provides:
- geocode_city(city) -> (lat, lon) or None
- get_weather(city) -> text summary
"""

import requests
from typing import Optional

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 6.0

def geocode_city(city: str) -> Optional[tuple]:
    if not city:
        return None
    try:
        resp = requests.get(GEO_URL, params={"name": city, "count":1, "language":"en"}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        results = j.get("results")
        if not results:
            return None
        r0 = results[0]
        return float(r0["latitude"]), float(r0["longitude"])
    except Exception:
        return None

def get_weather(city: str) -> str:
    """
    Returns a short natural-language summary for current_weather.
    """
    coords = geocode_city(city)
    if not coords:
        return f"Sorry, I couldn't find the coordinates for '{city}'."
    lat, lon = coords
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "auto"
        }
        resp = requests.get(WEATHER_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        cw = j.get("current_weather")
        if not cw:
            return "Weather data unavailable right now."
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        wind_dir = cw.get("winddirection")
        # Might include weathercode mapping in future
        return f"Current weather in {city}: {temp}°C, wind {wind} m/s (dir {wind_dir}°)."
    except Exception as e:
        return f"Weather fetch failed: {e}"