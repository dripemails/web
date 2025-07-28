# PyPI Upload Guide for DripEmails SMTP Server

This guide will help you upload your package to PyPI successfully.

## 🚀 Quick Upload

### Option 1: Use the Upload Script (Recommended)

```bash
# From the smtp_server directory
python upload_to_pypi.py
```

### Option 2: Manual Upload

```bash
# From the smtp_server directory
python -m twine upload dist/*
```

## 🔑 PyPI Authentication

### Method 1: API Token (Recommended)

1. **Get your API token:**
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with "Entire account" scope
   - Copy the token (it starts with `pypi-`)

2. **Use the token:**
   - Username: `__token__`
   - Password: `pypi-your-token-here`

### Method 2: .pypirc File

Create `~/.pypirc` (Linux/macOS) or `%USERPROFILE%\.pypirc` (Windows):

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-your-api-token-here
```

### Method 3: Environment Variables

```bash
# Linux/macOS
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-your-api-token-here"

# Windows
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-your-api-token-here
```

## 🔧 Common Issues & Solutions

### Issue 1: "HTTPError: 403 Client Error: Invalid or non-existent authentication information"

**Solution:**
- Make sure you're using `__token__` as username (with double underscores)
- Ensure your API token starts with `pypi-`
- Check that the token has the correct permissions

### Issue 2: "HTTPError: 400 Client Error: File already exists"

**Solution:**
- Update the version number in `setup.py` and `pyproject.toml`
- Rebuild the package: `python -m build`
- Upload again

### Issue 3: "HTTPError: 401 Client Error: You are not allowed to upload to 'dripemails-smtp-server'"

**Solution:**
- Check if the package name is available on PyPI
- Try a different package name if needed
- Ensure you own the package name

### Issue 4: "ModuleNotFoundError: No module named 'twine'"

**Solution:**
```bash
pip install twine
```

### Issue 5: "distutils.errors.DistutilsError: Could not find suitable distribution"

**Solution:**
- Make sure you're in the correct directory (smtp_server/)
- Run the packaging script first: `python package_smtp_server.py`
- Check that `dist/` directory exists with package files

## 📋 Step-by-Step Upload Process

### 1. Prepare Your Package

```bash
# Make sure you're in the smtp_server directory
cd smtp_server

# Check if package files exist
ls dist/
```

### 2. Validate Your Package

```bash
# Check package for issues
python -m twine check dist/*
```

### 3. Upload to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
```

### 4. Verify Upload

```bash
# Check if package is available
pip install dripemails-smtp-server
```

## 🧪 TestPyPI (Optional)

For testing before uploading to PyPI:

### 1. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

### 2. Install from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ dripemails-smtp-server
```

## 🔍 Troubleshooting Commands

### Check Package Files

```bash
# List package files
ls -la dist/

# Check package contents
python -m twine check dist/*
```

### Check PyPI Configuration

```bash
# Check if .pypirc exists
cat ~/.pypirc

# Check environment variables
echo $TWINE_USERNAME
echo $TWINE_PASSWORD
```

### Validate Package

```bash
# Check package metadata
python -m twine check dist/*

# Test package installation
pip install --no-index --find-links dist/ dripemails-smtp-server
```

## 📞 Getting Help

If you're still having issues:

1. **Check PyPI Status:** https://status.python.org/
2. **PyPI Documentation:** https://packaging.python.org/tutorials/packaging-projects/
3. **Twine Documentation:** https://twine.readthedocs.io/

## 🎯 Success Checklist

- [ ] Package builds successfully
- [ ] Package validation passes
- [ ] PyPI credentials are correct
- [ ] Package name is available
- [ ] Version number is unique
- [ ] Upload completes without errors
- [ ] Package is visible on PyPI
- [ ] Package installs correctly

## 🚨 Important Notes

- **Never commit API tokens** to version control
- **Use API tokens** instead of passwords for better security
- **Test on TestPyPI** before uploading to PyPI
- **Update version numbers** for each release
- **Keep .pypirc file secure** with proper permissions 