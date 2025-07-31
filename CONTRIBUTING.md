# Contributing to DripEmails.org

Thank you for your interest in contributing to DripEmails.org! We welcome contributions from the community and appreciate your help in making this comprehensive email marketing platform better.

## 🤝 How to Contribute

### Reporting Issues

Before creating a new issue, please:

1. **Search existing issues** to see if your problem has already been reported
2. **Check the documentation** to see if there's already a solution
3. **Provide detailed information** including:
   - Python version (3.11+)
   - Django version
   - Operating system
   - Error messages and stack traces
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Browser/device information (for frontend issues)

### Suggesting Features

We welcome feature suggestions! Please:

1. **Describe the feature** clearly and concisely
2. **Explain the use case** and why it would be valuable
3. **Consider implementation** - is it feasible and maintainable?
4. **Check existing issues** to avoid duplicates
5. **Specify the component** (frontend, backend, SMTP server, etc.)

### Code Contributions

#### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/dripemails.org.git
   cd dripemails.org
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   npm install
   ```

5. **Set up environment**
   ```bash
   cp docs/env.example .env
   # Edit .env with your configuration
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Coding Standards

- **Python 3.11+**: Ensure compatibility with Python 3.11 and above
- **Django 4.0+**: Follow Django best practices and conventions
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Add docstrings to all public functions and classes
- **Code formatting**: Use Black for Python code formatting
- **Linting**: Follow PEP 8 guidelines and use flake8
- **JavaScript/TypeScript**: Use ESLint and Prettier
- **CSS**: Follow Tailwind CSS conventions

#### Testing

1. **Write tests** for new features and bug fixes
2. **Run existing tests** to ensure nothing breaks
   ```bash
   # Run all Django tests
   python manage.py test
   
   # Run specific app tests
   python manage.py test campaigns
   python manage.py test subscribers
   python manage.py test analytics
   
   # Run SMTP server tests
   cd smtp_server
   python -m pytest tests/
   ```
3. **Check test coverage**
   ```bash
   pytest --cov=core --cov=campaigns --cov=subscribers --cov=analytics tests/
   ```

#### Code Quality

Before submitting a pull request:

1. **Format your Python code**
   ```bash
   black core/ campaigns/ subscribers/ analytics/ tests/
   ```

2. **Run Python linting**
   ```bash
   flake8 core/ campaigns/ subscribers/ analytics/ tests/
   ```

3. **Run type checking**
   ```bash
   mypy core/ campaigns/ subscribers/ analytics/
   ```

4. **Format your JavaScript/TypeScript code**
   ```bash
   npm run lint:fix
   ```

5. **Run all tests**
   ```bash
   python manage.py test
   npm test
   ```

### Pull Request Process

1. **Update documentation** if your changes affect user-facing features
2. **Add tests** for new functionality
3. **Update CHANGELOG.md** with a brief description of your changes
4. **Ensure all tests pass** and code quality checks are satisfied
5. **Request review** from maintainers

### Development Guidelines

#### Django Development
- Follow Django's MVT (Model-View-Template) pattern
- Use Django REST Framework for API endpoints
- Implement proper model relationships and constraints
- Use Django's built-in security features
- Follow Django's naming conventions

#### Frontend Development
- Use React functional components with hooks
- Implement TypeScript for type safety
- Follow Tailwind CSS utility-first approach
- Ensure responsive design for mobile devices
- Implement proper error handling and loading states

#### SMTP Server Development
- Maintain async/await patterns for performance
- Implement proper error handling and logging
- Follow aiosmtpd conventions and best practices
- Ensure backward compatibility with existing configurations
- Add comprehensive tests for new features

#### Database Changes
- Create proper migrations for model changes
- Include both forward and backward migrations
- Test migrations on sample data
- Document any breaking changes

## 🏗️ Project Structure

```
dripemails.org/
├── core/                    # Core Django app with SMTP server
├── campaigns/               # Email campaign management
├── subscribers/             # Subscriber management
├── analytics/               # Analytics and reporting
├── smtp_server/             # Standalone SMTP server package
├── templates/               # Django templates
├── static/                  # Static assets
├── src/                     # React frontend source
├── docs/                    # Documentation
└── tests/                   # Test suite
```

## 🧪 Testing Strategy

### Backend Testing
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **API Tests**: Test REST API endpoints
- **SMTP Tests**: Test email server functionality

### Frontend Testing
- **Component Tests**: Test React components
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows

### Performance Testing
- **Load Testing**: Test system under high load
- **Email Processing**: Test SMTP server performance
- **Database Performance**: Test query optimization

## 📚 Documentation

### Code Documentation
- **Docstrings**: Comprehensive docstrings for all functions
- **Type Hints**: Use type hints for better code understanding
- **Comments**: Add comments for complex logic
- **README Updates**: Update relevant README files

### User Documentation
- **API Documentation**: Document all API endpoints
- **Installation Guides**: Update installation instructions
- **Configuration**: Document configuration options
- **Troubleshooting**: Add common issues and solutions

## 🔒 Security

### Security Guidelines
- **Input Validation**: Validate all user inputs
- **SQL Injection**: Use Django ORM to prevent SQL injection
- **XSS Protection**: Use Django's built-in XSS protection
- **CSRF Protection**: Implement CSRF protection for forms
- **Authentication**: Use secure authentication methods
- **Data Encryption**: Encrypt sensitive data

### Security Reporting
- **Responsible Disclosure**: Report security issues privately
- **Security Issues**: Create private security issues
- **CVE Reporting**: Follow CVE reporting guidelines

## 🚀 Deployment

### Production Considerations
- **Environment Variables**: Use environment variables for configuration
- **Database Migrations**: Test migrations in staging environment
- **Static Files**: Configure proper static file serving
- **SSL/TLS**: Implement proper SSL/TLS configuration
- **Monitoring**: Set up monitoring and alerting

## 📞 Getting Help

- **GitHub Issues**: Create issues for bugs and feature requests
- **GitHub Discussions**: Use discussions for questions and ideas
- **Documentation**: Check the docs/ directory for guides
- **Code Examples**: Look at existing code for patterns

## 🎯 Contribution Areas

We welcome contributions in these areas:

### Backend Development
- Django application development
- API endpoint implementation
- Database optimization
- SMTP server enhancements
- Background task processing

### Frontend Development
- React component development
- UI/UX improvements
- Responsive design
- Performance optimization
- Accessibility improvements

### DevOps & Infrastructure
- Docker containerization
- CI/CD pipeline improvements
- Deployment automation
- Monitoring and logging
- Security hardening

### Documentation
- API documentation
- User guides
- Developer documentation
- Tutorial creation
- Code examples

### Testing
- Test coverage improvement
- Performance testing
- Security testing
- Integration testing
- End-to-end testing

Thank you for contributing to DripEmails.org! Your contributions help make this platform better for everyone. 