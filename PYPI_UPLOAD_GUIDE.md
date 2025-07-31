# PyPI Upload Guide for DripEmails.org Components

This guide will help you upload DripEmails.org packages to PyPI successfully.

## 📦 Available Packages

DripEmails.org consists of multiple components that can be published to PyPI:

1. **dripemails-smtp-server** - Standalone SMTP server component
2. **dripemails-core** - Core Django application (future)
3. **dripemails-campaigns** - Campaign management (future)
4. **dripemails-analytics** - Analytics and reporting (future)

## 🚀 Quick Upload

### SMTP Server Package

```bash
# From the smtp_server directory
cd smtp_server
python upload_to_pypi.py
```

### Manual Upload

```bash
# From the smtp_server directory
cd smtp_server
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
# Navigate to the component directory
cd smtp_server

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Update version numbers
# Edit setup.py and pyproject.toml with new version
```

### 2. Build the Package

```bash
# Build the package
python -m build

# Or use the packaging script
python package_smtp_server.py
```

### 3. Test the Package

```bash
# Test upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ dripemails-smtp-server
```

### 4. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

## 📝 Package Configuration

### SMTP Server Package (smtp_server/)

```python
# setup.py
setup(
    name="dripemails-smtp-server",
    version="1.0.0",
    description="Custom SMTP server for DripEmails.org",
    long_description=read("README.md"),
    author="DripEmails Team",
    author_email="founders@dripemails.org",
    url="https://github.com/dripemails/dripemails.org",
    packages=find_packages(),
    install_requires=[
        "aiosmtpd>=1.4.4",
        "django>=4.0",
        "aiohttp>=3.8.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
```

### Future Packages

#### Core Package (core/)
```python
# Future setup.py for core package
setup(
    name="dripemails-core",
    version="1.0.0",
    description="Core Django application for DripEmails.org",
    # ... configuration
)
```

#### Campaigns Package (campaigns/)
```python
# Future setup.py for campaigns package
setup(
    name="dripemails-campaigns",
    version="1.0.0",
    description="Campaign management for DripEmails.org",
    # ... configuration
)
```

## 🔄 Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/) for all packages:

- **MAJOR.MINOR.PATCH**
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Version Update Process

1. **Update version in multiple files:**
   - `setup.py`
   - `pyproject.toml`
   - `__init__.py` (if applicable)
   - `CHANGELOG.md`

2. **Update CHANGELOG.md:**
   - Add new version section
   - Document all changes
   - Follow [Keep a Changelog](https://keepachangelog.com/) format

3. **Commit and tag:**
   ```bash
   git add .
   git commit -m "Release version 1.0.0"
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin main --tags
   ```

## 🧪 Testing Before Upload

### Local Testing

```bash
# Install package in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Test functionality
python -c "import dripemails_smtp; print('Package works!')"
```

### TestPyPI Testing

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ dripemails-smtp-server

# Test installation
python -c "import dripemails_smtp; print('TestPyPI package works!')"
```

## 📊 Package Statistics

After successful upload, you can monitor your package:

- **PyPI Page**: https://pypi.org/project/dripemails-smtp-server/
- **Download Statistics**: https://pypistats.org/packages/dripemails-smtp-server
- **GitHub Releases**: https://github.com/dripemails/dripemails.org/releases

## 🚨 Security Considerations

### Package Security

- **Sign your packages** with GPG for additional security
- **Use API tokens** instead of username/password
- **Regular updates** to fix security vulnerabilities
- **Dependency scanning** for known vulnerabilities

### Upload Security

- **Never commit** API tokens to version control
- **Use environment variables** for sensitive data
- **Test on TestPyPI** before production upload
- **Verify package contents** before upload

## 📞 Support

If you encounter issues with package uploads:

1. **Check PyPI Status**: https://status.python.org/
2. **Review PyPI Documentation**: https://packaging.python.org/
3. **Create GitHub Issue**: https://github.com/dripemails/dripemails.org/issues
4. **Contact Maintainers**: founders@dripemails.org

## 🎯 Best Practices

1. **Always test** on TestPyPI first
2. **Update documentation** with new features
3. **Follow semantic versioning** strictly
4. **Maintain changelog** for all releases
5. **Use automated tools** for packaging when possible
6. **Verify package integrity** after upload
7. **Monitor package statistics** and user feedback 