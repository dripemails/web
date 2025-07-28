#!/bin/bash

echo "🚀 DripEmails SMTP Server Packaging Script for Linux/macOS"
echo "========================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "core/smtp_server.py" ]; then
    echo "❌ This script must be run from the dripemails.org workspace directory"
    echo "Please run this script from the directory containing the 'core' folder"
    exit 1
fi

echo "✅ Python found and directory structure looks correct"
echo

# Run the packaging script
python3 package_smtp_server.py

if [ $? -ne 0 ]; then
    echo
    echo "❌ Packaging failed. Please check the error messages above."
    exit 1
fi

echo
echo "✅ Packaging completed successfully!"
echo
echo "📋 Next Steps:"
echo "1. Review the package in the smtp_server directory"
echo "2. Push to GitHub: git push -u origin main"
echo "3. Upload to PyPI: python -m twine upload dist/*"
echo "4. Test installation: pip install dripemails-smtp-server"
echo 