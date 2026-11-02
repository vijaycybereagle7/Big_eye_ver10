# OpenAPI Specification
## Cybersecurity Threat Intelligence Platform API

---

## 📋 API Overview

### API Information
```yaml
openapi: 3.0.3
info:
  title: Cybersecurity Threat Intelligence Platform API
  description: |
    Comprehensive cybersecurity validation and threat intelligence API providing email, domain, IP, URL, and sender validation with integrated threat intelligence and reputation analysis.
    
    ## Features
    - **Multi-type Validation**: Email, domain, IP, URL, and sender validation
    - **Threat Intelligence**: Multi-source threat intelligence aggregation
    - **Reputation Scoring**: Weighted confidence scoring and risk assessment
    - **Bulk Processing**: High-volume batch processing capabilities
    - **Real-time Processing**: Low-latency validation and threat analysis
    
    ## Authentication
    All endpoints require authentication using API keys:
    - Header: `X-API-Key: your-api-key`
    - Bearer: `Authorization: Bearer your-api-key`
    
    ## Rate Limiting
    - Standard endpoints: 100 requests per minute
    - Admin endpoints: 1000 requests per minute
    - Bulk operations: 10 requests per minute
    
    ## Response Format
    All responses follow a consistent format:
    ```json
    {
      "success": true|false,
      "message": "Human-readable message",
      "result": { ... },  // Response data
      "timestamp": "ISO 8601 timestamp"
    }
    ```
    
    ## Error Handling
    Error responses include detailed information:
    ```json
    {
      "success": false,
      "message": "Error description",
      "error": {
        "error_code": "ERROR_CODE",
        "error_message": "Detailed error message",
        "details": { ... }
      },
      "timestamp": "ISO 8601 timestamp"
    }
    ```
  version: "1.0.0"
  contact:
    name: API Support
    email: api-support@cybersecurity-platform.example.com
    url: https://docs.cybersecurity-platform.example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
  termsOfService: https://cybersecurity-platform.example.com/terms

servers:
  - url: https://api.cybersecurity-platform.example.com/v1
    description: Production server
  - url: https://staging-api.cybersecurity-platform.example.com/v1
    description: Staging server
  - url: http://localhost:8000/v1
    description: Development server

security:
  - ApiKeyAuth: []
  - BearerAuth: []

paths:
  # Validation Endpoints
  /validate/email:
    post:
      tags:
        - Validation
      summary: Email validation
      description: |
        Validate email addresses including syntax, MX records, disposable detection, and reputation analysis.
        
        ### Validation Steps
        1. **Syntax Validation**: Check email format compliance
        2. **Domain Verification**: Verify domain existence and MX records
        3. **Disposable Check**: Detect disposable email services
        4. **Reputation Analysis**: Check against multiple threat intelligence sources
        5. **Role Account Detection**: Identify distribution lists and role accounts
        
        ### Response Includes
        - Validity status and confidence score
        - Domain information and MX records
        - Disposable service detection
        - Reputation score (0-100)
        - Threat indicators if detected
        - Validation suggestions
      operationId: validateEmail
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EmailValidationRequest'
            examples:
              basic_validation:
                summary: Basic email validation
                value:
                  email: "user@example.com"
              comprehensive_validation:
                summary: Comprehensive validation with threat intelligence
                value:
                  email: "suspicious@malicious-domain.com"
                  verify_syntax: true
                  verify_mx_record: true
                  check_disposable: true
                  check_reputation: true
                  check_threats: true
      responses:
        '200':
          description: Email validation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EmailValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
    
  /validate/domain:
    post:
      tags:
        - Validation
      summary: Domain validation
      description: |
        Validate domain names including DNS resolution, WHOIS data, parked domain detection, and reputation analysis.
        
        ### Validation Steps
        1. **Format Validation**: Check domain name format
        2. **DNS Resolution**: Verify A, AAAA, MX records
        3. **WHOIS Analysis**: Extract registration information
        4. **Parked Domain Detection**: Identify parked or for-sale domains
        5. **Reputation Scoring**: Analyze domain reputation
        6. **Security Analysis**: Check for security issues
      operationId: validateDomain
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DomainValidationRequest'
      responses:
        '200':
          description: Domain validation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DomainValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /validate/ip:
    post:
      tags:
        - Validation
      summary: IP address validation
      description: |
        Validate IP addresses including format verification, geolocation, proxy/VPN detection, and reputation analysis.
        
        ### Validation Steps
        1. **Format Validation**: Check IPv4/IPv6 format
        2. **Type Classification**: Identify public/private/reserved IPs
        3. **Geolocation**: Determine geographic location and ISP
        4. **Reputation Analysis**: Check against threat intelligence databases
        5. **Blacklist Check**: Verify against spam and malware blacklists
        6. **Security Analysis**: Detect proxies, VPNs, and Tor nodes
      operationId: validateIP
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IPValidationRequest'
      responses:
        '200':
          description: IP validation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/IPValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /validate/url:
    post:
      tags:
        - Validation
      summary: URL validation
      description: |
        Validate URLs including accessibility checks, safety analysis, reputation scoring, and threat intelligence.
        
        ### Validation Steps
        1. **Format Validation**: Check URL format and encoding
        2. **Accessibility Check**: Verify URL is reachable
        3. **Content Analysis**: Analyze web page content for threats
        4. **Reputation Analysis**: Check URL reputation across sources
        5. **Threat Detection**: Identify malicious URLs
        6. **Redirect Analysis**: Track redirects and final destination
      operationId: validateURL
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/URLValidationRequest'
      responses:
        '200':
          description: URL validation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/URLValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /validate/sender:
    post:
      tags:
        - Validation
      summary: Email sender validation
      description: |
        Validate email senders including SPF, DKIM, and DMARC authentication checks with comprehensive security analysis.
        
        ### Validation Steps
        1. **SPF Check**: Verify Sender Policy Framework records
        2. **DKIM Verification**: Check DomainKeys Identified Mail signatures
        3. **DMARC Analysis**: Verify Domain-based Message Authentication
        4. **Email Content Analysis**: Scan email content for threats
        5. **Attachment Analysis**: Check email attachments for malware
        6. **Sender Reputation**: Analyze sender reputation and history
      operationId: validateSender
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SenderValidationRequest'
      responses:
        '200':
          description: Sender validation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SenderValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /validate/bulk:
    post:
      tags:
        - Validation
      - Bulk Processing
      summary: Bulk validation
      description: |
        Process multiple validation requests concurrently for high-volume operations.
        
        ### Features
        - Process up to 1000 items per request
        - Multiple validation types in single request
        - Asynchronous processing with job tracking
        - Progress monitoring and status updates
        - Error handling with detailed reporting
        
        ### Processing Flow
        1. Submit bulk validation job
        2. Receive job ID for tracking
        3. Monitor processing status
        4. Retrieve results when completed
        
        ### Rate Limiting
        - Maximum 10 bulk requests per minute
        - Processing rate: 100 items per second
        - Job retention: 30 days
      operationId: bulkValidation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BulkValidationRequest'
            examples:
              mixed_validation:
                summary: Mixed validation types
                value:
                  emails:
                    - "user1@example.com"
                    - "user2@example.com"
                  domains:
                    - "example.com"
                    - "malicious-site.com"
                  ip_addresses:
                    - "8.8.8.8"
                    - "192.168.1.1"
                  options:
                    check_reputation: true
                    check_threats: true
                    max_concurrent: 10
      responses:
        '202':
          description: Bulk validation job accepted for processing
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkValidationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /validate/bulk/{job_id}:
    get:
      tags:
        - Validation
        - Bulk Processing
      summary: Get bulk validation status
      description: |
        Retrieve the status and results of a bulk validation job.
        
        ### Response Includes
        - Job status (pending, processing, completed, failed)
        - Progress percentage
        - Results for completed items
        - Error details for failed items
        - Job metadata and timing information
      operationId: getBulkValidationStatus
      parameters:
        - name: job_id
          in: path
          required: true
          description: Unique job identifier
          schema:
            type: string
            format: uuid
            example: "550e8400-e29b-41d4-a716-446655440000"
      responses:
        '200':
          description: Bulk validation status retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkValidationStatusResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  # Threat Intelligence Endpoints
  /threats/query:
    post:
      tags:
        - Threat Intelligence
      summary: Query threat intelligence
      description: |
        Query threat intelligence databases for indicators of compromise and threat information.
        
        ### Query Capabilities
        - Multi-source threat intelligence aggregation
        - Historical threat data and trends
        - Context and relationship analysis
        - Threat categorization and severity scoring
        - Real-time and cached results
        
        ### Supported Query Types
        - **IP Addresses**: Reputation, geolocation, threat history
        - **Domains**: WHOIS, DNS, reputation, threat indicators
        - **URLs**: Safety analysis, threat detection, reputation
        - **File Hashes**: Malware analysis, threat classification
        - **Email Addresses**: Phishing, spam, malicious activity
      operationId: queryThreatIntelligence
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ThreatIntelligenceQueryRequest'
      responses:
        '200':
          description: Threat intelligence query completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ThreatIntelligenceResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /threats/search:
    post:
      tags:
        - Threat Intelligence
      summary: Search threat indicators
      description: |
        Search threat intelligence database for indicators matching specific criteria.
        
        ### Search Features
        - Full-text search across threat indicators
        - Filter by indicator types, time ranges, confidence scores
        - Paginated results with configurable page sizes
        - Sort by relevance, date, confidence, or severity
        
        ### Use Cases
        - Hunt for specific threat patterns
        - Analyze threat trends over time
        - Find related indicators and relationships
        - Generate threat intelligence reports
      operationId: searchThreatIndicators
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ThreatSearchRequest'
      responses:
        '200':
          description: Threat indicator search completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ThreatSearchResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /threats/feeds:
    get:
      tags:
        - Threat Intelligence
      summary: Get threat feed status
      description: |
        Retrieve the status and health of external threat intelligence feeds.
        
        ### Information Provided
        - Feed availability and health status
        - Last successful data collection
        - API quota usage and limits
        - Data quality metrics
        - Feed configuration details
      operationId: getThreatFeedStatus
      responses:
        '200':
          description: Threat feed status retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ThreatFeedStatusResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalError'

  # Reputation Endpoints
  /reputation/query:
    post:
      tags:
        - Reputation
      summary: Query reputation
      description: |
        Query reputation data for IPs, domains, emails, and URLs from multiple sources.
        
        ### Reputation Sources
        - VirusTotal, AbuseIPDB, Shodan, GreyNoise
        - SecurityTrails, OTX, and other providers
        - Weighted confidence scoring algorithm
        - Historical reputation trends
        
        ### Output Includes
        - Overall reputation score (0-100)
        - Category-specific scores
        - Source-specific scores and confidence
        - Reputation history and trends
        - Risk assessment and recommendations
      operationId: queryReputation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReputationQueryRequest'
      responses:
        '200':
          description: Reputation query completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReputationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /reputation/batch:
    post:
      tags:
        - Reputation
        - Bulk Processing
      summary: Batch reputation queries
      description: |
        Query reputation for multiple entities in a single request for efficiency.
        
        ### Batch Features
        - Process up to 100 entities per request
        - Multiple entity types in single request
        - Optimized for high-volume operations
        - Cached results for improved performance
        
        ### Supported Entities
        - IP addresses
        - Domain names
        - Email addresses
        - URLs
        - File hashes
      operationId: batchReputationQuery
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReputationBatchRequest'
      responses:
        '200':
          description: Batch reputation query completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReputationBatchResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'

  # Admin Endpoints
  /admin/dashboard:
    get:
      tags:
        - Administration
      summary: Get dashboard statistics
      description: |
        Retrieve comprehensive dashboard statistics and system health metrics.
        
        ### Metrics Provided
        - System performance metrics
        - API usage statistics
        - Database performance
        - Cache hit rates
        - Error rates and trends
        - Active user statistics
        - Threat intelligence metrics
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: getDashboard
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: Dashboard statistics retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DashboardResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /admin/api-keys:
    get:
      tags:
        - Administration
      summary: List API keys
      description: |
        Retrieve a list of all API keys with their metadata and usage statistics.
        
        ### Information Included
        - Key ID and name
        - User association
        - Permissions and rate limits
        - Usage statistics
        - Creation and expiration dates
        - Status (active/inactive)
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: listAPIKeys
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: API keys list retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/APIKeyListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    
    post:
      tags:
        - Administration
      summary: Create API key
      description: |
        Create a new API key with specified permissions and rate limits.
        
        ### Features
        - Configurable rate limits
        - Admin/non-admin permissions
        - Expiration date setting
        - Custom key names and descriptions
        - Automatic key generation
        
        ### Security
        - Keys are hashed before storage
        - Regeneration capabilities
        - Usage tracking and monitoring
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: createAPIKey
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAPIKeyRequest'
      responses:
        '201':
          description: API key created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateAPIKeyResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /admin/api-keys/{key_id}:
    get:
      tags:
        - Administration
      summary: Get API key details
      description: |
        Retrieve detailed information about a specific API key including usage statistics and configuration.
      operationId: getAPIKeyDetails
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      parameters:
        - name: key_id
          in: path
          required: true
          description: API key identifier
          schema:
            type: string
      responses:
        '200':
          description: API key details retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/APIKeyDetailsResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
    
    patch:
      tags:
        - Administration
      summary: Update API key
      description: |
        Update API key configuration including rate limits, permissions, and status.
      operationId: updateAPIKey
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      parameters:
        - name: key_id
          in: path
          required: true
          description: API key identifier
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateAPIKeyRequest'
      responses:
        '200':
          description: API key updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UpdateAPIKeyResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
    
    delete:
      tags:
        - Administration
      summary: Delete API key
      description: |
        Permanently delete an API key. This action cannot be undone.
        
        ### Considerations
        - All associated usage data is removed
        - Any active sessions using this key will be invalidated
        - Audit log entry is created
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: deleteAPIKey
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      parameters:
        - name: key_id
          in: path
          required: true
          description: API key identifier
          schema:
            type: string
      responses:
        '204':
          description: API key deleted successfully
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /admin/health:
    get:
      tags:
        - Administration
      summary: System health check
      description: |
        Perform comprehensive system health check including all services, databases, and external dependencies.
        
        ### Health Check Components
        - Database connectivity and performance
        - Cache system status
        - External API availability
        - System resource utilization
        - Service dependencies
        
        ### Response Includes
        - Overall system status
        - Component health details
        - Performance metrics
        - Recommendations for issues
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: getSystemHealth
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: System health check completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemHealthResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
  
  /admin/stats:
    get:
      tags:
        - Administration
      summary: System statistics
      description: |
        Retrieve comprehensive system statistics and performance metrics.
        
        ### Statistics Provided
        - API request rates and trends
        - Database performance metrics
        - Cache performance statistics
        - User activity metrics
        - Error rates and analysis
        - Threat intelligence statistics
        - System resource usage
        
        ### Time Ranges
        - Last hour, day, week, month
        - Custom time range support
        - Historical trend data
        
        ### Requires
        - Admin API key
        - Appropriate permissions
      operationId: getSystemStats
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
      parameters:
        - name: time_range
          in: query
          description: Time range for statistics
          schema:
            type: string
            enum: [hour, day, week, month]
            default: day
        - name: start_date
          in: query
          description: Start date for custom range (ISO 8601)
          schema:
            type: string
            format: date-time
        - name: end_date
          in: query
          description: End date for custom range (ISO 8601)
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: System statistics retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemStatsResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  # Health Check Endpoints
  /health:
    get:
      tags:
        - System
      summary: Basic health check
      description: |
        Basic health check endpoint for monitoring and load balancer checks.
        
        ### Response
        - Service status (healthy/unhealthy)
        - Timestamp
        - Service version
        - Basic uptime information
        
        ### Usage
        - Load balancer health checks
        - Monitoring system checks
        - Basic availability verification
        
        ### No Authentication Required
        This endpoint does not require API key authentication.
      operationId: getBasicHealth
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BasicHealthResponse'
        '503':
          description: Service is unhealthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BasicHealthResponse'

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: |
        API key authentication header. Get your API key from the admin dashboard.
        
        Example: `X-API-Key: cybersec_key_20251030_143022_a1b2c3d4e5f6...`
    
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT bearer token authentication. Use for OAuth 2.0 flows.
        
        Example: `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

  schemas:
    # Request Schemas
    EmailValidationRequest:
      type: object
      required:
        - email
      properties:
        email:
          type: string
          format: email
          description: Email address to validate
          example: "user@example.com"
        verify_syntax:
          type: boolean
          default: true
          description: Perform syntax validation
        verify_mx_record:
          type: boolean
          default: true
          description: Verify MX records exist for domain
        check_disposable:
          type: boolean
          default: true
          description: Check if email is from disposable service
        check_reputation:
          type: boolean
          default: true
          description: Check email reputation against threat intelligence
        check_threats:
          type: boolean
          default: true
          description: Perform threat intelligence check
        verify_deliverability:
          type: boolean
          default: false
          description: Verify email deliverability (more intensive)
      additionalProperties: false
    
    DomainValidationRequest:
      type: object
      required:
        - domain
      properties:
        domain:
          type: string
          description: Domain name to validate
          example: "example.com"
          pattern: "^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
        check_dns:
          type: boolean
          default: true
          description: Verify DNS resolution
        check_whois:
          type: boolean
          default: false
          description: Retrieve and analyze WHOIS data
        check_reputation:
          type: boolean
          default: true
          description: Check domain reputation
        check_security:
          type: boolean
          default: true
          description: Perform security analysis
        check_parking:
          type: boolean
          default: true
          description: Detect parked domains
      additionalProperties: false
    
    IPValidationRequest:
      type: object
      required:
        - ip_address
      properties:
        ip_address:
          type: string
          description: IP address to validate
          example: "8.8.8.8"
          pattern: "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        check_reputation:
          type: boolean
          default: true
          description: Check IP reputation
        check_geolocation:
          type: boolean
          default: true
          description: Determine geolocation information
        check_blacklists:
          type: boolean
          default: true
          description: Check against spam and malware blacklists
        check_proxy:
          type: boolean
          default: true
          description: Detect proxies, VPNs, and Tor nodes
      additionalProperties: false
    
    URLValidationRequest:
      type: object
      required:
        - url
      properties:
        url:
          type: string
          format: uri
          description: URL to validate
          example: "https://example.com/page"
        check_safety:
          type: boolean
          default: true
          description: Check URL safety and accessibility
        check_reputation:
          type: boolean
          default: true
          description: Check URL reputation
        check_threats:
          type: boolean
          default: true
          description: Perform threat intelligence check
        follow_redirects:
          type: boolean
          default: true
          description: Follow redirects to final destination
        max_redirects:
          type: integer
          default: 5
          minimum: 1
          maximum: 10
          description: Maximum number of redirects to follow
        timeout:
          type: integer
          default: 30
          minimum: 5
          maximum: 120
          description: Request timeout in seconds
      additionalProperties: false
    
    SenderValidationRequest:
      type: object
      required:
        - email
      properties:
        email:
          type: string
          format: email
          description: Sender email address
          example: "sender@example.com"
        domain:
          type: string
          description: Sender domain (optional, derived from email if not provided)
          example: "example.com"
        check_spf:
          type: boolean
          default: true
          description: Verify SPF (Sender Policy Framework)
        check_dkim:
          type: boolean
          default: true
          description: Verify DKIM (DomainKeys Identified Mail)
        check_dmarc:
          type: boolean
          default: true
          description: Check DMARC (Domain-based Message Authentication)
        analyze_content:
          type: boolean
          default: false
          description: Analyze email content for threats
        check_attachments:
          type: boolean
          default: false
          description: Analyze email attachments for malware
      additionalProperties: false
    
    BulkValidationRequest:
      type: object
      properties:
        emails:
          type: array
          items:
            type: string
            format: email
          maxItems: 1000
          description: List of email addresses to validate
        domains:
          type: array
          items:
            type: string
          maxItems: 1000
          description: List of domains to validate
        ip_addresses:
          type: array
          items:
            type: string
          maxItems: 1000
          description: List of IP addresses to validate
        urls:
          type: array
          items:
            type: string
            format: uri
          maxItems: 1000
          description: List of URLs to validate
        options:
          type: object
          properties:
            check_reputation:
              type: boolean
              default: true
            check_threats:
              type: boolean
              default: true
            max_concurrent:
              type: integer
              default: 10
              minimum: 1
              maximum: 50
            timeout:
              type: integer
              default: 30
              minimum: 10
              maximum: 300
          additionalProperties: false
      additionalProperties: false
    
    ThreatIntelligenceQueryRequest:
      type: object
      required:
        - value
        - query_type
      properties:
        value:
          type: string
          description: Value to query (IP, domain, URL, hash, etc.)
          example: "8.8.8.8"
        query_type:
          type: string
          enum: [ip, domain, url, hash, email]
          description: Type of value being queried
        include_context:
          type: boolean
          default: true
          description: Include context and related information
        include_related:
          type: boolean
          default: false
          description: Include related indicators and correlations
        time_range_days:
          type: integer
          default: 30
          minimum: 1
          maximum: 365
          description: Time range for historical data in days
        sources:
          type: array
          items:
            type: string
            enum: [virustotal, abuseipdb, shodan, greynoise, otx, securitytrails]
          description: Specific sources to query (all if not specified)
      additionalProperties: false
    
    ThreatSearchRequest:
      type: object
      required:
        - query
      properties:
        query:
          type: string
          description: Search query string
          example: "malware ransomware"
        filters:
          type: object
          properties:
            indicator_types:
              type: array
              items:
                type: string
                enum: [ip, domain, url, hash, email]
            time_range_days:
              type: integer
              minimum: 1
              maximum: 365
            min_confidence:
              type: number
              minimum: 0
              maximum: 1
            categories:
              type: array
              items:
                type: string
            sources:
              type: array
              items:
                type: string
          additionalProperties: false
        page:
          type: integer
          default: 1
          minimum: 1
          description: Page number for pagination
        page_size:
          type: integer
          default: 20
          minimum: 1
          maximum: 100
          description: Number of results per page
        sort_by:
          type: string
          enum: [relevance, date, confidence, severity]
          default: relevance
          description: Sort results by specified field
        sort_order:
          type: string
          enum: [asc, desc]
          default: desc
          description: Sort order (ascending or descending)
      additionalProperties: false
    
    ReputationQueryRequest:
      type: object
      required:
        - value
        - value_type
      properties:
        value:
          type: string
          description: Value to check reputation for
          example: "8.8.8.8"
        value_type:
          type: string
          enum: [ip, domain, email, url, hash]
          description: Type of value
        sources:
          type: array
          items:
            type: string
          description: Specific reputation sources to query
        detailed:
          type: boolean
          default: true
          description: Include detailed source information
        include_history:
          type: boolean
          default: false
          description: Include historical reputation data
      additionalProperties: false
    
    ReputationBatchRequest:
      type: array
      items:
        type: object
        required:
          - value
          - value_type
        properties:
          value:
            type: string
          value_type:
            type: string
            enum: [ip, domain, email, url, hash]
        additionalProperties: false
      maxItems: 100
    
    CreateAPIKeyRequest:
      type: object
      required:
        - name
        - is_admin
        - rate_limit
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
          description: Human-readable name for the API key
          example: "Production Service Account"
        is_admin:
          type: boolean
          description: Whether this key has admin privileges
          default: false
        rate_limit:
          type: integer
          minimum: 1
          maximum: 10000
          description: Rate limit per minute
          example: 1000
        rate_window:
          type: integer
          minimum: 60
          maximum: 3600
          description: Rate limit window in seconds
          default: 60
        expires_at:
          type: string
          format: date-time
          description: Expiration date for the key
        description:
          type: string
          maxLength: 500
          description: Description of the key's purpose
      additionalProperties: false
    
    UpdateAPIKeyRequest:
      type: object
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        is_admin:
          type: boolean
        rate_limit:
          type: integer
          minimum: 1
          maximum: 10000
        rate_window:
          type: integer
          minimum: 60
          maximum: 3600
        is_active:
          type: boolean
        expires_at:
          type: string
          format: date-time
        description:
          type: string
          maxLength: 500
      additionalProperties: false

  responses:
    BadRequest:
      description: Bad request - invalid parameters
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Validation failed"
            error:
              error_code: "VALIDATION_ERROR"
              error_message: "Invalid email format"
              details:
                field: "email"
                value: "invalid-email"
                reason: "Does not match email pattern"
            timestamp: "2025-10-30T10:00:00Z"
    
    Unauthorized:
      description: Unauthorized - invalid or missing API key
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Authentication required"
            error:
              error_code: "HTTP_401"
              error_message: "Valid API key required"
            timestamp: "2025-10-30T10:00:00Z"
    
    Forbidden:
      description: Forbidden - insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Insufficient permissions"
            error:
              error_code: "HTTP_403"
              error_message: "Admin privileges required"
            timestamp: "2025-10-30T10:00:00Z"
    
    NotFound:
      description: Not found - resource does not exist
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Resource not found"
            error:
              error_code: "HTTP_404"
              error_message: "API key not found"
            timestamp: "2025-10-30T10:00:00Z"
    
    RateLimited:
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Rate limit exceeded"
            error:
              error_code: "HTTP_429"
              error_message: "Rate limit exceeded. Try again later"
              details:
                limit: 100
                window: 60
                reset_time: "2025-10-30T10:01:00Z"
            timestamp: "2025-10-30T10:00:00Z"
    
    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            success: false
            message: "Internal server error"
            error:
              error_code: "INTERNAL_ERROR"
              error_message: "An unexpected error occurred"
            timestamp: "2025-10-30T10:00:00Z"

  examples:
    # Common examples
    successful_validation:
      summary: Successful validation example
      value:
        success: true
        message: "Email validation completed"
        result:
          value: "user@example.com"
          is_valid: true
          confidence_score: 0.95
          domain_exists: true
          mx_record_exists: true
          is_disposable: false
          is_role_account: false
          reputation_score: 85
          threat_indicators: []
        timestamp: "2025-10-30T10:00:00Z"
    
    validation_with_threats:
      summary: Validation with threat indicators
      value:
        success: true
        message: "Email validation completed"
        result:
          value: "suspicious@malicious-domain.com"
          is_valid: false
          confidence_score: 0.25
          domain_exists: true
          mx_record_exists: true
          is_disposable: false
          is_role_account: false
          reputation_score: 15
          threat_indicators:
            - source: "virustotal"
              indicator: "malicious_domain"
              confidence: 0.95
              description: "Domain associated with malware distribution"
          suggestions:
            - "Avoid interacting with emails from this domain"
        timestamp: "2025-10-30T10:00:00Z"

tags:
  - name: Validation
    description: Email, domain, IP, URL, and sender validation endpoints
  - name: Bulk Processing
    description: High-volume batch processing operations
  - name: Threat Intelligence
    description: Threat intelligence queries and searches
  - name: Reputation
    description: Reputation analysis and scoring
  - name: Administration
    description: Administrative and management endpoints (requires admin key)
  - name: System
    description: System health and monitoring endpoints

externalDocs:
  description: Complete API documentation
  url: https://docs.cybersecurity-platform.example.com
```

---

## 📝 API Usage Examples

### cURL Examples

#### Email Validation
```bash
curl -X POST "https://api.cybersecurity-platform.example.com/v1/validate/email" \
  -H "X-API-Key: cybersec_key_20251030_143022_a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "verify_syntax": true,
    "verify_mx_record": true,
    "check_disposable": true,
    "check_reputation": true
  }'
```

#### Bulk Validation
```bash
curl -X POST "https://api.cybersecurity-platform.example.com/v1/validate/bulk" \
  -H "X-API-Key: cybersec_key_20251030_143022_a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      "user1@example.com",
      "user2@example.com"
    ],
    "domains": [
      "example.com",
      "malicious-site.com"
    ],
    "options": {
      "check_reputation": true,
      "check_threats": true,
      "max_concurrent": 10
    }
  }'
```

#### Threat Intelligence Query
```bash
curl -X POST "https://api.cybersecurity-platform.example.com/v1/threats/query" \
  -H "X-API-Key: cybersec_key_20251030_143022_a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{
    "value": "8.8.8.8",
    "query_type": "ip",
    "include_context": true,
    "include_related": true,
    "time_range_days": 30
  }'
```

#### Create API Key (Admin)
```bash
curl -X POST "https://api.cybersecurity-platform.example.com/v1/admin/api-keys" \
  -H "X-API-Key: cybersec_admin_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Service",
    "is_admin": false,
    "rate_limit": 1000,
    "rate_window": 60,
    "description": "API key for production services"
  }'
```

### JavaScript/Node.js Examples

#### Using Fetch API
```javascript
// Email validation
const validateEmail = async (email) => {
  const response = await fetch('https://api.cybersecurity-platform.example.com/v1/validate/email', {
    method: 'POST',
    headers: {
      'X-API-Key': 'cybersec_key_20251030_143022_a1b2c3d4e5f6...',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: email,
      verify_syntax: true,
      verify_mx_record: true,
      check_disposable: true,
      check_reputation: true
    })
  });
  
  const result = await response.json();
  return result;
};

// Bulk validation
const bulkValidate = async (emails, domains) => {
  const response = await fetch('https://api.cybersecurity-platform.example.com/v1/validate/bulk', {
    method: 'POST',
    headers: {
      'X-API-Key': 'cybersec_key_20251030_143022_a1b2c3d4e5f6...',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      emails: emails,
      domains: domains,
      options: {
        check_reputation: true,
        check_threats: true,
        max_concurrent: 10
      }
    })
  });
  
  const result = await response.json();
  return result;
};
```

#### Using Axios
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.cybersecurity-platform.example.com/v1',
  headers: {
    'X-API-Key': 'cybersec_key_20251030_143022_a1b2c3d4e5f6...',
    'Content-Type': 'application/json'
  }
});

// Threat intelligence query
const queryThreatIntel = async (value, queryType) => {
  try {
    const response = await api.post('/threats/query', {
      value: value,
      query_type: queryType,
      include_context: true,
      include_related: false,
      time_range_days: 30
    });
    
    return response.data;
  } catch (error) {
    console.error('API Error:', error.response.data);
    throw error;
  }
};

// Reputation query
const queryReputation = async (value, valueType) => {
  try {
    const response = await api.post('/reputation/query', {
      value: value,
      value_type: valueType,
      detailed: true
    });
    
    return response.data;
  } catch (error) {
    console.error('API Error:', error.response.data);
    throw error;
  }
};
```

### Python Examples

#### Using Requests
```python
import requests
import json

API_BASE_URL = "https://api.cybersecurity-platform.example.com/v1"
API_KEY = "cybersec_key_20251030_143022_a1b2c3d4e5f6..."

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def validate_email(email):
    """Validate an email address"""
    payload = {
        "email": email,
        "verify_syntax": True,
        "verify_mx_record": True,
        "check_disposable": True,
        "check_reputation": True
    }
    
    response = requests.post(
        f"{API_BASE_URL}/validate/email",
        headers=headers,
        json=payload
    )
    
    return response.json()

def bulk_validate(emails=None, domains=None, ip_addresses=None):
    """Perform bulk validation"""
    payload = {
        "emails": emails or [],
        "domains": domains or [],
        "ip_addresses": ip_addresses or [],
        "options": {
            "check_reputation": True,
            "check_threats": True,
            "max_concurrent": 10
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/validate/bulk",
        headers=headers,
        json=payload
    )
    
    return response.json()

def query_threat_intel(value, query_type):
    """Query threat intelligence"""
    payload = {
        "value": value,
        "query_type": query_type,
        "include_context": True,
        "include_related": False,
        "time_range_days": 30
    }
    
    response = requests.post(
        f"{API_BASE_URL}/threats/query",
        headers=headers,
        json=payload
    )
    
    return response.json()

# Example usage
if __name__ == "__main__":
    # Validate email
    email_result = validate_email("user@example.com")
    print("Email validation:", json.dumps(email_result, indent=2))
    
    # Bulk validation
    bulk_result = bulk_validate(
        emails=["user1@example.com", "user2@example.com"],
        domains=["example.com", "malicious-site.com"]
    )
    print("Bulk validation:", json.dumps(bulk_result, indent=2))
    
    # Threat intelligence query
    threat_result = query_threat_intel("8.8.8.8", "ip")
    print("Threat intelligence:", json.dumps(threat_result, indent=2))
```

#### Using Async/Await
```python
import aiohttp
import asyncio

async def validate_email_async(session, email):
    """Validate an email address asynchronously"""
    payload = {
        "email": email,
        "verify_syntax": True,
        "verify_mx_record": True,
        "check_disposable": True,
        "check_reputation": True
    }
    
    async with session.post(
        f"{API_BASE_URL}/validate/email",
        headers=headers,
        json=payload
    ) as response:
        return await response.json()

async def bulk_validate_async(session, emails, domains):
    """Perform bulk validation asynchronously"""
    payload = {
        "emails": emails,
        "domains": domains,
        "options": {
            "check_reputation": True,
            "check_threats": True,
            "max_concurrent": 10
        }
    }
    
    async with session.post(
        f"{API_BASE_URL}/validate/bulk",
        headers=headers,
        json=payload
    ) as response:
        return await response.json()

async def main():
    """Main async function"""
    async with aiohttp.ClientSession() as session:
        # Validate email
        email_result = await validate_email_async(session, "user@example.com")
        print("Email validation:", json.dumps(email_result, indent=2))
        
        # Bulk validation
        bulk_result = await bulk_validate_async(
            session,
            emails=["user1@example.com", "user2@example.com"],
            domains=["example.com"]
        )
        print("Bulk validation:", json.dumps(bulk_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

---

**Document Version**: 1.0  
**Last Updated**: October 30, 2025  
**Classification**: Public  
**Review Date**: January 30, 2026
