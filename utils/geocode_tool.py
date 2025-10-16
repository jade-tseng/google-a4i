# -*- coding: utf-8 -*-
"""
Geocoding Tool for Google Maps API
Provides geocoding functionality for converting addresses to coordinates.
"""

import os
import requests
import inspect
from typing import Dict, Any

# Try to import FunctionTool; older builds may not have it
try:
    from google.adk.tools import FunctionTool
    HAVE_FUNCTION_TOOL = True
except Exception:
    HAVE_FUNCTION_TOOL = False


def _geocode_address(address: str, api_key: str = None) -> Dict[str, Any]:
    """
    Look up a street address and return coordinates and location information.
    
    Args:
        address: The street address to geocode
        api_key: Google Maps API key (if not provided, looks for GOOGLE_MAPS_API_KEY env var)
    
    Returns:
        Dictionary containing geocoding results with keys:
        - ok: Boolean indicating success
        - address: Original input address
        - address_normalized: Formatted address from Google
        - lat: Latitude coordinate
        - lon: Longitude coordinate
        - place_id: Google Places ID
        - types: List of location types
        - error: Error message if ok is False
    """
    if not api_key:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        
    if not api_key:
        # Use hardcoded key as fallback (from original code)
        api_key = "AIzaSyAk3h2srJGmWAyCeISHdFE2zP7b2A8WBIk"
    
    if not api_key:
        return {
            "ok": False, 
            "error": "GOOGLE_MAPS_API_KEY env var not set and no API key provided", 
            "address": address
        }

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "ok": False, 
            "error": f"request_failed: {e}", 
            "address": address
        }

    if data.get("status") != "OK" or not data.get("results"):
        return {
            "ok": False, 
            "error": f"geocode_status: {data.get('status')}", 
            "address": address
        }

    result = data["results"][0]
    location = result.get("geometry", {}).get("location", {})
    
    return {
        "ok": True,
        "address": address,
        "address_normalized": result.get("formatted_address"),
        "lat": float(location.get("lat")),
        "lon": float(location.get("lng")),
        "place_id": result.get("place_id"),
        "types": result.get("types", []),
    }


def _reverse_geocode(lat: float, lon: float, api_key: str = None) -> Dict[str, Any]:
    """
    Reverse geocode coordinates to get address information.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        api_key: Google Maps API key
    
    Returns:
        Dictionary containing reverse geocoding results
    """
    if not api_key:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        
    if not api_key:
        # Use hardcoded key as fallback
        api_key = "AIzaSyAk3h2srJGmWAyCeISHdFE2zP7b2A8WBIk"
    
    if not api_key:
        return {
            "ok": False, 
            "error": "GOOGLE_MAPS_API_KEY env var not set and no API key provided", 
            "lat": lat,
            "lon": lon
        }

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{lat},{lon}", "key": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "ok": False, 
            "error": f"request_failed: {e}", 
            "lat": lat,
            "lon": lon
        }

    if data.get("status") != "OK" or not data.get("results"):
        return {
            "ok": False, 
            "error": f"reverse_geocode_status: {data.get('status')}", 
            "lat": lat,
            "lon": lon
        }

    result = data["results"][0]
    
    return {
        "ok": True,
        "lat": lat,
        "lon": lon,
        "address": result.get("formatted_address"),
        "place_id": result.get("place_id"),
        "types": result.get("types", []),
    }


class GeocodeToolLegacy:
    """Legacy geocoding tool class for older ADK versions."""
    
    name = "maps_geocode"
    description = "Convert a street address to latitude/longitude using Google Maps Geocoding API."
    __name__ = "maps_geocode"  # Add __name__ attribute for ADK compatibility

    def __call__(self, *, address: str) -> Dict[str, Any]:
        """Geocode an address to coordinates."""
        return _geocode_address(address)


class ReverseGeocodeToolLegacy:
    """Legacy reverse geocoding tool class for older ADK versions."""
    
    name = "maps_reverse_geocode"
    description = "Convert latitude/longitude coordinates to a street address using Google Maps Geocoding API."
    __name__ = "maps_reverse_geocode"  # Add __name__ attribute for ADK compatibility

    def __call__(self, *, lat: float, lon: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to address."""
        return _reverse_geocode(lat, lon)


# Create tool instances
geocode_tool = GeocodeToolLegacy()
reverse_geocode_tool = ReverseGeocodeToolLegacy()


def get_geocoding_tools() -> list:
    """
    Get a list of geocoding tools compatible with the current ADK version.
    
    Returns:
        List of geocoding tool instances
    """
    tools = []
    
    if HAVE_FUNCTION_TOOL:
        # Use modern FunctionTool if available
        try:
            geocode_function_tool = FunctionTool(
                name="maps_geocode",
                description="Convert a street address to latitude/longitude using Google Maps Geocoding API.",
                function=_geocode_address
            )
            
            reverse_geocode_function_tool = FunctionTool(
                name="maps_reverse_geocode", 
                description="Convert latitude/longitude coordinates to a street address using Google Maps Geocoding API.",
                function=_reverse_geocode
            )
            
            tools.extend([geocode_function_tool, reverse_geocode_function_tool])
        except Exception as e:
            print(f"Warning: Could not create FunctionTool instances: {e}")
            # Fallback to legacy tools
            tools.extend([geocode_tool, reverse_geocode_tool])
    else:
        # Use legacy tool classes
        tools.extend([geocode_tool, reverse_geocode_tool])
    
    return tools


def test_geocoding_tools():
    """Test the geocoding tools with sample data."""
    print("Testing geocoding tools...")
    
    # Test forward geocoding
    test_address = "1600 Amphitheatre Pkwy, Mountain View, CA"
    result = geocode_tool(address=test_address)
    print(f"Forward geocoding test:")
    print(f"  Address: {test_address}")
    print(f"  Result: {result}")
    
    if result.get("ok"):
        # Test reverse geocoding with the coordinates we just got
        lat, lon = result["lat"], result["lon"]
        reverse_result = reverse_geocode_tool(lat=lat, lon=lon)
        print(f"\nReverse geocoding test:")
        print(f"  Coordinates: {lat}, {lon}")
        print(f"  Result: {reverse_result}")
    
    print("\nGeocode tools test complete!")


if __name__ == "__main__":
    test_geocoding_tools()
