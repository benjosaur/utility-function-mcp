---
title: Utility Function Mcp
emoji: 💻
colorFrom: pink
colorTo: red
sdk: gradio
sdk_version: 6.0.1
app_file: app.py
pinned: false
license: mit
tags:
  - building-mcp-track-consumer
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# EV Utility Function MCP Server

An MCP (Model Context Protocol) server that provides utility function calculations for electric vehicles based on user preferences. Contributors: benjosaur, reuzed, MJ141592

Demo:
https://drive.google.com/file/d/1Z-PoQgvLaEBnhMk8nwrKOnRj8sOKz-QH/view?usp=sharing

Ig Social Media Post:
https://www.instagram.com/p/DRsxbbWCl0m/?img_index=6&igsh=MWoxc3ZrOTM2ZWxhbA==

## Features

This MCP server exposes two tools:

### 1. `calculate_utility`

Calculate the utility score for a single car based on a user's trained preferences.

**Parameters:**

- `user_id`: Username whose utility function to use
- `price`: Car price in euros
- `range`: Range in kilometers
- `efficiency`: Efficiency in Wh/km
- `acceleration`: 0-100km/h time in seconds
- `fast_charge`: Fast charging power in kW
- `seat_count`: Number of seats

**Returns:** JSON with utility score and coefficients used

### 2. `find_best_car`

Find the best car from an array based on a user's utility function.

**Parameters:**

- `user_id`: Username whose utility function to use
- `cars`: Array of car objects with the above features

**Returns:** JSON with the best car and all cars ranked by utility

## Setup

### Local Development

1. Install dependencies:

```bash
pip install -e .
```

2. Create a `.env` file with your Upstash Redis credentials:

```bash
UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

3. Run the MCP server:

```bash
python server.py
```

### Using with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ev-utility": {
      "command": "python",
      "args": ["/path/to/utility-mcp-server/server.py"],
      "env": {
        "UPSTASH_REDIS_REST_URL": "https://your-redis-url.upstash.io",
        "UPSTASH_REDIS_REST_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Hugging Face Space

This server is also available as a Hugging Face Space for easy web-based access and demonstration.

## How It Works

1. User preferences (coefficients) are stored in Upstash Redis with key format `params:{user_id}`
2. The server fetches coefficients from Redis when calculating utilities
3. Features are scaled consistently with the training data
4. Utility is calculated as a dot product: `utility = Σ(coefficient_i × scaled_feature_i)`

## Default Coefficients

If a user_id is not found in Redis, default coefficients are used:

- price: -0.5
- range: 0.8
- efficiency: -0.3
- acceleration: -0.5
- fast_charge: 0.6
- seat_count: 0.4
