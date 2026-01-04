# 📚 AI Email Generation Documentation Index

Welcome to the Ollama AI email generation setup documentation for DripEmails.

## 🚀 Start Here

**New to Ollama?** → [Quick Start Guide](quick_start.md)  
**Setting up production?** → [Remote Server Setup](ollama_remote_setup.md)  
**Need examples?** → [Configuration Examples](configuration_examples.md)

---

## 📖 Documentation Files

### 1. [Quick Start Guide](quick_start.md)

⏱️ **5-minute setup**

Perfect for getting started quickly. Covers:

- Local installation (Windows, macOS, Linux)
- Remote server setup basics
- Common configurations
- Quick troubleshooting

**Use this if:** You want to get Ollama running ASAP.

---

### 2. [Remote Server Setup Guide](ollama_remote_setup.md)

📘 **Comprehensive guide**

Complete production deployment documentation. Covers:

- Detailed installation for all platforms
- Network configuration and firewall setup
- Django integration (settings.py and live.py)
- Getting server IP addresses
- Security best practices
- Performance optimization
- In-depth troubleshooting
- Monitoring and logging

**Use this if:** You need detailed production setup or troubleshooting help.

---

### 3. [Configuration Examples](configuration_examples.md)

🎯 **Real-world scenarios**

Practical deployment examples. Covers:

- 5 common deployment scenarios
- Hardware recommendations
- Model performance comparison
- Security checklists
- Test scripts
- Monitoring setup

**Use this if:** You want to see how others have deployed Ollama.

---

### 4. [Setup Summary](SETUP_SUMMARY.md)

📋 **Quick reference**

High-level overview of the complete setup. Covers:

- Quick installation commands
- Configuration file changes
- Key concepts
- Security notes

**Use this if:** You need a quick refresher or overview.

---

## 🎯 Choose Your Path

### Path 1: Local Development

```
1. Read: Quick Start Guide → Local Development Setup
2. Follow: 4 simple commands
3. Test: Django shell test
4. Time: ~5 minutes
```

### Path 2: Remote Server (Production)

```
1. Read: Remote Server Setup Guide → Complete
2. Configure: Server + Django
3. Secure: Firewall + monitoring
4. Test: Connection + generation
5. Time: ~30 minutes
```

### Path 3: Advanced Deployment

```
1. Read: Configuration Examples → Your scenario
2. Review: Remote Server Setup Guide → Security section
3. Implement: Reverse proxy + SSL
4. Monitor: Setup logging
5. Time: ~2 hours
```

---

## 🔧 What Was Changed

### Configuration Files

1. **`dripemails/settings.py`** (Local Development)

   ```python
   OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
   OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.1:8b')
   ```

2. **`dripemails/live.py`** (Production)

   ```python
   OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
   OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
   ```

3. **`campaigns/ai_utils.py`** (AI Module)
   - Now uses Django settings
   - Falls back to environment variables
   - Removed Hugging Face dependency

### Environment Variables

Add to your `.env` file:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # or your server IP
OLLAMA_MODEL=llama3.1:8b
```

---

## ✅ Quick Checklist

Before you start:

- [ ] Choose deployment scenario (local vs remote)
- [ ] Have server access (if using remote)
- [ ] Minimum 8GB RAM available
- [ ] 20GB+ free disk space

Setup steps:

- [ ] Install Ollama on target server
- [ ] Configure for remote access (if needed)
- [ ] Pull llama3.1:8b model
- [ ] Update Django settings
- [ ] Add environment variables
- [ ] Test connection
- [ ] Test email generation

---

## 🆘 Common Issues

### "Connection refused"

→ See [Remote Setup Guide - Troubleshooting](ollama_remote_setup.md#troubleshooting)

### "Model not found"

→ Run: `ollama pull llama3.1:8b`

### Slow responses

→ See [Configuration Examples - Performance](configuration_examples.md#model-performance-comparison)

### Can't connect remotely

→ See [Remote Setup Guide - Firewall Configuration](ollama_remote_setup.md#firewall-configuration)

---

## 📞 Support

1. ✅ Check the [Quick Start FAQ](quick_start.md)
2. ✅ Review [Troubleshooting Guide](ollama_remote_setup.md#troubleshooting)
3. ✅ Test with provided test scripts
4. ✅ Check Ollama logs: `sudo journalctl -u ollama -f`
5. ✅ Verify with curl: `curl http://YOUR_IP:11434/api/tags`

---

## 🔗 External Resources

- **Ollama GitHub:** https://github.com/ollama/ollama
- **API Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Model Library:** https://ollama.com/library
- **Discord Community:** https://discord.gg/ollama

---

## 📊 At a Glance

| Topic             | File                                                   | Time   |
| ----------------- | ------------------------------------------------------ | ------ |
| Quick local setup | [quick_start.md](quick_start.md)                       | 5 min  |
| Complete guide    | [ollama_remote_setup.md](ollama_remote_setup.md)       | 30 min |
| Real examples     | [configuration_examples.md](configuration_examples.md) | 15 min |
| Overview          | [SETUP_SUMMARY.md](SETUP_SUMMARY.md)                   | 2 min  |

---

**Last Updated:** January 4, 2026  
**Documentation Version:** 1.0  
**Django Project:** DripEmails  
**Location:** `docs/ai/`
