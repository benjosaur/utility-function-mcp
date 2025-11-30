#!/usr/bin/env python3
"""
MCP Server for EV Utility Function Calculations

This server provides tools to calculate utility scores for electric vehicles
using personalized coefficients stored in Upstash Redis.
"""

import json
import os
from typing import Any
from dotenv import load_dotenv
from upstash_redis import Redis

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv()

# Initialize Redis client
redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

# Feature keys in order (must match the order in the coefficient array)
FEATURE_KEYS = ["price", "range", "efficiency", "acceleration", "fast_charge", "seat_count"]

# Default coefficients if user not found
DEFAULT_COEFFS = {
    "price": -0.5,
    "range": 0.8,
    "efficiency": -0.3,
    "acceleration": -0.5,
    "fast_charge": 0.6,
    "seat_count": 0.4,
}


def get_user_coefficients(user_id: str) -> dict[str, float]:
    """
    Fetch user coefficients from Redis. Returns default if not found.
    """
    redis_key = f"params:{user_id}"
    data_str = redis.get(redis_key)

    if data_str is None:
        return DEFAULT_COEFFS

    # Parse the JSON data - handle both string and bytes
    if isinstance(data_str, bytes):
        data_str = data_str.decode('utf-8')

    data = json.loads(data_str) if isinstance(data_str, str) else data_str
    return data.get("coeffs", DEFAULT_COEFFS)


def scale_features(car_features: dict[str, float]) -> list[float]:
    """
    Scale car features to match the training data scaling.
    """
    def get_val(key: str) -> float:
        val = car_features.get(key)
        if val is None:
            return 0.0
        return float(val)

    # ORDER MATTERS: Must match FEATURE_KEYS
    scaled = [
        get_val("price") / 1000,
        get_val("range") / 100,
        get_val("efficiency") / 10,
        get_val("acceleration"),
        get_val("fast_charge") / 100,
        get_val("seat_count"),
    ]
    return scaled


def calculate_utility_score(car_features: dict[str, float], coeffs: dict[str, float]) -> float:
    """
    Calculate utility score using dot product of features and coefficients.
    """
    scaled_features = scale_features(car_features)
    coeff_array = [coeffs[key] for key in FEATURE_KEYS]

    # Dot product
    utility = sum(f * c for f, c in zip(scaled_features, coeff_array))
    return utility


# Create the MCP server
server = Server("utility-function")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
    """
    return [
        Tool(
            name="calculate_utility",
            description="Calculate the utility score for a car based on a user's preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The username/ID whose utility function to use"
                    },
                    "price": {
                        "type": "number",
                        "description": "Car price in euros"
                    },
                    "range": {
                        "type": "number",
                        "description": "Range in kilometers"
                    },
                    "efficiency": {
                        "type": "number",
                        "description": "Efficiency in Wh/km"
                    },
                    "acceleration": {
                        "type": "number",
                        "description": "0-100km/h time in seconds"
                    },
                    "fast_charge": {
                        "type": "number",
                        "description": "Fast charging power in kW"
                    },
                    "seat_count": {
                        "type": "number",
                        "description": "Number of seats"
                    }
                },
                "required": ["user_id", "price", "range", "efficiency", "acceleration", "fast_charge", "seat_count"]
            }
        ),
        Tool(
            name="find_best_car",
            description="Find the best car from an array based on a user's utility function",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The username/ID whose utility function to use"
                    },
                    "cars": {
                        "type": "array",
                        "description": "Array of car objects with features",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"},
                                "range": {"type": "number"},
                                "efficiency": {"type": "number"},
                                "acceleration": {"type": "number"},
                                "fast_charge": {"type": "number"},
                                "seat_count": {"type": "number"}
                            },
                            "required": ["price", "range", "efficiency", "acceleration", "fast_charge", "seat_count"]
                        }
                    }
                },
                "required": ["user_id", "cars"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool execution requests.
    """
    if name == "calculate_utility":
        user_id = arguments["user_id"]

        # Get user coefficients
        coeffs = get_user_coefficients(user_id)

        # Extract car features
        car_features = {
            "price": arguments["price"],
            "range": arguments["range"],
            "efficiency": arguments["efficiency"],
            "acceleration": arguments["acceleration"],
            "fast_charge": arguments["fast_charge"],
            "seat_count": arguments["seat_count"]
        }

        # Calculate utility
        utility = calculate_utility_score(car_features, coeffs)

        result = {
            "user_id": user_id,
            "utility": utility,
            "coefficients_used": coeffs,
            "car_features": car_features
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "find_best_car":
        user_id = arguments["user_id"]
        cars = arguments["cars"]

        # Get user coefficients
        coeffs = get_user_coefficients(user_id)

        # Calculate utility for each car
        best_car = None
        best_utility = float('-inf')
        all_results = []

        for car in cars:
            utility = calculate_utility_score(car, coeffs)
            car_result = {**car, "utility": utility}
            all_results.append(car_result)

            if utility > best_utility:
                best_utility = utility
                best_car = car_result

        result = {
            "user_id": user_id,
            "best_car": best_car,
            "all_cars_with_utilities": all_results,
            "coefficients_used": coeffs
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """
    Main entry point for the MCP server.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="utility-function",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
