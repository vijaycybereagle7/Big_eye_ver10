# SSL Labs API v4 Complete Documentation

**Last update:** 17 October 2023  
**Author:** Nauman Shah <nshah@qualys.com>

## Overview

This document explains the SSL Labs Assessment APIs, which can be used to test SSL servers available on the public Internet.

## Protocol Overview

The protocol is based on HTTP and JSON. All API calls should use GET except for register API, which must use POST. Specify the parameters in the query string with HTTP header of the registered email, as explained in the following paragraphs. The response body contains the results in a JSON payload.

For example, the client requests an assessment from the servers and receives an existing report if available. Otherwise, the server will start a new assessment and the client should periodically check to see if the job is complete.

## Terms and Conditions

SSL Labs APIs are provided free of charge, subject to our terms and conditions: <https://www.ssllabs.com/about/terms.html>. The spirit of the license is that the APIs are made available so that system operators can test their own infrastructure. 

**Commercial use is generally not allowed**, except with an explicit permission from Qualys. For CAs, CDNs, hosting companies, and domain name registrars, API usage is permitted but requires prior contact with Qualys.

## API Base URLs

**Main API:** `https://api.ssllabs.com/api/v4/`  
**Development API:** `https://api.dev.ssllabs.com/api/v4/` (for testing features not yet deployed to production)

**Availability Check:** `https://api.ssllabs.com/api/v4/info`

## Authentication

**IMPORTANT:** SSL Labs API v4 requires registration before use. You must:

1. Register your organization using the `register` API endpoint
2. Use your registered email address in the `email` header for all subsequent API calls
3. **Note:** Email services like Gmail, Yahoo, or Hotmail are NOT allowed

## API Endpoints

### 1. Register for API Access

**Endpoint:** `register`  
**Method:** POST  
**URL:** `https://api.ssllabs.com/api/v4/register`

#### Parameters

| Parameter        | Type   | Required | Description                                                                                          |
|------------------|--------|----------|------------------------------------------------------------------------------------------------------|
| firstName        | String | Yes      | First name                                                                                          |
| lastName         | String | Yes      | Last name                                                                                           |
| email            | String | Yes      | Organization email (Gmail, Yahoo, Hotmail NOT allowed)                                              |
| organization     | String | Yes      | Organization name                                                                                   |

#### Example

```bash
curl --location 'https://api.ssllabs.com/api/v4/register' \
  --header 'Content-Type: application/json' \
  --data '{
    "firstName":"John",
    "lastName":"Doe", 
    "email":"jdoe@someorganizationemail.com",
    "organization":"Some Organization"
  }'
```

#### Response Object

| Parameter   | Description                   |
|-------------|-------------------------------|
| **message** | Registration message response |
| **status**  | Either `success` or `failure` |

### 2. Check API Availability

**Endpoint:** `info`  
**Method:** GET  
**URL:** `https://api.ssllabs.com/api/v4/info`

#### Parameters
None

#### Response Object (Info)

| Parameter                | Description                                                                                                                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **engineVersion**        | SSL Labs software version (e.g., "2.2.0")                                                                                                                                    |
| **criteriaVersion**      | Rating criteria version (e.g., "2009f")                                                                                                                                     |
| **maxAssessments**       | Maximum number of concurrent assessments allowed                                                                                                                            |
| **currentAssessments**   | Number of ongoing assessments submitted by this client                                                                                                                      |
| **newAssessmentCoolOff** | Cool-off period after each new assessment in milliseconds (must wait before submitting new assessments)                                                                     |
| **messages**             | List of messages (public and private, prefixed with "[Private]")                                                                                                            |

### 3. Initiate and Monitor Assessment

**Endpoint:** `analyze`  
**Method:** GET  
**URL:** `https://api.ssllabs.com/api/v4/analyze`  
**Headers:** `email: your_registered_email@domain.com`

#### Parameters

| Parameter          | Type   | Required | Description                                                                                                                                                                                                                                                                                                                                   |
|-------------------|--------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **host**          | String | Yes      | Hostname to assess                                                                                                                                                                                                                                                                                                                            |
| **publish**       | String | No       | Set to "on" to publish results on public boards<br/>Default: off                                                                                                                                                                                                                                                                              |
| **startNew**      | String | No       | Set to "on" to start new assessment (ignore cached results)<br/>Default: off<br/>**Note:** Use only once to avoid assessment loops                                                                                                                                                                                                            |
| **fromCache**     | String | No       | Use cached results if available<br/>Cannot be used with `startNew`<br/>Default: off                                                                                                                                                                                                                                                            |
| **maxAge**        | String | No       | Maximum report age in hours (when using fromCache)                                                                                                                                                                                                                                                                                           |
| **all**           | String | No       | Endpoint summary detail level:<br/>`on` - Always return full information<br/>`done` - Return full information only when assessment is complete<br/>Default: on                                                                                                                                                                              |
| **ignoreMismatch**| String | No       | Set to "on" to proceed if certificate doesn't match hostname<br/>Default: off                                                                                                                                                                                                                                                                 |

#### Examples

```bash
# Basic assessment
curl --location 'https://api.ssllabs.com/api/v4/analyze?host=www.ssllabs.com' \
  --header 'email: jdoe@someorganizationemail.com'

# Assessment with publication
curl --location 'https://api.ssllabs.com/api/v4/analyze?host=www.ssllabs.com&publish=on' \
  --header 'email: jdoe@someorganizationemail.com'

# Start new assessment
curl --location 'https://api.ssllabs.com/api/v4/analyze?host=example.com&startNew=on' \
  --header 'email: jdoe@someorganizationemail.com'
```

#### Response Object (Host)

| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                           |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **host**            | Assessment host (hostname or IP address)                                                                                                                                                                                                                                                                                                                             |
| **port**            | Assessment port (e.g., 443)                                                                                                                                                                                                                                                                                                                                           |
| **protocol**        | Protocol (e.g., HTTP)                                                                                                                                                                                                                                                                                                                                                 |
| **isPublic**        | `true` if publicly available on SSL Labs boards                                                                                                                                                                                                                                                                                                                      |
| **status**          | Assessment status: DNS, ERROR, IN_PROGRESS, READY                                                                                                                                                                                                                                                                                                                    |
| **statusMessage**   | Status message in English                                                                                                                                                                                                                                                                                                                                             |
| **startTime**       | Assessment start time (milliseconds since 1970)                                                                                                                                                                                                                                                                                                                      |
| **testTime**        | Assessment completion time (milliseconds since 1970)                                                                                                                                                                                                                                                                                                                 |
| **engineVersion**   | Assessment engine version                                                                                                                                                                                                                                                                                                                                             |
| **criteriaVersion** | Grading criteria version                                                                                                                                                                                                                                                                                                                                              |
| **cacheExpiryTime** | When assessment expires from cache                                                                                                                                                                                                                                                                                                                                    |
| **certHostnames[]** | Certificate hostnames (when hostname mismatch occurs)                                                                                                                                                                                                                                                                                                                |
| **endpoints[]**     | List of Endpoint objects                                                                                                                                                                                                                                                                                                                                              |
| **certs[]**         | List of certificate chain objects                                                                                                                                                                                                                                                                                                                                     |

### 4. Get Endpoint Details

**Endpoint:** `getEndpointData`  
**Method:** GET  
**URL:** `https://api.ssllabs.com/api/v4/getEndpointData`  
**Headers:** `email: your_registered_email@domain.com`

#### Parameters

| Parameter     | Type   | Required | Description                                                                                      |
|---------------|--------|----------|--------------------------------------------------------------------------------------------------|
| **host**      | String | Yes      | Hostname                                                                                        |
| **s**         | String | Yes      | Endpoint IP address                                                                             |
| **fromCache** | String | No       | Use cached results if available<br/>Default: off                                                |

#### Example

```bash
curl --location 'https://api.ssllabs.com/api/v4/analyze?host=www.ssllabs.com&s=173.203.82.166' \
  --header 'email: jdoe@someorganizationemail.com'
```

### 5. Get Status Codes

**Endpoint:** `getStatusCodes`  
**Method:** GET  
**URL:** `https://api.ssllabs.com/api/v4/getStatusCodes`

#### Parameters
None

#### Response Object (StatusCodes)

| Parameter         | Description                                                                                                                       |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **statusDetails** | Map of status detail codes and English translations                                                                              |

### 6. Get Root Certificates

**Endpoint:** `getRootCertsRaw`  
**Method:** GET  
**URL:** `https://api.ssllabs.com/api/v4/getRootCertsRaw`

#### Parameters

| Parameter      | Type   | Required | Description                                                    |
|----------------|--------|----------|----------------------------------------------------------------|
| **trustStore** | String | Yes      | Trust store type:<br/>1-Mozilla (default)<br/>2-Apple MacOS<br/>3-Android<br/>4-Java<br/>5-Windows |

#### Examples

```bash
# Mozilla trust store (default)
https://api.ssllabs.com/api/v4/getRootCertsRaw

# Apple MacOS trust store  
https://api.ssllabs.com/api/v4/getRootCertsRaw?trustStore=2

# Android trust store
https://api.ssllabs.com/api/v4/getRootCertsRaw?trustStore=3
```

## Protocol Usage

### Standard Assessment Flow

1. **Start Assessment:** Call `analyze` with `startNew=on` and `all=done`
2. **Monitor Progress:** Call `analyze` periodically (without `startNew`) until status is READY or ERROR
3. **Multiple Servers:** When multiple servers exist behind one hostname, they are tested one at a time
4. **Interim Results:** During assessment, responses contain only endpoint status
5. **Complete Results:** At completion, response contains all available information

### Cached Results Flow

1. **Request Cached Data:** Call `analyze` with `fromCache=on` and `all=done`
2. **Set Max Age:** Set `maxAge` to control report freshness (impacts IP forwarding to tested server)
3. **Immediate Response:** Return cached data if available
4. **Start New Assessment:** Otherwise, new assessment begins
5. **Monitor Progress:** Continue calling `analyze` until completion

## Rate Limits and Performance

### Key Guidelines

- **Assessment Duration:** Server assessments take at least 60 seconds (intentionally slow to avoid harming servers)
- **Polling Strategy:** 
  - Poll every 5 seconds until status changes to IN_PROGRESS
  - Then poll every 10 seconds until completion
- **Concurrent Assessments:** Keep to minimum; test one hostname at a time when possible

### Rate Limit Headers

All successful API calls include these response headers:
- **`X-Max-Assessments`**: Maximum concurrent assessments allowed
- **`X-Current-Assessments`**: Current number of active assessments

### Rate Limit Error Codes

| Code | Description                                                                                                          | Action                                                      |
|------|----------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **429** | Too many requests or too many new assessments too fast                                                            | Reduce concurrent assessments and submission rate           |
| **529** | Service overloaded                                                                                                 | Wait 15+ minutes before retrying                           |
| **503** | Service unavailable (maintenance)                                                                                  | Wait 15+ minutes before retrying                           |
| **500** | Internal error                                                                                                     | Retry request                                               |

### Other Error Codes

| Code | Description                                                                                  | Action                    |
|------|----------------------------------------------------------------------------------------------|---------------------------|
| **400** | Invalid parameters                                                                          | Correct parameter values  |
| **441** | Unauthorized (not registered)                                                               | Register via register API |

## Error Response Format

When API calls fail, responses include an array of error messages:

```json
{"errors":[{"field":"host","message":"qp.mandatory"}]}
```

- **field**: API parameter name with incorrect value
- **message**: Detailed error description

## Protocol Evolution

The API is versioned. New versions are introduced for incompatible changes. Existing applications can continue using previous versions as long as supported.

## Response Object Structures

### Endpoint Object

| Parameter                | Description                                                                                                                                                                      |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **ipAddress**            | Endpoint IP address (IPv4 or IPv6)                                                                                                                                               |
| **serverName**           | Server name from reverse DNS                                                                                                                                                      |
| **statusMessage**        | "Ready" if assessment successful                                                                                                                                                  |
| **statusDetails**        | Current operation code                                                                                                                                                           |
| **statusDetailsMessage** | Current operation description                                                                                                                                                     |
| **grade**                | Grade: A+, A-, A-F, T (no trust), M (certificate name mismatch)                                                                                                                  |
| **gradeTrustIgnored**    | Grade with trust issues ignored                                                                                                                                                   |
| **futureGrade**          | Next grade due to upcoming criteria changes (null if no impact)                                                                                                                  |
| **hasWarnings**          | True if warnings affect score (e.g., A- instead of A)                                                                                                                            |
| **isExceptional**        | True for exceptional configurations (receives A+)                                                                                                                                 |
| **progress**             | Assessment progress percentage                                                                                                                                                    |
| **eta**                  | Estimated completion time (seconds)                                                                                                                                               |
| **delegation**           | Domain delegation status:<br/>bit 0 (1) - non-prefixed<br/>bit 1 (2) - prefixed                                                                                                  |
| **details**              | EndpointDetails object (when `all` parameter used)                                                                                                                                |

### Endpoint Details

The `details` object contains comprehensive assessment information including:

#### Certificate Information
- **certChains[]**: Certificate chain objects
- **cert subjects, issuers, validity periods**
- **Certificate signature algorithms and key information**

#### Protocol Support
- **protocols[]**: Supported SSL/TLS versions
- **suites[]**: Cipher suites per protocol
- **namedGroups**: Supported elliptic curve groups

#### Security Tests
- **vulnBeast**: BEAST attack vulnerability
- **heartbleed**: Heartbleed vulnerability
- **poodle**: POODLE attack vulnerability
- **freak**: FREAK attack vulnerability
- **logjam**: Logjam attack vulnerability
- **drownVulnerable**: DROWN attack vulnerability
- **rc4WithModern**: RC4 cipher usage
- **forwardSecrecy**: Forward secrecy support

#### Session and Handshake
- **renegSupport**: Renegotiation support
- **sessionResumption**: Session resumption capability
- **compressionMethods**: Supported compression
- **sessionTickets**: Session ticket support

#### Extensions and Features
- **ocspStapling**: OCSP stapling support
- **alpnProtocols**: ALPN protocol list
- **npnProtocols**: NPN protocol list
- **supportsAead**: AEAD cipher support
- **supportsCBC**: CBC cipher support

#### HSTS and Security Headers
- **hstsPolicy**: HSTS policy object
- **hpkpPolicy**: HPKP policy object (deprecated)
- **hstsPreloads[]**: Preloaded HSTS information

#### Advanced Features
- **implementsTLS13MandatoryCS**: TLS 1.3 mandatory cipher suite support
- **zeroRTTEnabled**: 0-RTT test results
- **sims**: Client simulation results
- **httpTransactions[]**: HTTP transaction details

## Response Headers

All successful API responses include:

```
X-Max-Assessments: <maximum concurrent assessments>
X-Current-Assessments: <current active assessments>
```

These headers help you manage your assessment rate and concurrent requests.

## Best Practices

1. **Registration First**: Always register before using any API
2. **Rate Limit Respect**: Monitor response headers to stay within limits
3. **Polling Strategy**: Use variable polling (5s → 10s intervals)
4. **Error Handling**: Implement exponential backoff for 503/529 errors
5. **Client Diversification**: Randomize retry delays when possible
6. **Single Assessment**: Test one hostname at a time when not urgent
7. **Email Requirements**: Use organization email, not consumer email services

## Example Implementation

```bash
#!/bin/bash

# Register first
REGISTER_RESPONSE=$(curl -s -X POST \
  'https://api.ssllabs.com/api/v4/register' \
  -H 'Content-Type: application/json' \
  -d '{"firstName":"John","lastName":"Doe","email":"jdoe@company.com","organization":"Example Corp"}')

# Check registration success
if echo "$REGISTER_RESPONSE" | grep -q '"status":"success"'; then
  EMAIL="jdoe@company.com"
  
  # Start assessment
  ASSESSMENT_URL="https://api.ssllabs.com/api/v4/analyze?host=example.com&startNew=on&all=done"
  
  # Monitor assessment
  while true; do
    RESPONSE=$(curl -s -H "email: $EMAIL" "$ASSESSMENT_URL")
    STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    echo "Current status: $STATUS"
    
    if [ "$STATUS" = "READY" ] || [ "$STATUS" = "ERROR" ]; then
      echo "$RESPONSE" | jq '.'
      break
    fi
    
    sleep 10
  done
else
  echo "Registration failed"
fi
```

This documentation provides complete coverage of the SSL Labs API v4, including all endpoints, authentication requirements, rate limits, response structures, and implementation guidance.