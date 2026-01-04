# Ollama Model Selection Guide

Choose the right model based on your server's memory availability.

## 📊 Model Comparison

| Model | RAM Required | Size | Speed | Quality | Use Case |
|-------|--------------|------|-------|---------|----------|
| `llama3.2:1b` | ~1.3 GB | 1.3 GB | Fastest | Good | **Low memory servers (recommended)** |
| `llama3.2:3b` | ~2.0 GB | 2.0 GB | Fast | Better | Medium memory servers |
| `llama3.1:8b` | ~4.8 GB | 4.7 GB | Slower | Best | High memory servers (4GB+ free RAM) |

## 🎯 Quick Selection Guide

### If you have less than 2GB free RAM:
**Use: `llama3.2:1b`** ✅
```bash
ollama pull llama3.2:1b
```

Then set in `.env`:
```bash
OLLAMA_MODEL=llama3.2:1b
```

### If you have 2-4GB free RAM:
**Use: `llama3.2:3b`** ✅
```bash
ollama pull llama3.2:3b
```

Then set in `.env`:
```bash
OLLAMA_MODEL=llama3.2:3b
```

### If you have 4GB+ free RAM:
**Use: `llama3.1:8b`** ✅
```bash
ollama pull llama3.1:8b
```

Then set in `.env`:
```bash
OLLAMA_MODEL=llama3.1:8b
```

## 🔍 Check Your Available Memory

```bash
# Check total memory
free -h

# Check available memory (look for "available" column)
free -m

# Check what's using memory
top
# OR
htop
```

**Important:** You need **more free RAM** than the model size. If you have 1GB free but the model needs 1.3GB, you'll get out-of-memory errors.

## 🚀 Switching Models

### Step 1: Pull the new model

```bash
# For low memory (recommended if you got memory errors)
ollama pull llama3.2:1b

# For medium memory
ollama pull llama3.2:3b

# For high memory
ollama pull llama3.1:8b
```

### Step 2: Update your `.env` file

```bash
# Edit your .env file
nano /path/to/your/.env

# Update OLLAMA_MODEL
OLLAMA_MODEL=llama3.2:1b  # or llama3.2:3b or llama3.1:8b
```

### Step 3: Restart Django

```bash
# Restart your Django application
sudo supervisorctl restart gunicorn
# OR
sudo systemctl restart gunicorn
```

### Step 4: Test

```bash
# Test from Django shell
python manage.py shell
>>> from campaigns.ai_utils import generate_email_content
>>> result = generate_email_content("Test email", context="Testing")
>>> print(result['subject'])
```

## 🔄 Changing from One Model to Another

If you want to switch models:

1. **Pull the new model:**
   ```bash
   ollama pull llama3.2:1b
   ```

2. **Update `.env` file:**
   ```bash
   OLLAMA_MODEL=llama3.2:1b
   ```

3. **Optional: Remove old model to save space:**
   ```bash
   ollama rm llama3.1:8b  # Only if you're not using it anymore
   ```

4. **Restart Django**

## 💡 Tips

- **Start small:** If you're unsure, start with `llama3.2:1b` - it works well for email generation
- **Monitor memory:** Use `htop` or `free -h` to monitor memory usage
- **Quality vs Speed:** Larger models = better quality but slower and need more RAM
- **Test first:** Try generating a few emails to see if the model quality meets your needs

## ❓ Which Model Should I Use?

**For email generation specifically:**
- `llama3.2:1b` is usually sufficient for email content - it's designed for text generation tasks
- `llama3.2:3b` provides better quality if you have the memory
- `llama3.1:8b` is best for complex tasks, but overkill for most email generation needs

**Default recommendation:** `llama3.2:1b` unless you have specific quality requirements and enough memory.

