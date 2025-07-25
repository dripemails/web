# Contributing to DripEmails SMTP Server

Thank you for your interest in contributing to DripEmails SMTP Server! We welcome contributions from the community and appreciate your help in making this project better.

## 🤝 How to Contribute

### Reporting Issues

Before creating a new issue, please:

1. **Search existing issues** to see if your problem has already been reported
2. **Check the documentation** to see if there's already a solution
3. **Provide detailed information** including:
   - Python version
   - Operating system
   - Error messages and stack traces
   - Steps to reproduce the issue
   - Expected vs actual behavior

### Suggesting Features

We welcome feature suggestions! Please:

1. **Describe the feature** clearly and concisely
2. **Explain the use case** and why it would be valuable
3. **Consider implementation** - is it feasible and maintainable?
4. **Check existing issues** to avoid duplicates

### Code Contributions

#### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/dripemails-smtp.git
   cd dripemails-smtp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Coding Standards

- **Python 3.11+**: Ensure compatibility with Python 3.11 and above
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Add docstrings to all public functions and classes
- **Code formatting**: Use Black for code formatting
- **Linting**: Follow PEP 8 guidelines and use flake8

#### Testing

1. **Write tests** for new features and bug fixes
2. **Run existing tests** to ensure nothing breaks
   ```bash
   pytest tests/
   ```
3. **Check test coverage**
   ```bash
   pytest --cov=core tests/
   ```

#### Code Quality

Before submitting a pull request:

1. **Format your code**
   ```bash
   black core/ tests/
   ```

2. **Run linting**
   ```bash
   flake8 core/ tests/
   ```

3. **Run type checking**
   ```bash
   mypy core/
   ```

4. **Run all tests**
   ```bash
   pytest
   ```

### Pull Request Process

1. **Create a pull request** with a clear description of your changes
2. **Reference issues** that your PR addresses
3. **Include tests** for new functionality
4. **Update documentation** if needed
5. **Ensure CI passes** before requesting review

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add webhook authentication support
fix: resolve session.peer compatibility issue
docs: update installation instructions
test: add tests for email processing
```

## 📋 Development Guidelines

### Architecture

- **Keep it simple**: Prefer simple, readable code over complex solutions
- **Async first**: Use async/await patterns where appropriate
- **Error handling**: Provide meaningful error messages and graceful degradation
- **Logging**: Use appropriate log levels and include context

### Security

- **Input validation**: Validate all user inputs
- **Authentication**: Implement secure authentication mechanisms
- **Rate limiting**: Protect against abuse and spam
- **Dependencies**: Keep dependencies updated and secure

### Performance

- **Async operations**: Use async I/O for network operations
- **Memory efficiency**: Avoid unnecessary object creation
- **Database queries**: Optimize database operations
- **Resource cleanup**: Ensure proper cleanup of resources

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/
│   ├── test_email_processor.py
│   ├── test_smtp_server.py
│   └── test_webhook.py
├── integration/
│   ├── test_django_integration.py
│   └── test_smtp_communication.py
└── fixtures/
    └── sample_emails/
```

### Test Requirements

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Edge cases**: Test error conditions and boundary cases
- **Performance tests**: Test with realistic load

### Mocking

- **External services**: Mock webhook calls and database operations
- **Network calls**: Mock SMTP client connections
- **Time-dependent code**: Mock datetime operations

## 📚 Documentation

### Code Documentation

- **Docstrings**: Use Google-style docstrings
- **Type hints**: Include type hints for all public APIs
- **Examples**: Provide usage examples in docstrings

### User Documentation

- **README**: Keep the README up to date
- **API docs**: Document all public APIs
- **Examples**: Provide working examples
- **Troubleshooting**: Include common issues and solutions

## 🚀 Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Changelog is updated
- [ ] Version is bumped
- [ ] Release notes are written

## 🏷️ Labels

We use the following labels for issues and PRs:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested
- `wontfix`: This will not be worked on

## 📞 Getting Help

If you need help with contributing:

- **GitHub Discussions**: Ask questions and share ideas
- **GitHub Issues**: Report bugs and request features
- **Email**: Contact us at founders@dripemails.org

## 🙏 Recognition

Contributors will be recognized in:

- **README**: List of contributors
- **Release notes**: Credit for significant contributions
- **Documentation**: Attribution for major features

Thank you for contributing to DripEmails SMTP Server! 🎉 