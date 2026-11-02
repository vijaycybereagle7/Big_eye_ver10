# Contributing to Cybersecurity Database System

Thank you for your interest in contributing to the Cybersecurity Database System! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality](#code-quality)
- [Documentation](#documentation)
- [Security Guidelines](#security-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at conduct@yourorg.com.

## Getting Started

### Ways to Contribute

We welcome various types of contributions:

- **Code**: Bug fixes, new features, performance improvements
- **Documentation**: Improvements to README, API docs, guides
- **Testing**: Adding test cases, improving test coverage
- **Reviews**: Peer review of pull requests
- **Design**: UI/UX improvements, system design
- **Community**: Help other users, participate in discussions

### Before You Start

1. Check existing issues and pull requests
2. Create an issue to discuss major changes
3. Ask questions in discussions if unsure
4. Read the codebase and architecture documentation

## Development Environment

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL 14+ / MongoDB 5.0+
- Redis 6.0+
- Git
- Node.js 16+ (for frontend development)

### Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/cybersecurity-database-system.git
   cd cybersecurity-database-system
   ```

2. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/your-org/cybersecurity-database-system.git
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r api/requirements.txt
   pip install -r testing/requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Start Development Environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

7. **Run Tests**
   ```bash
   python -m pytest testing/
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/threat-intelligence-new-source`
- `fix/anomaly-detection-memory-leak`
- `docs/improve-api-documentation`
- `security/add-rate-limiting`
- `performance/database-query-optimization`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(api): add new threat intelligence endpoint
fix(database): resolve connection pooling issue
docs(readme): update installation instructions
test(ml): add unit tests for anomaly detection
security(api): implement rate limiting
perf(database): optimize query performance
refactor(auth): simplify token validation logic
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `security`: Security-related changes
- `perf`: Performance improvements

### Code Style

#### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all functions
- Write docstrings for all public functions and classes

#### Formatting Code

```bash
# Format code
black *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
isort *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/

# Check formatting
black --check *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
isort --check-only *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
```

#### Linting

```bash
# Lint code
flake8 *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
mypy *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/

# Security scan
bandit -r api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
```

### Code Quality Standards

1. **Readability**: Code should be self-documenting and easy to understand
2. **DRY (Don't Repeat Yourself)**: Avoid code duplication
3. **Single Responsibility**: Each function/class should have one clear purpose
4. **Error Handling**: Proper error handling and logging
5. **Performance**: Consider performance implications of changes
6. **Security**: Follow security best practices

### Example Code Structure

```python
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.models import ThreatIndicator
from database.connection import get_db

logger = logging.getLogger(__name__)


class ThreatIntelligenceService:
    """Service for managing threat intelligence data."""
    
    def __init__(self, db_connection: Optional[Any] = None):
        """Initialize the service.
        
        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection or get_db()
        self._cache = {}
    
    async def get_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Get reputation data for an IP address.
        
        Args:
            ip_address: IP address to query
            
        Returns:
            Dictionary containing reputation information
            
        Raises:
            ValueError: If IP address is invalid
            DatabaseError: If database operation fails
        """
        if not self._is_valid_ip(ip_address):
            raise ValueError(f"Invalid IP address: {ip_address}")
        
        try:
            # Check cache first
            if ip_address in self._cache:
                logger.debug(f"Returning cached data for {ip_address}")
                return self._cache[ip_address]
            
            # Query database
            result = await self.db.fetch_threat_data(ip_address)
            
            # Process and cache result
            processed_result = self._process_reputation_data(result)
            self._cache[ip_address] = processed_result
            
            logger.info(f"Retrieved reputation data for {ip_address}")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error retrieving reputation for {ip_address}: {e}")
            raise DatabaseError(f"Failed to get reputation for {ip_address}") from e
    
    @staticmethod
    def _is_valid_ip(ip_address: str) -> bool:
        """Validate IP address format.
        
        Args:
            ip_address: IP address to validate
            
        Returns:
            True if valid, False otherwise
        """
        parts = ip_address.split('.')
        return (len(parts) == 4 and 
                all(0 <= int(part) <= 255 for part in parts))
    
    def _process_reputation_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw reputation data.
        
        Args:
            raw_data: Raw data from database
            
        Returns:
            Processed reputation data
        """
        return {
            'ip': raw_data.get('ip_address'),
            'reputation_score': raw_data.get('score', 0),
            'threat_categories': raw_data.get('categories', []),
            'last_seen': raw_data.get('updated_at'),
            'sources': raw_data.get('sources', [])
        }
```

## Testing Guidelines

### Test Structure

```
testing/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── load/           # Load and performance tests
├── fixtures/       # Test fixtures and test data
├── mocks/          # Mock objects and utilities
└── coverage/       # Coverage reporting tools
```

### Writing Tests

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **Load Tests**: Test system under stress
4. **Security Tests**: Test security controls

### Test Examples

```python
import pytest
from unittest.mock import Mock, patch
from ai_ml.anomaly_detection.anomaly_detector import AnomalyDetector
from database.postgresql.connection import get_db_connection

class TestAnomalyDetector:
    """Test cases for AnomalyDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance for testing."""
        return AnomalyDetector()
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'protocol': 'TCP',
            'port': 80,
            'bytes_sent': 1024000,
            'duration': 300
        }
    
    def test_detect_anomalies_valid_data(self, detector, sample_data):
        """Test anomaly detection with valid data."""
        anomalies = detector.detect(sample_data)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) >= 0
        
        # If anomalies detected, check structure
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'score' in anomaly
            assert 'description' in anomaly
            assert 0 <= anomaly['score'] <= 1
    
    def test_detect_anomalies_missing_fields(self, detector):
        """Test anomaly detection with missing required fields."""
        incomplete_data = {'src_ip': '192.168.1.100'}
        
        with pytest.raises(ValueError):
            detector.detect(incomplete_data)
    
    @patch('database.postgresql.connection.get_db_connection')
    async def test_database_integration(self, mock_db, detector):
        """Test integration with database."""
        mock_db.return_value.fetch_threat_data.return_value = {
            'score': 0.8,
            'categories': ['malware', 'phishing']
        }
        
        result = await detector.get_reputation_with_db('192.168.1.1')
        
        assert result['score'] == 0.8
        assert 'malware' in result['categories']
        mock_db.return_value.fetch_threat_data.assert_called_once_with('192.168.1.1')
```

### Running Tests

```bash
# Run all tests
python -m pytest testing/ -v

# Run specific test category
python -m pytest testing/unit/ -v
python -m pytest testing/integration/ -v
python -m pytest testing/load/ -v

# Run with coverage
python -m pytest testing/ --cov=api --cov=ai_ml --cov=threat_intelligence --cov-report=html

# Run specific test file
python -m pytest testing/unit/test_anomaly_detection.py -v

# Run with markers
python -m pytest testing/ -m "not slow"
python -m pytest testing/ -m "integration"
```

## Documentation

### Documentation Types

1. **API Documentation**: Auto-generated from docstrings
2. **User Guides**: Step-by-step usage instructions
3. **Developer Documentation**: Architecture and design docs
4. **Admin Guides**: Deployment and configuration guides

### Writing Documentation

#### Docstring Format

Use Google-style docstrings:

```python
def get_threat_intelligence(ip_address: str) -> Dict[str, Any]:
    """Get threat intelligence for an IP address.
    
    This function queries multiple threat intelligence sources to provide
    comprehensive reputation data for the given IP address.
    
    Args:
        ip_address: IP address to analyze. Must be a valid IPv4 or IPv6 address.
        
    Returns:
        Dictionary containing:
        - reputation_score (float): Reputation score from 0.0 to 1.0
        - threat_categories (list): Categories of threats associated with IP
        - sources (list): List of intelligence sources that reported this IP
        - last_seen (datetime): When the IP was last observed
        
    Raises:
        ValueError: If ip_address is not a valid IP address
        APIError: If threat intelligence service is unavailable
        RateLimitError: If API rate limit is exceeded
        
    Example:
        >>> result = get_threat_intelligence('192.168.1.1')
        >>> print(result['reputation_score'])
        0.85
    """
    # Function implementation
```

#### README Updates

When making significant changes, update relevant sections of the README:
- Installation instructions
- Usage examples
- Configuration options
- Breaking changes

### Documentation Tools

- **API Docs**: Generated from code using Sphinx
- **User Guides**: Written in Markdown
- **Diagrams**: Created with Mermaid or PlantUML

## Security Guidelines

### Security Checklist

Before submitting a PR, ensure:

- [ ] No hardcoded passwords or API keys
- [ ] Input validation implemented
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (proper output encoding)
- [ ] CSRF protection for state-changing operations
- [ ] Rate limiting implemented where appropriate
- [ ] Logging of security-relevant events
- [ ] No sensitive data in error messages
- [ ] Proper authentication and authorization
- [ ] Secure random number generation

### Security Best Practices

1. **Input Validation**
   ```python
   from pydantic import BaseModel, validator, ValidationError
   
   class ThreatQuery(BaseModel):
       ip_address: str
       
       @validator('ip_address')
       def validate_ip(cls, v):
           # IP validation logic
           if not is_valid_ip(v):
               raise ValueError('Invalid IP address format')
           return v
   ```

2. **SQL Injection Prevention**
   ```python
   # Good: Parameterized query
   query = "SELECT * FROM threats WHERE ip = $1"
   result = await db.fetch(query, ip_address)
   
   # Bad: String concatenation
   query = f"SELECT * FROM threats WHERE ip = '{ip_address}'"  # DON'T DO THIS
   ```

3. **Authentication**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   async def get_current_user(token: str = Depends(security)):
       try:
           payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
           user_id = payload.get("sub")
           if user_id is None:
               raise HTTPException(status_code=401, detail="Invalid authentication")
       except JWTError:
           raise HTTPException(status_code=401, detail="Invalid authentication")
       
       user = await get_user(user_id)
       if user is None:
           raise HTTPException(status_code=401, detail="User not found")
       return user
   ```

## Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Code Quality**: Run linting and formatting tools
3. **Security Scan**: Run security scanning tools
4. **Documentation**: Update documentation if needed
5. **Changelog**: Update CHANGELOG.md if applicable

### PR Template

When creating a PR, use the provided template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Security fix
- [ ] Performance improvement

## Changes Made
- List specific changes
- Include any dependencies

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Security testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Security considerations addressed

## Related Issues
Closes #issue_number

## Screenshots (if applicable)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: At least one maintainer reviews code
3. **Security Review**: Security team reviews security-related changes
4. **Documentation Review**: Documentation is checked for completeness
5. **Testing Review**: Tests are reviewed for coverage and quality

### Review Criteria

- Code quality and style
- Test coverage and quality
- Documentation completeness
- Security considerations
- Performance implications
- Backward compatibility

### Addressing Feedback

- Respond to review comments promptly
- Make requested changes
- Re-run tests after changes
- Ask for clarification if needed

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Steps

1. **Prepare Release**
   - Update version numbers
   - Update CHANGELOG.md
   - Create release branch
   - Run full test suite

2. **Release Testing**
   - Deploy to staging environment
   - Run integration tests
   - Performance testing
   - Security testing

3. **Create Release**
   - Create GitHub release
   - Tag release version
   - Deploy to production
   - Update documentation

### Changelog Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-10-30

### Added
- New threat intelligence source integration (CIRCL Hash Lookup)
- Real-time threat monitoring via WebSocket
- Advanced anomaly detection with ML models
- Multi-tenant support for enterprise deployments

### Changed
- Improved API response times by 40%
- Updated database schema for better performance
- Enhanced security logging and audit trails

### Fixed
- Resolved memory leak in anomaly detection module
- Fixed race condition in threat intelligence collection
- Corrected rate limiting implementation

### Security
- Updated dependencies to patch CVE-2025-1234
- Implemented additional input validation
- Enhanced encryption for sensitive data storage

### Deprecated
- Legacy API endpoints (to be removed in v3.0)
- Old authentication method (migrate to JWT)

### Removed
- Deprecated threat intelligence sources
- Unused configuration options

### Performance
- Optimized database queries
- Improved caching strategy
- Reduced memory footprint
```

## Community

### Getting Help

- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and API reference
- **Security Issues**: Email security@yourorg.com

### Communication Channels

- **GitHub Discussions**: Main community forum
- **GitHub Issues**: Bug tracking and feature requests
- **Email**: support@yourorg.com
- **Security**: security@yourorg.com

### Recognition

We recognize contributors through:
- **Contributors.md**: List of all contributors
- **Release Notes**: Credit in release announcements
- **GitHub Contributors**: Automatic recognition
- **Special Mentions**: Outstanding contribution recognition

## Additional Resources

- [Architecture Documentation](docs/architecture/architecture-overview.md)
- [API Documentation](docs/api/openapi-specification.md)
- [Security Guidelines](SECURITY.md)
- [License](LICENSE)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

Thank you for contributing to the Cybersecurity Database System! Your involvement helps make the project better for everyone.