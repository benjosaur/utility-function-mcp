#!/usr/bin/env python3
"""
Simple test script to verify the utility calculation functions work correctly.
This doesn't test the MCP protocol itself, just the core logic.
"""

import json
from server import get_user_coefficients, calculate_utility_score

def test_calculate_utility():
    """Test basic utility calculation."""
    print("Testing utility calculation...")

    # Test with default coefficients
    user_id = "test_user_nonexistent"
    coeffs = get_user_coefficients(user_id)
    print(f"\nCoefficients for {user_id}:")
    print(json.dumps(coeffs, indent=2))

    # Example car features
    car = {
        "price": 45000,
        "range": 500,
        "efficiency": 150,
        "acceleration": 6.1,
        "fast_charge": 170,
        "seat_count": 5
    }

    utility = calculate_utility_score(car, coeffs)
    print(f"\nCar features:")
    print(json.dumps(car, indent=2))
    print(f"\nCalculated utility: {utility:.4f}")


def test_with_saved_user():
    """Test with a user that has saved preferences."""
    print("\n" + "="*60)
    print("Testing with saved user preferences...")

    user_id = "benjo"  # Should exist in Redis from the screenshot
    coeffs = get_user_coefficients(user_id)
    print(f"\nCoefficients for {user_id}:")
    print(json.dumps({k: round(v, 4) for k, v in coeffs.items()}, indent=2))

    # Example cars
    cars = [
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
    ]

    print(f"\nComparing {len(cars)} cars:")
    results = []
    for car in cars:
        utility = calculate_utility_score(car, coeffs)
        results.append((car["name"], utility))
        print(f"  {car['name']}: {utility:.4f}")

    # Find best
    best_car, best_utility = max(results, key=lambda x: x[1])
    print(f"\n🏆 Best car for {user_id}: {best_car} (utility: {best_utility:.4f})")


if __name__ == "__main__":
    try:
        test_calculate_utility()
        test_with_saved_user()
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
