"""
Gradio App for EV Utility Function Calculator
Deployed on Hugging Face Spaces
"""

import gradio as gr
import json
import os
from upstash_redis import Redis

# Initialize Redis client
redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

# Feature keys in order
FEATURE_KEYS = ["price", "range", "efficiency", "acceleration", "fast_charge", "seat_count"]

# Default coefficients
DEFAULT_COEFFS = {
    "price": -0.5,
    "range": 0.8,
    "efficiency": -0.3,
    "acceleration": -0.5,
    "fast_charge": 0.6,
    "seat_count": 0.4,
}


def get_user_coefficients(user_id: str) -> dict[str, float]:
    """Fetch user coefficients from Redis."""
    redis_key = f"params:{user_id}"
    data_str = redis.get(redis_key)

    if data_str is None:
        return DEFAULT_COEFFS

    if isinstance(data_str, bytes):
        data_str = data_str.decode('utf-8')

    data = json.loads(data_str) if isinstance(data_str, str) else data_str
    return data.get("coeffs", DEFAULT_COEFFS)


def scale_features(car_features: dict[str, float]) -> list[float]:
    """Scale car features."""
    def get_val(key: str) -> float:
        val = car_features.get(key)
        if val is None:
            return 0.0
        return float(val)

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
    """Calculate utility score."""
    scaled_features = scale_features(car_features)
    coeff_array = [coeffs[key] for key in FEATURE_KEYS]
    utility = sum(f * c for f, c in zip(scaled_features, coeff_array))
    return utility


def calculate_single_utility(user_id: str, price: float, range_km: float, efficiency: float,
                            acceleration: float, fast_charge: float, seat_count: int) -> str:
    """Calculate utility for a single car."""
    try:
        coeffs = get_user_coefficients(user_id)

        car_features = {
            "price": price,
            "range": range_km,
            "efficiency": efficiency,
            "acceleration": acceleration,
            "fast_charge": fast_charge,
            "seat_count": seat_count
        }

        utility = calculate_utility_score(car_features, coeffs)

        result = {
            "user_id": user_id,
            "utility_score": round(utility, 4),
            "coefficients_used": {k: round(v, 4) for k, v in coeffs.items()},
            "car_features": car_features,
            "note": "Using default coefficients" if coeffs == DEFAULT_COEFFS else "Using saved user preferences"
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def find_best_from_list(user_id: str, cars_json: str) -> str:
    """Find the best car from a JSON list."""
    try:
        cars = json.loads(cars_json)
        coeffs = get_user_coefficients(user_id)

        best_car = None
        best_utility = float('-inf')
        all_results = []

        for car in cars:
            utility = calculate_utility_score(car, coeffs)
            car_result = {**car, "utility": round(utility, 4)}
            all_results.append(car_result)

            if utility > best_utility:
                best_utility = utility
                best_car = car_result

        # Sort by utility descending
        all_results.sort(key=lambda x: x["utility"], reverse=True)

        result = {
            "user_id": user_id,
            "best_car": best_car,
            "all_cars_ranked": all_results,
            "coefficients_used": {k: round(v, 4) for k, v in coeffs.items()},
            "note": "Using default coefficients" if coeffs == DEFAULT_COEFFS else "Using saved user preferences"
        }

        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# Example cars JSON
example_cars = json.dumps([
    {
        "name": "Tesla Model 3",
        "price": 45000,
        "range": 500,
        "efficiency": 150,
        "acceleration": 6.1,
        "fast_charge": 170,
        "seat_count": 5
    },
    {
        "name": "Volkswagen ID.4",
        "price": 40000,
        "range": 420,
        "efficiency": 180,
        "acceleration": 8.5,
        "fast_charge": 125,
        "seat_count": 5
    },
    {
        "name": "Hyundai Ioniq 5",
        "price": 48000,
        "range": 480,
        "efficiency": 165,
        "acceleration": 7.4,
        "fast_charge": 220,
        "seat_count": 5
    }
], indent=2)


# Create Gradio interface
with gr.Blocks(title="EV Utility Function Calculator") as demo:
    gr.Markdown("""
    # 🚗 EV Utility Function Calculator

    This tool calculates utility scores for electric vehicles based on user preferences.
    User preferences are stored in Upstash Redis with their trained coefficients.
                
    **Train your own function here**
    https://autofinder.onrender.com
                
    Demo:
    https://drive.google.com/file/d/1Z-PoQgvLaEBnhMk8nwrKOnRj8sOKz-QH/view?usp=sharing

    Ig Social Media Post:
    https://www.instagram.com/p/DRsxbbWCl0m/?img_index=6&igsh=MWoxc3ZrOTM2ZWxhbA==

    **Note:** If a user_id is not found, default coefficients will be used.
    """)

    with gr.Tab("Calculate Single Car Utility"):
        gr.Markdown("### Calculate the utility score for a single car")

        with gr.Row():
            with gr.Column():
                user_id_single = gr.Textbox(label="User ID", value="benjo", placeholder="Enter username")
                price = gr.Number(label="Price (€)", value=45000)
                range_km = gr.Number(label="Range (km)", value=500)
                efficiency = gr.Number(label="Efficiency (Wh/km)", value=150)
                acceleration = gr.Number(label="0-100km/h (seconds)", value=6.1)
                fast_charge = gr.Number(label="Fast Charge (kW)", value=170)
                seat_count = gr.Number(label="Seat Count", value=5, precision=0)

            with gr.Column():
                output_single = gr.Code(label="Result", language="json")

        calc_btn = gr.Button("Calculate Utility", variant="primary")
        calc_btn.click(
            calculate_single_utility,
            inputs=[user_id_single, price, range_km, efficiency, acceleration, fast_charge, seat_count],
            outputs=output_single
        )

    with gr.Tab("Find Best Car"):
        gr.Markdown("### Find the best car from a list based on user preferences")

        with gr.Row():
            with gr.Column():
                user_id_best = gr.Textbox(label="User ID", value="benjo", placeholder="Enter username")
                cars_json = gr.Code(
                    label="Cars (JSON Array)",
                    value=example_cars,
                    language="json",
                    lines=20
                )

            with gr.Column():
                output_best = gr.Code(label="Result", language="json", lines=25)

        find_btn = gr.Button("Find Best Car", variant="primary")
        find_btn.click(
            find_best_from_list,
            inputs=[user_id_best, cars_json],
            outputs=output_best
        )

    gr.Markdown("""
    ---
    ## About

    This is the web interface for the EV Utility Function MCP Server.

    ### MCP Server

    This tool is also available as an MCP (Model Context Protocol) server that can be used with Claude Desktop
    and other MCP-compatible clients.

    **Repository:** https://github.com/MJ141592/AutoFinder

    ### How it works:

    1. Users train their preferences through the AutoFinder app
    2. Preferences are saved to Upstash Redis as coefficients
    3. This tool fetches those coefficients and calculates utility scores
    4. Utility = Σ(coefficient × scaled_feature)
    """)

if __name__ == "__main__":
    demo.launch(mcp_server=True)
