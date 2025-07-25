#!/usr/bin/env python3
"""
Setup script for DripEmails SMTP Server

A modern, async SMTP server built with aiosmtpd for Python 3.11+.
Perfect for development, testing, and production email handling.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dripemails-smtp",
    version="1.0.0",
    author="DripEmails Team",
    author_email="founders@dripemails.org",
    description="A modern, async SMTP server built with aiosmtpd for Python 3.11+",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dripemails/dripemails-smtp",
    project_urls={
        "Bug Tracker": "https://github.com/dripemails/dripemails-smtp/issues",
        "Documentation": "https://github.com/dripemails/dripemails-smtp/blob/main/README.md",
        "Source Code": "https://github.com/dripemails/dripemails-smtp",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email :: Mail Transport Agents",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "django": [
            "django>=4.0.0",
        ],
        "webhook": [
            "aiohttp>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dripemails-smtp=core.smtp_server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="smtp email server aiosmtpd async python",
    license="MIT",
    platforms=["any"],
) 