# Changelog

All notable changes to DripEmails SMTP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of DripEmails SMTP Server
- Modern async SMTP server built with aiosmtpd
- Python 3.11+ compatibility
- Django integration support
- Webhook notification system
- Database logging capabilities
- Rate limiting and domain restrictions
- Debug mode with comprehensive logging
- Authentication support (PLAIN and LOGIN)
- Command-line interface
- Management command for Django integration
- Comprehensive test suite
- Production deployment guides
- Documentation and examples

### Features
- **Email Processing**: Parse and process incoming emails
- **Metadata Extraction**: Extract sender, recipient, subject, body, and headers
- **Database Storage**: Store email metadata in Django models
- **Webhook Integration**: Forward email data to external services
- **Domain Validation**: Restrict email delivery to allowed domains
- **Rate Limiting**: Protect against spam and abuse
- **Authentication**: Support for SMTP authentication
- **Logging**: File-based and console logging
- **Statistics**: Track server performance and usage

### Technical Details
- Built with aiosmtpd 1.4.4+
- Async/await patterns for high performance
- Type hints throughout the codebase
- Comprehensive error handling
- Modular architecture for easy extension
- Production-ready configuration options

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Core SMTP server functionality
- Django integration
- Webhook support
- Database logging
- Authentication system
- Rate limiting
- Debug mode
- Command-line interface
- Management commands
- Test suite
- Documentation

### Known Issues
- Session.peer compatibility issues with some aiosmtpd versions
- Authentication requires additional testing in production environments
- Webhook functionality requires aiohttp dependency

### Future Plans
- Enhanced authentication mechanisms
- SSL/TLS support
- Advanced spam filtering
- Performance optimizations
- Additional webhook formats
- Monitoring and metrics
- Docker containerization
- Kubernetes deployment guides 