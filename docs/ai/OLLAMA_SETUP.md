# Ollama Setup for AI Email Generation

This guide will help you set up Ollama with the llama3.2:1b model for AI-powered email generation and revision features in your DripEmails application.

## Overview

The application uses **Ollama** with the **llama3.2:1b** model (8 billion parameter model), which provides:

- High-quality professional email content generation
- Email revision for grammar, clarity, and tone improvements
- Personalized email campaign creation
- **Complete privacy** - runs entirely on your local machine
- **No API keys required** - no external service dependencies
- **CPU-only operation** - no GPU required

## Prerequisites

- 8GB RAM minimum (16GB recommended)
- 8GB free disk space for the model
- 4+ CPU cores recommended
- Internet connection for initial model download
- Windows, macOS, or Linux operating system

## Step 1: Install Ollama

### Windows

1. **Download Ollama**

   - Visit [https://ollama.ai](https://ollama.ai)
   - Click "Download for Windows"
   - Run the installer (OllamaSetup.exe)

2. **Verify Installation**
   - Open PowerShell
   - Run: `ollama --version`
   - You should see the Ollama version number

### macOS

1. **Download Ollama**

   - Visit [https://ollama.ai](https://ollama.ai)
   - Click "Download for Mac"
   - Open the downloaded .dmg file
   - Drag Ollama to Applications

2. **Verify Installation**
   - Open Terminal
   - Run: `ollama --version`
   - You should see the Ollama version number

### Linux

1. **Install via Script**

   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Verify Installation**
   ```bash
   ollama --version
   ```

## Step 2: Download the llama3.2:1b Model

1. **Pull the Model**

   Open your terminal/PowerShell and run:

   ```bash
   ollama pull llama3.2:1b
   ```

2. **Wait for Download**

   - The model is approximately 4.7GB
   - Download time depends on your internet speed
   - You only need to do this once

3. **Verify Model Installation**
   ```bash
   ollama list
   ```
   You should see `llama3.2:1b` in the list

## Step 3: Start Ollama with CPU-Only Mode

**IMPORTANT:** To ensure Ollama runs on CPU only (avoiding GPU driver requirements), you must set the `OLLAMA_NUM_GPU=0` environment variable.

### Windows PowerShell

**Temporary (current session only):**

```powershell
$env:OLLAMA_NUM_GPU=0
ollama serve
```

**Create a startup script** (recommended):

1. Create a file named `start-ollama-cpu.bat`:

   ```batch
   @echo off
   set OLLAMA_NUM_GPU=0
   ollama serve
   pause
   ```

2. Run this batch file to start Ollama

### macOS/Linux

**Temporary (current session only):**

```bash
export OLLAMA_NUM_GPU=0
ollama serve
```

**Permanent (add to shell profile):**

Add to `~/.bashrc`, `~/.zshrc`, or equivalent:

```bash
export OLLAMA_NUM_GPU=0
```

Then run:

```bash
source ~/.bashrc  # or ~/.zshrc
ollama serve
```

**Create a startup script** (recommended):

1. Create `start-ollama-cpu.sh`:

   ```bash
   #!/bin/bash
   export OLLAMA_NUM_GPU=0
   ollama serve
   ```

2. Make it executable:

   ```bash
   chmod +x start-ollama-cpu.sh
   ```

3. Run it:
   ```bash
   ./start-ollama-cpu.sh
   ```

## Step 4: Test the Setup

1. **Keep Ollama Running**

   - Leave the `ollama serve` command running in a terminal/PowerShell window
   - You should see output like: "Ollama is running"

2. **Test in Another Terminal/PowerShell Window**

   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.2:1b",
     "prompt": "Write a professional welcome email",
     "stream": false
   }'
   ```

3. **Expected Response**
   - You should receive a JSON response with generated text
   - Response time: 10-30 seconds on CPU (this is normal)
   - If you get a connection error, ensure `ollama serve` is running

## Step 5: Configure DripEmails (Optional)

If you're running Ollama on a different host or port, create a `.env` file in your project root:

```env
# Ollama Configuration (defaults shown)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

**Note:** These are the default values. You only need to set them if you're using different settings.

## Performance Expectations

### CPU-Only Mode

- **Generation Time:** 10-30 seconds per email (normal for CPU)
- **Quality:** Excellent - llama3.2:1b provides high-quality output
- **Memory Usage:** ~5GB RAM during inference
- **CPU Usage:** High during generation, minimal when idle

### Tips for Best Performance

1. **Close unnecessary applications** to free up CPU and RAM
2. **Be patient** - CPU inference takes time but produces quality results
3. **Keep Ollama running** in the background to avoid startup delays
4. **Use the startup scripts** to ensure correct CPU-only configuration

## Troubleshooting

### Ollama Won't Start

**Issue:** `ollama serve` fails or exits immediately

**Solutions:**

- Check if another instance is already running: `ps aux | grep ollama` (Linux/Mac) or Task Manager (Windows)
- Kill existing instances and try again
- Check port 11434 is not in use: `netstat -an | grep 11434`

### Model Not Found

**Issue:** Error: "model 'llama3.2:1b' not found"

**Solutions:**

- Run: `ollama pull llama3.2:1b`
- Verify with: `ollama list`
- Ensure you have enough disk space (8GB required)

### Connection Refused

**Issue:** "Connection refused" error when DripEmails tries to connect

**Solutions:**

- Ensure `ollama serve` is running
- Check the correct port: http://localhost:11434
- Verify firewall isn't blocking the connection
- Test with curl as shown in Step 4

### Slow Generation (>60 seconds)

**Issue:** AI generation takes more than 60 seconds

**Solutions:**

- **Expected on slower CPUs** - 10-30 seconds is normal, up to 60 is acceptable
- Close other CPU-intensive applications
- Consider upgrading RAM to 16GB+
- Ensure OLLAMA_NUM_GPU=0 is set (GPU initialization can slow things down)

### Out of Memory Errors

**Issue:** Ollama crashes or returns memory errors

**Solutions:**

- Ensure you have at least 8GB RAM
- Close other applications to free memory
- Restart Ollama service
- Consider upgrading to 16GB RAM for better stability

### Wrong GPU Being Used

**Issue:** Ollama tries to use GPU despite CPU-only setting

**Solutions:**

- **Critical:** Ensure `OLLAMA_NUM_GPU=0` is set BEFORE starting ollama
- Restart the terminal/PowerShell and set the variable again
- Use the startup scripts provided in Step 3
- Verify with environment variable check:
  - Windows: `echo $env:OLLAMA_NUM_GPU`
  - Linux/Mac: `echo $OLLAMA_NUM_GPU`

## Security Notes

- **Privacy:** All AI processing happens locally on your machine
- **No API Keys:** No external service accounts required
- **Network:** Ollama only needs internet for initial model download
- **Data:** Your email content never leaves your machine

## Updating Ollama

To update Ollama to the latest version:

### Windows

- Download the latest installer from https://ollama.ai
- Run the installer (it will update automatically)

### macOS

- Download the latest version from https://ollama.ai
- Replace the old application

### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## Alternative Models

While DripEmails is configured for `llama3.2:1b`, you can experiment with other models:

### Smaller (faster, less RAM)

```bash
ollama pull llama3.1:7b   # Similar to 8b but slightly smaller
```

### Larger (better quality, more resources)

```bash
ollama pull llama3.1:13b  # Requires 16GB+ RAM
```

To use a different model, update your `.env` file:

```env
OLLAMA_MODEL=llama3.1:13b
```

**Note:** CPU generation time increases with larger models.

## Getting Help

- **Ollama Documentation:** https://github.com/ollama/ollama/blob/main/README.md
- **DripEmails Issues:** See the project's GitHub repository
- **Model Information:** https://ollama.ai/library/llama3.1

## Summary Checklist

- [ ] Ollama installed and `ollama --version` works
- [ ] Model downloaded with `ollama pull llama3.2:1b`
- [ ] OLLAMA_NUM_GPU=0 environment variable set
- [ ] `ollama serve` running successfully
- [ ] Tested with curl command (Step 4)
- [ ] DripEmails can generate emails (10-30 second response time)

---

**Congratulations!** Your AI email generation features are now fully configured and running locally on your machine with CPU-only operation.
