# Deployment Guide

## Deploying to Hugging Face Spaces

### Step 1: Create a New Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose:
   - **SDK:** Gradio
   - **Space name:** `ev-utility-function` (or your preferred name)
   - **License:** Choose appropriate license
   - **Visibility:** Public or Private

### Step 2: Push Your Code

Option A: Using Git

```bash
# Clone your space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/ev-utility-function
cd ev-utility-function

# Copy all files from utility-mcp-server directory
cp -r /path/to/utility-mcp-server/* .

# Remove server.py if you only want the Gradio interface
# (Keep it if you want to document the MCP server too)

# Add and commit
git add .
git commit -m "Initial commit: EV Utility Function Calculator"
git push
```

Option B: Using Hugging Face Web Interface

1. Upload the following files through the web interface:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`

### Step 3: Configure Environment Variables

1. Go to your Space settings
2. Click on "Settings" → "Variables and secrets"
3. Add the following secrets:
   - `UPSTASH_REDIS_REST_URL`: Your Upstash Redis URL
   - `UPSTASH_REDIS_REST_TOKEN`: Your Upstash Redis token

### Step 4: Wait for Build

Your Space will automatically build and deploy. You can monitor the build logs in the "Logs" section.

## Using as an MCP Server

### With Claude Desktop

1. Copy `server.py` to your local machine
2. Create a `.env` file with your Upstash credentials
3. Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ev-utility": {
      "command": "python",
      "args": ["/absolute/path/to/utility-mcp-server/server.py"],
      "env": {
        "UPSTASH_REDIS_REST_URL": "https://your-redis-url.upstash.io",
        "UPSTASH_REDIS_REST_TOKEN": "your-token-here"
      }
    }
  }
}
```

4. Restart Claude Desktop

### With Other MCP Clients

The server uses stdio for communication. Any MCP-compatible client can connect to it.

## Testing Locally

### Test the Gradio App

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials

# Run the app
python app.py
```

### Test the MCP Server

```bash
# Run the MCP server
python server.py

# The server will communicate via stdin/stdout
# Use an MCP client to test, or integrate with Claude Desktop
```

## Troubleshooting

### "No module named 'mcp'"

Install the MCP package:
```bash
pip install mcp
```

### "Connection to Redis failed"

1. Check your environment variables are set correctly
2. Verify your Upstash Redis URL and token
3. Ensure your IP is not blocked by Upstash

### Space Build Fails

1. Check the build logs in Hugging Face Spaces
2. Ensure all dependencies are in `requirements.txt`
3. Verify Python version compatibility (use Python 3.10+)

## Updating the Space

To update your deployed Space:

```bash
# Make your changes locally
# Commit and push
git add .
git commit -m "Update: description of changes"
git push
```

The Space will automatically rebuild with your changes.
