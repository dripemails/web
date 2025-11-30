# Running Llama 3.1:8B with Ollama

This guide will help you set up and run the Llama 3.1:8B model using Ollama in the VS Code terminal for the AI email revision feature.

## Prerequisites

- Windows, macOS, or Linux
- At least 8GB of RAM (16GB+ recommended)
- ~5GB of free disk space for the model

## Installation

### Windows (PowerShell)

1. **Download and Install Ollama**

   ```powershell
   # Download the Ollama installer from https://ollama.ai/download
   # Or use winget:
   winget install Ollama.Ollama
   ```

2. **Verify Installation**
   ```powershell
   ollama --version
   ```

### macOS

1. **Download and Install Ollama**

   ```bash
   # Download from https://ollama.ai/download
   # Or use Homebrew:
   brew install ollama
   ```

2. **Verify Installation**
   ```bash
   ollama --version
   ```

### Linux

1. **Install Ollama**

   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Verify Installation**
   ```bash
   ollama --version
   ```

## Running Llama 3.1:8B

### Step 1: Start Ollama Service

Open a terminal in VS Code and start Ollama:

**Windows (PowerShell):**

```powershell
# Ollama usually starts automatically on Windows
# If not, you can start it manually:
ollama serve
```

**macOS/Linux:**

```bash
# Start Ollama service in the background
ollama serve &
```

### Step 2: Pull the Llama 3.1:8B Model

In a new terminal (or the same one if running in background):

```bash
ollama pull llama3.1:8b
```

This will download the model (~4.7GB). It may take several minutes depending on your internet connection.

### Step 3: Run the Model (CPU Mode Recommended)

For stable performance and to avoid GPU issues, run the model in CPU mode:

**Windows (PowerShell/CMD):**

```powershell
# Set environment variable to disable GPU
set OLLAMA_NO_GPU=1

# Run the model
ollama run llama3.1:8b
```

**macOS/Linux (Bash):**

```bash
# Set environment variable to disable GPU
export OLLAMA_NO_GPU=1

# Run the model
ollama run llama3.1:8b
```

Test the model by typing a message. You should see a response from the model. Press `Ctrl+D` or type `/bye` to exit the interactive mode.

> **Note:** Running in CPU mode (`OLLAMA_NO_GPU=1`) ensures consistent performance and avoids GPU compatibility issues. The model will still run efficiently on most systems.

### Step 4: List Available Models

To see all installed models:

```bash
ollama list
```

You should see `llama3.1:8b` in the list.

## Using with the Django App

Once Ollama is running with the llama3.1:8b model:

1. **Start the Django development server** (in a separate terminal):

   ```powershell
   python manage.py runserver
   ```

2. **The app will automatically connect to Ollama** at `http://localhost:11434` (default)

3. **Use the AI Revise feature** in the A/B Test page (`/campaigns/abtest/`)

## Environment Variables (Optional)

If you need to customize Ollama settings, you can set these environment variables:

**PowerShell:**

```powershell
$env:USE_OLLAMA = "true"
$env:OLLAMA_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3.1:8b"
```

**Bash:**

```bash
export USE_OLLAMA=true
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1:8b
```

> **Note:** These are already set as defaults in `campaigns/apps.py`, so you only need to set them if you want different values.

## Troubleshooting

### Ollama service not running

**Error:** `connection refused` or `Ollama not responding`

**Solution:**

```bash
# Check if Ollama is running
ollama list

# If not, start the service
ollama serve
```

### Model not found

**Error:** `model 'llama3.1:8b' not found`

**Solution:**

```bash
# Pull the model again
ollama pull llama3.1:8b
```

### Port already in use

**Error:** `bind: address already in use`

**Solution:**

```powershell
# Windows: Find and kill the process using port 11434
netstat -ano | findstr :11434
taskkill /PID <PID> /F

# macOS/Linux: Find and kill the process
lsof -ti:11434 | xargs kill -9
```

### Out of memory

**Error:** Model crashes or system becomes slow

**Solution:**

- Close other applications to free up RAM
- Consider using a smaller model like `llama3.1:3b` instead
- Increase system swap/page file

## Quick Reference

| Command                   | Description            |
| ------------------------- | ---------------------- |
| `ollama serve`            | Start Ollama service   |
| `ollama pull llama3.1:8b` | Download the model     |
| `ollama list`             | List installed models  |
| `ollama run llama3.1:8b`  | Start interactive chat |
| `ollama rm llama3.1:8b`   | Remove the model       |
| `ollama --help`           | Show all commands      |

## Model Information

- **Model:** Llama 3.1:8B
- **Size:** ~4.7GB
- **RAM Required:** 8GB minimum (16GB recommended)
- **Context Length:** 8192 tokens
- **Best For:** Email revision, grammar checking, content improvement

## Additional Models (Optional)

If you want to try other models:

```bash
# Smaller, faster model (good for testing)
ollama pull llama3.1:3b

# Larger, more capable model (requires 16GB+ RAM)
ollama pull llama3.1:70b

# Alternative models
ollama pull mistral
ollama pull codellama
```

## Resources

- [Ollama Official Website](https://ollama.ai/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Llama 3.1 Model Card](https://ollama.ai/library/llama3.1)
- [Available Models](https://ollama.ai/library)

## Support

If you encounter issues:

1. Check the [Ollama GitHub Issues](https://github.com/ollama/ollama/issues)
2. Review the Django server logs for error messages
3. Verify Ollama is running: `curl http://localhost:11434`
