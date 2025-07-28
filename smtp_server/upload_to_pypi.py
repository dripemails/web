#!/usr/bin/env python3
"""
PyPI Upload Script for DripEmails SMTP Server

This script helps upload the package to PyPI with proper authentication
and error handling.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_step(message):
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"🔄 {message}")
    print(f"{'='*60}")


def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")


def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  {message}")


def run_command(command, cwd=None, capture_output=True):
    """Run a command and return result."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout, result.stderr
        else:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                check=True
            )
            return True, "", ""
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_package_files():
    """Check if package files exist."""
    print_step("Checking package files")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print_error("dist/ directory not found")
        print_error("Please run the packaging script first")
        return False
    
    files = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
    if not files:
        print_error("No package files found in dist/ directory")
        print_error("Please run the packaging script first")
        return False
    
    print_success(f"Found {len(files)} package file(s):")
    for file in files:
        print(f"  - {file.name}")
    
    return True


def check_twine_installation():
    """Check if twine is installed."""
    print_step("Checking twine installation")
    
    success, stdout, stderr = run_command("python -m twine --version")
    if not success:
        print_error("twine is not installed")
        print_error("Installing twine...")
        
        install_success, _, _ = run_command("pip install twine")
        if not install_success:
            print_error("Failed to install twine")
            return False
        
        print_success("twine installed successfully")
    else:
        print_success("twine is already installed")
        print(f"Version: {stdout.strip()}")
    
    return True


def check_pypi_config():
    """Check PyPI configuration."""
    print_step("Checking PyPI configuration")
    
    # Check for .pypirc file
    pypirc_file = Path.home() / ".pypirc"
    if pypirc_file.exists():
        print_success("Found .pypirc file")
        try:
            content = pypirc_file.read_text(encoding='utf-8')
            if "username" in content and "password" in content:
                print_success("PyPI credentials configured in .pypirc")
                return True
            else:
                print_warning(".pypirc file exists but may not have proper credentials")
        except Exception as e:
            print_error(f"Error reading .pypirc file: {e}")
    else:
        print_warning("No .pypirc file found")
    
    # Check environment variables
    if os.environ.get("TWINE_USERNAME") and os.environ.get("TWINE_PASSWORD"):
        print_success("PyPI credentials found in environment variables")
        return True
    
    print_warning("No PyPI credentials found")
    print_warning("You will be prompted for username and password during upload")
    return True


def test_pypi_connection():
    """Test connection to PyPI."""
    print_step("Testing PyPI connection")
    
    success, stdout, stderr = run_command("python -m twine check dist/*")
    if not success:
        print_error("Package validation failed")
        print_error(f"Error: {stderr}")
        return False
    
    print_success("Package validation passed")
    return True


def upload_to_pypi():
    """Upload package to PyPI."""
    print_step("Uploading to PyPI")
    
    print("🚀 Starting upload to PyPI...")
    print("📝 You will be prompted for your PyPI credentials")
    print("🔑 Use your PyPI username and API token as password")
    print()
    
    # Upload to PyPI
    success, stdout, stderr = run_command("python -m twine upload dist/*", capture_output=False)
    
    if success:
        print_success("Package uploaded successfully to PyPI!")
        print()
        print("🎉 Your package is now available on PyPI!")
        print("📦 Install it with: pip install dripemails-smtp-server")
        return True
    else:
        print_error("Upload failed")
        print_error("Please check your credentials and try again")
        return False


def create_pypirc_template():
    """Create a template .pypirc file."""
    print_step("Creating .pypirc template")
    
    pypirc_content = """[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
"""
    
    pypirc_file = Path.home() / ".pypirc"
    
    if pypirc_file.exists():
        print_warning(".pypirc file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .pypirc creation")
            return
    
    try:
        pypirc_file.write_text(pypirc_content, encoding='utf-8')
        print_success(f"Created .pypirc template at {pypirc_file}")
        print()
        print("📝 Please edit the .pypirc file and replace:")
        print("   - 'pypi-your-api-token-here' with your actual PyPI API token")
        print("   - 'pypi-your-test-api-token-here' with your TestPyPI API token (optional)")
        print()
        print("🔒 Make sure to keep your API token secure!")
    except Exception as e:
        print_error(f"Failed to create .pypirc file: {e}")


def main():
    """Main upload function."""
    print("🚀 DripEmails SMTP Server - PyPI Upload Script")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("dist").exists():
        print_error("This script must be run from the smtp_server directory")
        print_error("Please run this script from the directory containing the 'dist' folder")
        sys.exit(1)
    
    try:
        # Check package files
        if not check_package_files():
            sys.exit(1)
        
        # Check twine installation
        if not check_twine_installation():
            sys.exit(1)
        
        # Check PyPI configuration
        if not check_pypi_config():
            print_warning("No PyPI credentials found")
            response = input("Do you want to create a .pypirc template? (y/N): ")
            if response.lower() == 'y':
                create_pypirc_template()
                print()
                print("📝 After editing .pypirc, run this script again")
                sys.exit(0)
        
        # Test PyPI connection
        if not test_pypi_connection():
            sys.exit(1)
        
        # Upload to PyPI
        if not upload_to_pypi():
            sys.exit(1)
        
        print_step("Upload Complete!")
        print_success("Your package has been successfully uploaded to PyPI!")
        print()
        print("📋 Next Steps:")
        print("1. Verify your package on PyPI: https://pypi.org/project/dripemails-smtp-server/")
        print("2. Test installation: pip install dripemails-smtp-server")
        print("3. Update your GitHub repository with the new release")
        
    except KeyboardInterrupt:
        print("\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 