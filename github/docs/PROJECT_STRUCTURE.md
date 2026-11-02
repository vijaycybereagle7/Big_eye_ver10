# Project Structure

This document describes the complete project structure for the Big Eye Security Database.

## Root Directory

```
big-eye-security-database/
├── .github/                     # GitHub-specific files
├── api/                         # FastAPI application
├── ai_ml/                       # AI/ML components
├── browser/                     # Browser automation and extension
├── code/                        # Code generation and automation scripts
├── database/                    # Database schemas and configurations
├── deployment/                  # Deployment configurations and scripts
├── docs/                        # Documentation
├── monitoring/                  # Monitoring and observability
├── performance/                 # Performance optimization
├── security/                    # Security module
├── testing/                     # Test suites
├── threat_intelligence/         # Threat intelligence collection
├── .gitignore                   # Git ignore patterns
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── CODEOWNERS                   # Code ownership and review rules
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # License file
├── README.md                    # Project documentation
├── SECURITY.md                  # Security policy
├── CODE_OF_CONDUCT.md           # Code of conduct
├── CHANGELOG.md                 # Version history
├── requirements.txt             # Main Python dependencies
├── setup.py                     # Setup configuration
├── pyproject.toml               # Python project configuration
├── docker-compose.yml           # Docker compose configuration
├── Dockerfile                   # Docker image definition
├── .env.example                 # Environment variables template
└── .fossaryya.yml               # FOSSASYA configuration
```

## Detailed Directory Structure

### `.github/` - GitHub Integration
```
.github/
├── workflows/
│   ├── ci.yml                   # Main CI/CD pipeline
│   ├── security.yml             # Security scanning workflow
│   └── dependency-updates.yml   # Dependency update automation
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml           # Bug report template
│   ├── feature_request.yml      # Feature request template
│   └── security_issue.yml       # Security issue template
├── PULL_REQUEST_TEMPLATE.md     # Pull request template
└── dependabot.yml               # Dependabot configuration
```

### `api/` - FastAPI Application
```
api/
├── app/                         # Main application module
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── config/                  # Configuration module
│   │   ├── __init__.py
│   │   └── settings.py          # Application settings
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── database.py          # Database models
│   │   └── schemas.py           # Pydantic schemas
│   ├── routers/                 # API routers
│   │   ├── __init__.py
│   │   ├── admin.py             # Administrative endpoints
│   │   ├── reputation.py        # Reputation endpoints
│   │   ├── threat_intelligence.py # Threat intel endpoints
│   │   └── validation.py        # Validation endpoints
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── reputation.py        # Reputation service
│   │   ├── threat_intelligence.py # Threat intel service
│   │   └── validation.py        # Validation service
│   ├── middleware/              # API middleware
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication middleware
│   │   └── rate_limit.py        # Rate limiting middleware
│   ├── database/                # Database connections
│   │   ├── __init__.py
│   │   └── connections.py       # Database connection management
│   ├── cache/                   # Caching layer
│   │   └── redis_cache.py       # Redis cache implementation
│   ├── utils/                   # Utility functions
│   │   └── helpers.py           # Helper functions
│   └── tests/                   # API tests
│       └── test_config.py       # Configuration tests
├── requirements.txt             # API dependencies
└── README.md                    # API documentation
```

### `ai_ml/` - Artificial Intelligence and Machine Learning
```
ai_ml/
├── anomaly_detection/           # Anomaly detection module
│   ├── __init__.py
│   ├── README.md
│   ├── example_usage.py         # Usage examples
│   ├── final_demo.py            # Demo script
│   ├── test_system.py           # System tests
│   ├── algorithms/              # Detection algorithms
│   ├── core/                    # Core detection logic
│   ├── use_cases/               # Use case implementations
│   └── utils/                   # Utility functions
├── nlp/                         # Natural Language Processing
│   ├── README.md
│   ├── config.py                # NLP configuration
│   ├── demo.py                  # Demo script
│   ├── nlp_processor.py         # Main NLP processor
│   ├── test_nlp.py              # NLP tests
│   ├── requirements.txt         # NLP dependencies
│   ├── data/                    # NLP training data
│   ├── models/                  # Trained NLP models
│   ├── tests/                   # NLP test suite
│   └── utils/                   # NLP utilities
└── pattern_recognition/         # Pattern recognition
    ├── README.md
    ├── __init__.py
    ├── demo.py                  # Demo script
    ├── feature_extraction.py    # Feature extraction
    ├── gradient_boosting_sender_reputation.py # Gradient boosting model
    ├── inference.py             # Inference engine
    ├── model_evaluation.py      # Model evaluation
    ├── random_forest_domain_reputation.py     # Random forest model
    ├── training_pipeline.py     # Training pipeline
    └── xgboost_phishing_detection.py # XGBoost phishing detection
```

### `browser/` - Browser Automation
```
browser/
├── global_browser.py            # Global browser controller
├── browser_extension/           # Browser extension
│   └── error_capture/           # Error capture functionality
└── extracted_content/           # Extracted content storage
    ├── *.json                   # Extracted content files
    └── screenshots/             # Screenshot captures
        ├── *.png                # Screenshot images
        └── screenshots metadata
```

### `code/` - Code Generation
```
code/
├── create_architecture_diagrams.py      # Architecture diagram generator
└── create_simplified_diagrams.py        # Simplified diagram generator
```

### `database/` - Database Schemas
```
database/
├── postgresql/                          # PostgreSQL configuration
│   ├── postgresql_schema.sql           # Main schema definition
│   ├── validate_schema.sql             # Schema validation
│   ├── IMPLEMENTATION_SUMMARY.md       # Implementation notes
│   └── README.md                       # PostgreSQL documentation
└── mongodb/                             # MongoDB configuration
    └── mongodb_collections.json        # Collection definitions
```

### `deployment/` - Deployment Configurations
```
deployment/
├── IMPLEMENTATION_SUMMARY.md            # Deployment summary
├── README.md                            # Deployment documentation
├── backup/                              # Backup configurations
│   ├── scripts/                         # Backup scripts
│   └── templates/                       # Backup templates
├── config/                              # Service configurations
│   ├── alertmanager/                    # AlertManager config
│   ├── grafana/                         # Grafana dashboards
│   ├── logstash/                        # Logstash configuration
│   ├── mongodb/                         # MongoDB config
│   ├── nginx/                           # Nginx configuration
│   ├── postgres/                        # PostgreSQL config
│   ├── prometheus/                      # Prometheus config
│   └── redis/                           # Redis configuration
├── docker/                              # Docker configurations
│   └── docker-compose.yml               # Main compose file
├── docs/                                # Deployment documentation
│   ├── aws-deployment-guide.md          # AWS deployment guide
│   ├── azure-deployment-guide.md        # Azure deployment guide
│   ├── comprehensive_disaster_recovery_plan.md # Disaster recovery
│   ├── disaster_recovery_plan.md        # Basic disaster recovery
│   ├── gcp-deployment-guide.md          # GCP deployment guide
│   └── production_deployment_guide.md   # Production deployment
├── kubernetes/                          # Kubernetes manifests
│   ├── helm/                            # Helm charts
│   ├── manifests/                       # K8s manifests
│   └── templates/                       # Deployment templates
└── scripts/                             # Deployment scripts
    ├── deploy.sh                        # Deployment script
    ├── setup.sh                         # Setup script
    ├── validate.sh                      # Validation script
    └── validate_infrastructure.py       # Infrastructure validation
```

### `docs/` - Documentation
```
docs/
├── README.md                            # Main documentation index
├── Screenshot_Inventory.md              # Screenshot documentation
├── VirusTotal_API_v3_Research_Report.md # API research report
├── database_architecture_analysis.md    # Database analysis
├── executive-summary.md                 # Executive summary
├── phishtank_api_research_report.md     # API research report
├── safe_browsing_api_v4_research_summary.md # API research
├── spamhaus_api_research_report.md      # API research report
├── system-overview.md                   # System overview
├── technical-specifications.md          # Technical specifications
├── ai_ml_integration/                   # AI/ML documentation
│   └── ai_ml_architecture.md            # AI/ML architecture
├── api/                                 # API documentation
│   └── openapi-specification.md         # OpenAPI specification
├── architecture/                        # Architecture documentation
│   └── architecture-overview.md         # Architecture overview
├── compliance/                          # Compliance documentation
│   └── compliance-documentation.md      # Compliance docs
├── configuration/                       # Configuration documentation
│   └── configuration-guide.md           # Configuration guide
├── database/                            # Database documentation
│   └── database-schema.md               # Database schema docs
├── database_analysis/                   # Database analysis
│   ├── architecture_overview.png        # Architecture diagram
│   ├── data_flow_architecture.png       # Data flow diagram
│   ├── technology_radar.png             # Technology radar
│   └── use_case_comparison.png          # Use case comparison
├── operations/                          # Operations documentation
│   └── operational-runbook.md           # Operational runbook
├── performance/                         # Performance documentation
│   └── performance-tuning-guide.md      # Performance tuning
├── security/                            # Security documentation
│   └── security-considerations.md       # Security considerations
├── setup/                               # Setup documentation
│   └── installation-guide.md            # Installation guide
├── threat_intelligence/                 # Threat intelligence docs
│   ├── research_plan_threat_intelligence_sources.md # Research plan
│   ├── threat_intelligence_sources.md   # Threat sources
│   └── threat_intelligence_sources_primary_sources.md # Primary sources
└── troubleshooting/                     # Troubleshooting guides
    └── troubleshooting-guide.md         # Troubleshooting guide
```

### `monitoring/` - Monitoring and Observability
```
monitoring/
├── IMPLEMENTATION_SUMMARY.md            # Monitoring implementation summary
├── QUICK_REFERENCE.md                   # Quick reference guide
├── README.md                            # Monitoring documentation
├── deploy.sh                            # Monitoring deployment script
├── docker-compose.yml                   # Monitoring compose file
├── alertmanager/                        # AlertManager configuration
│   └── alertmanager.yml                 # AlertManager config
├── configs/                             # Monitoring configurations
│   └── threat-feeds.yml                 # Threat feed monitoring
├── dashboards/                          # Grafana dashboards
├── elk/                                 # ELK Stack configuration
│   ├── elasticsearch/                   # Elasticsearch config
│   ├── filebeat/                        # Filebeat configuration
│   ├── kibana/                          # Kibana configuration
│   └── logstash/                        # Logstash configuration
├── exporter-configs/                    # Exporter configurations
│   ├── mongodb-exporter.env             # MongoDB exporter config
│   ├── postgres-exporter.env            # PostgreSQL exporter config
│   └── postgres-queries.yaml            # PostgreSQL queries
├── grafana/                             # Grafana configuration
│   ├── dashboards/                      # Grafana dashboards
│   └── datasources/                     # Grafana datasources
├── prometheus/                          # Prometheus configuration
│   ├── prometheus.yml                   # Prometheus config
│   └── rules.yml                        # Prometheus rules
└── scripts/                             # Monitoring scripts
    ├── health_check.py                  # Health check script
    ├── metrics_collector.py             # Metrics collection
    ├── security_monitor.py              # Security monitoring
    ├── threat_intel_monitor.py          # Threat intel monitoring
    └── update_metrics.sh                # Metrics update script
```

### `performance/` - Performance Optimization
```
performance/
├── IMPLEMENTATION_REPORT.md             # Performance implementation report
├── README.md                            # Performance documentation
├── implementation_summary.py            # Implementation summary script
├── caching/                             # Caching optimizations
│   └── query_optimization.sql           # Query optimization
├── config/                              # Performance configuration
│   └── performance_config.yaml          # Performance config
├── database/                            # Database performance
│   └── indexing_strategy.sql            # Indexing strategy
├── monitoring/                          # Performance monitoring
│   └── performance_monitor.py           # Performance monitoring
├── partitioning/                        # Database partitioning
│   └── postgresql_partitioning.sql      # PostgreSQL partitioning
├── redis/                               # Redis optimizations
│   ├── redis_caching.sql                # Redis caching implementation
│   └── redis_caching_implementation.py  # Redis implementation
├── replicas/                            # Database replicas
│   └── read_replicas_setup.sql          # Read replicas setup
└── views/                               # Database views
    └── materialized_views.sql           # Materialized views
```

### `security/` - Security Module
```
security/
├── IMPLEMENTATION_SUMMARY.md            # Security implementation summary
├── OVERVIEW.md                          # Security overview
├── TASK_COMPLETION_REPORT.md            # Task completion report
├── requirements.txt                     # Security dependencies
├── access_control/                      # Access control module
│   ├── __init__.py
│   └── access_control.db                # Access control database
├── compliance/                          # Compliance module
│   ├── __init__.py
│   └── gdpr.db                          # GDPR compliance database
├── configs/                             # Security configurations
│   ├── access_control_config.json       # Access control config
│   ├── compliance_config.json           # Compliance config
│   ├── encryption_config.json           # Encryption config
│   └── infrastructure_config.json       # Infrastructure config
├── docs/                                # Security documentation
│   ├── README.md                        # Security docs index
│   ├── demo_summary_report.json         # Demo summary report
│   ├── gdpr_policy.md                   # GDPR policy
│   └── infosec_policy.md                # InfoSec policy
├── encryption/                          # Encryption module
│   ├── __init__.py
│   ├── encryption_at_rest.py            # Encryption at rest
│   ├── encryption_in_transit.py         # Encryption in transit
│   └── pii_protection.py                # PII protection
├── infrastructure/                      # Infrastructure security
│   ├── __init__.py
│   ├── firewall.db                      # Firewall rules database
│   └── ids.db                           # IDS rules database
├── logs/                                # Security logs directory
└── scripts/                             # Security scripts
    ├── compliance_reporter.py           # Compliance reporting
    ├── demo.py                          # Security demo
    ├── security_manager.py              # Security management
    └── security_monitor.py              # Security monitoring
```

### `testing/` - Test Suite
```
testing/
├── IMPLEMENTATION_SUMMARY.md            # Testing implementation summary
├── README.md                            # Testing documentation
├── conftest.py                          # Pytest configuration
├── pytest.ini                          # Pytest settings
├── requirements.txt                     # Testing dependencies
├── run_tests.py                         # Test runner
├── setup.py                             # Test setup
├── coverage/                            # Coverage reporting
│   └── coverage_reporter.py             # Coverage reporting
├── fixtures/                            # Test fixtures
│   └── sample_validation_cases.py       # Sample validation cases
├── generators/                          # Test data generators
│   └── test_data_generator.py           # Test data generation
├── integration/                         # Integration tests
│   └── test_api_integration.py          # API integration tests
├── load/                                # Load testing
│   ├── load_test_config.py              # Load test configuration
│   ├── locustfile.py                    # Locust load test file
│   └── test_runner.py                   # Load test runner
├── mocks/                               # Mock objects and utilities
│   └── external_apis.py                 # External API mocks
└── unit/                                # Unit tests
    ├── test_api_endpoints.py            # API endpoint tests
    ├── test_database_operations.py      # Database operation tests
    └── test_ml_models.py                # ML model tests
```

### `threat_intelligence/` - Threat Intelligence Collection
```
threat_intelligence/
└── collection/                          # Threat intelligence collection
    ├── PROJECT_SUMMARY.md               # Project summary
    ├── README.md                        # Collection documentation
    ├── base_collector.py                # Base collector class
    ├── threat_intel_manager.py          # Threat intelligence manager
    ├── requirements.txt                 # Collection dependencies
    ├── threat_intel_config.json.template # Configuration template
    ├── abuseipdb_collector.py           # AbuseIPDB collector
    ├── circl_hashlookup_collector.py    # CIRCL Hash Lookup collector
    ├── greynoise_collector.py           # GreyNoise collector
    ├── malwarebazaar_collector.py       # MalwareBazaar collector
    ├── otx_collector.py                 # OTX collector
    ├── phishtank_collector.py           # PhishTank collector
    ├── safebrowsing_collector.py        # Safe Browsing collector
    ├── securitytrails_collector.py      # SecurityTrails collector
    ├── shodan_collector.py              # Shodan collector
    ├── spamhaus_collector.py            # Spamhaus collector
    ├── threatfox_collector.py           # ThreatFox collector
    ├── urlhaus_collector.py             # URLhaus collector
    ├── virustotal_collector.py          # VirusTotal collector
    ├── examples.py                      # Usage examples
    └── PROJECT_SUMMARY.md               # Project summary
```

## File Descriptions

### Configuration Files

- `.gitignore`: Patterns for files to ignore in Git
- `.pre-commit-config.yaml`: Pre-commit hooks for code quality
- `CODEOWNERS`: Code ownership and review requirements
- `requirements.txt`: Main Python dependencies
- `setup.py`: Python package setup configuration
- `pyproject.toml`: Modern Python project configuration
- `docker-compose.yml`: Docker services orchestration
- `Dockerfile`: Docker image definition
- `.env.example`: Environment variables template
- `.fossaryya.yml`: FOSSASYA security scanning configuration

### Documentation Files

- `README.md`: Main project documentation
- `CONTRIBUTING.md`: Contribution guidelines
- `LICENSE`: License file
- `SECURITY.md`: Security policy
- `CODE_OF_CONDUCT.md`: Community code of conduct
- `CHANGELOG.md`: Version history and changes

### Scripts

- `setup.sh`: Unix/Linux setup script
- `setup.bat`: Windows setup script

## Architecture Patterns

### Microservices Architecture
The system follows a microservices architecture with the following patterns:

1. **API Layer**: FastAPI-based REST API with routing
2. **Service Layer**: Business logic services
3. **Data Layer**: Multiple database technologies (PostgreSQL, MongoDB, Redis)
4. **External Integrations**: Threat intelligence source collectors
5. **AI/ML Pipeline**: Machine learning and NLP processing
6. **Security Layer**: Authentication, authorization, and encryption

### Database Strategy
- **PostgreSQL**: Structured data and complex queries
- **MongoDB**: Document storage and flexible schemas
- **Redis**: Caching and real-time operations
- **Elasticsearch**: Log storage and search

### Deployment Strategy
- **Containerization**: Docker for consistent deployments
- **Orchestration**: Kubernetes for production scaling
- **CI/CD**: GitHub Actions for automated pipelines
- **Monitoring**: Comprehensive observability stack

### Security Strategy
- **Defense in Depth**: Multiple layers of security
- **Zero Trust**: Verify everything, trust nothing
- **Encryption**: Data protection at rest and in transit
- **Compliance**: GDPR, SOC2, and other regulatory compliance

## Development Workflow

1. **Feature Development**: Create feature branch, implement changes
2. **Testing**: Run unit, integration, and security tests
3. **Code Review**: Peer review with CODEOWNERS approval
4. **CI/CD**: Automated testing and deployment
5. **Monitoring**: Continuous monitoring and alerting

## Scaling Considerations

- **Horizontal Scaling**: Stateless services can scale independently
- **Database Scaling**: Read replicas and sharding strategies
- **Caching**: Multi-level caching with Redis
- **Load Balancing**: Distribute traffic across service instances
- **Resource Management**: Efficient resource utilization and allocation
