#!/usr/bin/env python3
"""
Package Script for DripEmails SMTP Server

This script extracts the SMTP server components from the main DripEmails project
and creates a standalone package ready for PyPI submission.
"""

import os
import shutil
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


def run_command(command, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def create_directory_structure(target_dir):
    """Create the package directory structure."""
    print_step("Creating package directory structure")
    
    # Create main directories
    directories = [
        target_dir,
        target_dir / "dripemails_smtp",
        target_dir / "dripemails_smtp" / "management",
        target_dir / "dripemails_smtp" / "management" / "commands",
        target_dir / "tests",
        target_dir / "docs",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print_success(f"Created directory: {directory}")


def copy_core_files(source_dir, target_dir):
    """Copy core SMTP server files."""
    print_step("Copying core SMTP server files")
    
    # Core SMTP server file
    source_file = source_dir / "core" / "smtp_server.py"
    target_file = target_dir / "dripemails_smtp" / "smtp_server.py"
    
    if source_file.exists():
        try:
            # Read with UTF-8 and write with UTF-8
            content = source_file.read_text(encoding='utf-8')
            target_file.write_text(content, encoding='utf-8')
            print_success(f"Copied: {source_file} -> {target_file}")
        except UnicodeDecodeError as e:
            print_error(f"Encoding error copying {source_file}: {e}")
            # Fallback to binary copy
            shutil.copy2(source_file, target_file)
            print_success(f"Copied (binary): {source_file} -> {target_file}")
    else:
        print_error(f"Source file not found: {source_file}")
        return False
    
    # Management command
    source_cmd = source_dir / "core" / "management" / "commands" / "run_smtp_server.py"
    target_cmd = target_dir / "dripemails_smtp" / "management" / "commands" / "run_smtp_server.py"
    
    if source_cmd.exists():
        try:
            # Read with UTF-8 and write with UTF-8
            content = source_cmd.read_text(encoding='utf-8')
            target_cmd.write_text(content, encoding='utf-8')
            print_success(f"Copied: {source_cmd} -> {target_cmd}")
        except UnicodeDecodeError as e:
            print_error(f"Encoding error copying {source_cmd}: {e}")
            # Fallback to binary copy
            shutil.copy2(source_cmd, target_cmd)
            print_success(f"Copied (binary): {source_cmd} -> {target_cmd}")
    else:
        print_error(f"Management command not found: {source_cmd}")
        return False
    
    # Create __init__.py files
    init_files = [
        target_dir / "dripemails_smtp" / "__init__.py",
        target_dir / "dripemails_smtp" / "management" / "__init__.py",
        target_dir / "dripemails_smtp" / "management" / "commands" / "__init__.py",
    ]
    
    for init_file in init_files:
        init_file.write_text("# DripEmails SMTP Server Package\n", encoding='utf-8')
        print_success(f"Created: {init_file}")
    
    return True


def copy_test_files(source_dir, target_dir):
    """Copy test files."""
    print_step("Copying test files")
    
    # Copy test directory
    source_test_dir = source_dir / "tests"
    target_test_dir = target_dir / "tests"
    
    if source_test_dir.exists():
        if target_test_dir.exists():
            shutil.rmtree(target_test_dir)
        shutil.copytree(source_test_dir, target_test_dir)
        print_success(f"Copied test directory: {source_test_dir} -> {target_test_dir}")
    else:
        print_error(f"Test directory not found: {source_test_dir}")
        return False
    
    return True


def copy_documentation_files(source_dir, target_dir):
    """Copy documentation files."""
    print_step("Copying documentation files")
    
    # Documentation files to copy
    doc_files = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "setup.py",
        "pyproject.toml",
        "MANIFEST.in",
        "requirements.txt",
        "smtp_config_example.json",
    ]
    
    for doc_file in doc_files:
        source_file = source_dir / doc_file
        target_file = target_dir / doc_file
        
        if source_file.exists():
            try:
                # For text files, ensure UTF-8 encoding
                if doc_file.endswith(('.md', '.txt', '.py', '.toml', '.in')):
                    # Read with UTF-8 and write with UTF-8
                    content = source_file.read_text(encoding='utf-8')
                    target_file.write_text(content, encoding='utf-8')
                else:
                    # For binary files, use regular copy
                    shutil.copy2(source_file, target_file)
                print_success(f"Copied: {source_file} -> {target_file}")
            except UnicodeDecodeError as e:
                print_error(f"Encoding error copying {source_file}: {e}")
                # Fallback to binary copy
                shutil.copy2(source_file, target_file)
                print_success(f"Copied (binary): {source_file} -> {target_file}")
        else:
            print_error(f"Documentation file not found: {source_file}")
    
    # Copy docs directory
    source_docs_dir = source_dir / "docs"
    target_docs_dir = target_dir / "docs"
    
    if source_docs_dir.exists():
        if target_docs_dir.exists():
            shutil.rmtree(target_docs_dir)
        shutil.copytree(source_docs_dir, target_docs_dir)
        print_success(f"Copied docs directory: {source_docs_dir} -> {target_docs_dir}")
    
    return True


def update_package_files(target_dir):
    """Update package files for the standalone version."""
    print_step("Updating package files for standalone version")
    
    # Update setup.py
    setup_file = target_dir / "setup.py"
    if setup_file.exists():
        try:
            content = setup_file.read_text(encoding='utf-8')
            # Update package name and description
            content = content.replace(
                'name="dripemails-smtp"',
                'name="dripemails-smtp-server"'
            )
            content = content.replace(
                'description="A modern, async SMTP server built with aiosmtpd for Python 3.11+."',
                'description="A standalone, modern, async SMTP server built with aiosmtpd for Python 3.11+."'
            )
            setup_file.write_text(content, encoding='utf-8')
            print_success("Updated setup.py")
        except Exception as e:
            print_error(f"Error updating setup.py: {e}")
    
    # Update pyproject.toml
    pyproject_file = target_dir / "pyproject.toml"
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text(encoding='utf-8')
            # Update package name
            content = content.replace(
                'name = "dripemails-smtp"',
                'name = "dripemails-smtp-server"'
            )
            pyproject_file.write_text(content, encoding='utf-8')
            print_success("Updated pyproject.toml")
        except Exception as e:
            print_error(f"Error updating pyproject.toml: {e}")
    
    # Update README.md
    readme_file = target_dir / "README.md"
    if readme_file.exists():
        try:
            content = readme_file.read_text(encoding='utf-8')
            # Update installation instructions
            content = content.replace(
                'pip install dripemails-smtp',
                'pip install dripemails-smtp-server'
            )
            content = content.replace(
                'git clone https://github.com/dripemails/dripemails-smtp.git',
                'git clone https://github.com/dripemails/smtp_server.git'
            )
            content = content.replace(
                'cd dripemails-smtp',
                'cd smtp_server'
            )
            readme_file.write_text(content, encoding='utf-8')
            print_success("Updated README.md")
        except Exception as e:
            print_error(f"Error updating README.md: {e}")
            print_error("This might be due to emoji characters in the README")
            print_error("The package will still work, but README.md wasn't updated")


def create_git_repository(target_dir):
    """Initialize git repository and add files."""
    print_step("Initializing git repository")
    
    # Initialize git repository
    if not run_command("git init", cwd=target_dir):
        return False
    
    # Add all files
    if not run_command("git add .", cwd=target_dir):
        return False
    
    # Initial commit
    if not run_command('git commit -m "Initial commit: DripEmails SMTP Server"', cwd=target_dir):
        return False
    
    # Add remote origin
    if not run_command("git remote add origin https://github.com/dripemails/smtp_server.git", cwd=target_dir):
        return False
    
    print_success("Git repository initialized and configured")
    return True


def build_package(target_dir):
    """Build the Python package."""
    print_step("Building Python package")
    
    # Install build tools
    if not run_command("pip install build twine"):
        return False
    
    # Build package
    if not run_command("python -m build", cwd=target_dir):
        return False
    
    print_success("Package built successfully")
    return True


def main():
    """Main packaging function."""
    print("🚀 DripEmails SMTP Server Packaging Script")
    print("=" * 60)
    
    # Get current directory (should be the dripemails.org workspace)
    current_dir = Path.cwd()
    target_dir = current_dir / "smtp_server"
    
    print(f"Source directory: {current_dir}")
    print(f"Target directory: {target_dir}")
    
    # Check if we're in the right directory
    if not (current_dir / "core" / "smtp_server.py").exists():
        print_error("This script must be run from the dripemails.org workspace directory")
        print_error("Please run this script from the directory containing the 'core' folder")
        sys.exit(1)
    
    # Create target directory if it doesn't exist
    if target_dir.exists():
        print(f"Target directory {target_dir} already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Aborting...")
            sys.exit(0)
        shutil.rmtree(target_dir)
    
    try:
        # Create directory structure
        create_directory_structure(target_dir)
        
        # Copy core files
        if not copy_core_files(current_dir, target_dir):
            sys.exit(1)
        
        # Copy test files
        if not copy_test_files(current_dir, target_dir):
            sys.exit(1)
        
        # Copy documentation files
        if not copy_documentation_files(current_dir, target_dir):
            sys.exit(1)
        
        # Update package files
        update_package_files(target_dir)
        
        # Initialize git repository
        if not create_git_repository(target_dir):
            sys.exit(1)
        
        # Build package
        if not build_package(target_dir):
            sys.exit(1)
        
        print_step("Packaging Complete!")
        print_success(f"SMTP server package created in: {target_dir}")
        print_success("Git repository initialized and ready for push")
        print_success("Package built and ready for PyPI submission")
        
        print("\n📋 Next Steps:")
        print("1. Review the package in the smtp_server directory")
        print("2. Push to GitHub: git push -u origin main")
        print("3. Upload to PyPI: python -m twine upload dist/*")
        print("4. Test installation: pip install dripemails-smtp-server")
        
    except Exception as e:
        print_error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 