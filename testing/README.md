# Testing & Quality Assurance Framework

A comprehensive testing framework for the Cybersecurity Validation API, including unit tests, integration tests, load testing, and ML model validation.

## 🚀 Quick Start

### Installation

```bash
# Install testing dependencies
cd testing
pip install -r requirements.txt

# Generate test data
python generators/test_data_generator.py

# Run all tests
python run_tests.py --mode comprehensive
```

### Run Specific Test Types

```bash
# Unit tests with coverage
python run_tests.py --mode unit --generate-data

# Integration tests
python run_tests.py --mode integration

# Load testing
python run_tests.py --mode load --scenario moderate_load

# Coverage analysis only
python run_tests.py --mode coverage
```

## 📁 Directory Structure

```
testing/
├── conftest.py                 # Pytest configuration and fixtures
├── requirements.txt           # Testing dependencies
├── run_tests.py              # Main test runner
├── generators/               # Test data generators
│   └── test_data_generator.py
├── mocks/                    # Mock services for external APIs
│   └── external_apis.py
├── unit/                     # Unit tests
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_ml_models.py
├── integration/              # Integration tests
│   └── test_api_integration.py
├── load/                     # Load testing
│   ├── locustfile.py
│   ├── load_test_config.py
│   └── test_runner.py
├── coverage/                 # Coverage reporting
│   └── coverage_reporter.py
└── fixtures/                 # Test fixtures and data
    └── generated/            # Generated test data
```

## 🧪 Test Types

### Unit Tests

Test individual components in isolation:

- **API Endpoints**: Validation, reputation, threat intelligence, admin
- **Database Operations**: CRUD operations, caching, transactions
- **ML Models**: Anomaly detection, phishing classification, domain reputation

```bash
# Run unit tests with coverage
python -m pytest unit/ --cov=api --cov-report=html

# Run specific test class
python -m pytest unit/test_api_endpoints.py::TestValidationAPI -v
```

### Integration Tests

Test component interactions:

- **End-to-end workflows**: Complete validation pipelines
- **Database + Cache**: Combined database and Redis operations
- **External APIs**: Integration with threat intelligence sources
- **Error handling**: System recovery from failures

```bash
# Run integration tests
python -m pytest integration/ --run-integration -v
```

### Load Tests

Performance testing with Locust:

- **Smoke tests**: Quick validation of basic functionality
- **Light load**: Typical production traffic simulation
- **Heavy load**: Stress testing to find breaking points
- **Spike tests**: Sudden traffic increase handling
- **Endurance tests**: Long-running stability

```bash
# Run specific load test scenario
python load/test_runner.py moderate_load

# List available scenarios
python load/test_runner.py --list-scenarios

# Run with custom parameters
python load/test_runner.py heavy_load --host http://api.example.com
```

## 📊 Coverage Reporting

Comprehensive coverage analysis:

```bash
# Generate coverage report
python coverage/coverage_reporter.py --test-type unit --output-format all

# Generate badges
python coverage/coverage_reporter.py --generate-badges
```

### Coverage Targets

- **Overall Coverage**: ≥80%
- **Critical Functions**: ≥90%
- **API Endpoints**: ≥95%
- **Database Operations**: ≥85%
- **ML Models**: ≥75%

## 🔧 Configuration

### Test Configuration (`conftest.py`)

- Environment variables for test databases
- Mock services for external APIs
- Performance monitoring fixtures
- Test data generators

### Load Test Configuration (`load/load_test_config.py`)

- Predefined test scenarios
- Performance thresholds
- User behavior patterns

### Coverage Configuration

- Source paths to measure
- Component coverage targets
- Critical function identification

## 📈 Performance Metrics

### API Response Time Targets

| Endpoint Type | P50 | P95 | P99 | Max |
|---------------|-----|-----|-----|-----|
| Validation | 100ms | 500ms | 1s | 2s |
| Reputation | 500ms | 2s | 5s | 10s |
| Threat Intel | 1s | 5s | 10s | 20s |
| ML Models | 2s | 10s | 20s | 30s |

### Success Rate Targets

| Test Type | Target |
|-----------|--------|
| Unit Tests | 99.5% |
| Integration | 98% |
| Load Tests | 95% |

## 🛠️ Test Data Generation

### Generate Test Data

```bash
# Generate all test data
python generators/test_data_generator.py

# Generate specific types
python generators/test_data_generator.py --type validation reputation
```

### Test Data Types

- **Validation Data**: Valid/invalid emails, domains, IPs, URLs
- **Reputation Data**: Good/bad reputation indicators
- **Threat Intelligence**: Malware, botnet, phishing indicators
- **ML Training Data**: Normal/anomalous traffic patterns
- **Load Test Data**: Realistic user behavior patterns

## 🔍 Mock Services

### External API Mocks

- **AbuseIPDB**: IP reputation data
- **VirusTotal**: File and URL scanning
- **GreyNoise**: IP classification
- **OTX**: Threat intelligence

### Mock Response Generation

```python
from mocks.external_apis import MockThreatIntelligenceAPI

mock_api = MockThreatIntelligenceAPI()
result = await mock_api.query_ip_comprehensive("8.8.8.8")
```

## 📋 Test Categories

### Validation Tests

Test data validation and sanitization:

- Email format validation
- Domain validation (DNS, WHOIS)
- IP address validation (IPv4/IPv6)
- URL validation and analysis
- Bulk validation operations

### Reputation Tests

Test reputation scoring:

- Multi-source reputation aggregation
- Reputation score calculation
- Confidence interval validation
- Reputation trend analysis
- Bulk reputation queries

### Threat Intelligence Tests

Test threat detection:

- IOC extraction from text
- Threat actor attribution
- Campaign correlation
- Timeline analysis
- Contextual threat data

### ML Model Tests

Test machine learning components:

- Anomaly detection accuracy
- Phishing classification
- Domain reputation prediction
- Feature importance analysis
- Model performance metrics

## 🚨 Error Handling Tests

### Test Scenarios

- **Network timeouts**: External API failures
- **Database connection failures**: Connection pooling issues
- **Rate limiting**: Exceeding API quotas
- **Input validation**: Malformed data handling
- **Resource exhaustion**: Memory, CPU, disk space

### Recovery Testing

- **Circuit breaker patterns**: Service failure handling
- **Retry mechanisms**: Automatic retry logic
- **Fallback strategies**: Graceful degradation
- **Health checks**: Service monitoring

## 📊 Reporting

### Test Reports

- **HTML Reports**: Detailed test results with failure analysis
- **JSON Reports**: Machine-readable test results
- **Coverage Reports**: Line, branch, and function coverage
- **Performance Reports**: Response time and throughput metrics

### Continuous Integration

```yaml
# Example CI/CD pipeline
- name: Run Tests
  run: |
    cd testing
    python run_tests.py --mode comprehensive --no-coverage
    
- name: Load Tests
  run: |
    cd testing
    python load/test_runner.py moderate_load --host $API_URL
    
- name: Coverage Analysis
  run: |
    cd testing
    python coverage/coverage_reporter.py --generate-badges
```

## 🔒 Security Testing

### Input Validation

- SQL injection attempts
- XSS payload testing
- Path traversal attacks
- Command injection
- Buffer overflow testing

### Authentication & Authorization

- API key validation
- Rate limiting bypass attempts
- Privilege escalation testing
- Session management testing

## 🎯 Best Practices

### Writing Tests

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use specific, meaningful assertions
3. **Descriptive Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Mock External Dependencies**: Use mocks for external services

### Test Organization

```
test_class_name.py
├── TestFeatureName:
    ├── test_specific_functionality
    ├── test_edge_cases
    ├── test_error_handling
    └── test_performance
```

### Performance Testing

1. **Baseline Measurements**: Establish performance baselines
2. **Realistic Load**: Use realistic user behavior patterns
3. **Gradual Testing**: Start with light loads and increase
4. **Monitor Resources**: Track CPU, memory, and network usage
5. **Analyze Bottlenecks**: Identify performance bottlenecks

## 🚀 Advanced Usage

### Custom Test Scenarios

```python
# Create custom load test user
class CustomUser(HttpUser):
    @task(5)
    def custom_workload(self):
        # Your custom test logic
        pass
```

### Custom Mock Responses

```python
# Create custom mock response
custom_response = {
    "abuseipdb": {
        "abuseConfidenceScore": 95,
        "totalReports": 127
    }
}
```

### Performance Profiling

```bash
# Profile test execution
python -m pytest --profile unit/

# Memory profiling
python -m pytest --memray unit/
```

## 📚 Examples

### Unit Test Example

```python
@pytest.mark.unit
async def test_email_validation_valid(test_client, sample_test_data):
    response = await test_client.post(
        "/api/v1/validate/email",
        json={"email": sample_test_data["emails"]["valid"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["is_valid"] is True
```

### Integration Test Example

```python
@pytest.mark.integration
async def test_complete_workflow(authenticated_client):
    # Test complete validation workflow
    email_response = await authenticated_client.post(
        "/api/v1/validate/email",
        json={"email": "test@example.com"}
    )
    
    reputation_response = await authenticated_client.post(
        "/api/v1/reputation/query",
        json={"value": "8.8.8.8", "value_type": "ip"}
    )
    
    assert email_response.status_code == 200
    assert reputation_response.status_code == 200
```

### Load Test Example

```python
class ValidationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def validate_email(self):
        email = random.choice(test_data)
        self.client.post("/api/v1/validate/email", json={"email": email})
```

## 🤝 Contributing

### Adding New Tests

1. **Follow naming conventions**: `test_feature_scenario`
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
3. **Include docstrings**: Document what the test validates
4. **Add assertions**: Verify expected behavior
5. **Update coverage**: Ensure new code is covered

### Test Data

1. **Use factories**: Generate realistic test data
2. **Avoid hardcoding**: Use configuration or generators
3. **Include edge cases**: Test boundary conditions
4. **Validate generators**: Ensure data quality

## 📞 Support

For questions or issues with the testing framework:

1. Check the test logs for specific error messages
2. Verify test environment setup
3. Ensure all dependencies are installed
4. Review test configuration files
5. Check external service availability

---

**Happy Testing! 🧪✨**