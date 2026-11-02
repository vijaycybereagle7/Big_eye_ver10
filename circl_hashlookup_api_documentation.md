# CIRCL Hashlookup API Documentation Summary

*Research conducted on: October 30, 2025*
*Source: https://hashlookup.circl.lu/ and https://www.circl.lu/services/hashlookup/*

## 1. API Base URL

**Base URL:** `https://hashlookup.circl.lu`
- The API uses a RESTful HTTP interface
- Base path is `/` (root level)
- All endpoints are accessed directly from the root host

## 2. Authentication Method

**Authentication:** **NONE** (No authentication required)
- The API is publicly accessible without any API keys, tokens, or credentials
- No authentication mechanisms (OAuth, API keys, etc.) are implemented
- Service is provided on a "best-effort basis" for free

## 3. Rate Limits and Quotas

**Rate Limits:** **Not explicitly defined**
- No specific rate limits or quotas are documented in the OpenAPI specification
- No mention of request throttling or usage quotas in the main documentation
- Service operates on a "best-effort basis" indicating it may have informal limitations
- No explicit "429 Too Many Requests" responses mentioned in the documentation

## 4. Key Endpoints

### 4.1 Single Hash Lookup Endpoints (GET)
- `GET /lookup/md5/{md5}` - Look up a single MD5 hash
- `GET /lookup/sha1/{sha1}` - Look up a single SHA-1 hash  
- `GET /lookup/sha256/{sha256}` - Look up a single SHA-256 hash

### 4.2 Bulk Search Endpoints (POST)
- `POST /bulk/md5` - Perform bulk search for multiple MD5 hashes
- `POST /bulk/sha1` - Perform bulk search for multiple SHA-1 hashes

### 4.3 Contextual/Related Hash Endpoints (GET)
- `GET /children/{sha1}/{count}/{cursor}` - Retrieve child hashes for a SHA-1
- `GET /parents/{sha1}/{count}/{cursor}` - Retrieve parent hashes for a SHA-1

### 4.4 Session Management Endpoints (GET)
- `GET /session/create/{name}` - Create a new session for contextual searches
- `GET /session/get/{name}` - Retrieve session data

### 4.5 Information Endpoints (GET)
- `GET /info` - Get general information about the hashlookup database
- `GET /stats/top` - Retrieve top 100 most queried hash values (if enabled)

## 5. Request/Response Formats

### 5.1 Content Types
- **Consumes:** `application/json` (primarily for POST bulk requests)
- **Produces:** `application/json` for all responses

### 5.2 Request Format
**Single Lookups (GET):**
```
GET /lookup/{hash_type}/{hash_value}
```
No request body required for GET requests.

**Bulk Searches (POST):**
```
POST /bulk/{hash_type}
Content-Type: application/json

{
    "hashes": ["hash1", "hash2", "hash3"]
}
```

### 5.3 Response Format
**Successful Response (200 OK):**
```json
{
    "CRC32": "string",
    "FileName": "string", 
    "FileSize": "number",
    "MD5": "string",
    "SHA1": "string",
    "SHA256": "string", 
    "SHA512": "string",
    "SSDEEP": "string",
    "TLSH": "string",
    "OS": "string",
    "ProductCode": "string",
    "Source": "string",
    "TimeStamp": "string",
    "hashlookup:trust": "number (0-100)"
}
```

**HTTP Status Codes:**
- `200 OK` - Hash found in database
- `400 Bad Request` - Invalid hash format
- `404 Not Found` - Hash not in database
- `500 Internal Server Error` - Server error

## 6. Data Types Available (File Hashes)

### 6.1 Supported Hash Types for Lookup
- **MD5** - Full support (single + bulk)
- **SHA-1** - Full support (single + bulk + contextual)
- **SHA-256** - Full support (single + contextual)

### 6.2 Additional Hash Types in Responses
- **SHA-512** - Included in responses when available
- **SSDEEP** - Fuzzy hashing included in responses
- **TLSH** - Trend Locality Sensitive Hashing included in responses

### 6.3 Hashtrust Levels
- **0-49:** Low trust (less likely legitimate)
- **50:** Neutral trust level
- **51-100:** High trust (appears in multiple sources)

## 7. Example API Calls

### 7.1 Single Hash Lookup Examples
```bash
# MD5 Lookup
curl "https://hashlookup.circl.lu/lookup/md5/a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

# SHA-1 Lookup  
curl "https://hashlookup.circl.lu/lookup/sha1/0beec7b5ea3f0fdbcbcc11dcfa04313f8902be7"

# SHA-256 Lookup
curl "https://hashlookup.circl.lu/lookup/sha256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

### 7.2 Bulk Hash Search Examples
```bash
# Bulk MD5 Search
curl -X POST "https://hashlookup.circl.lu/bulk/md5" \
  -H "Content-Type: application/json" \
  -d '{"hashes": ["a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6", "deadbeefcafebabe0123456789abcdef0"]}'

# Bulk SHA-1 Search
curl -X POST "https://hashlookup.circl.lu/bulk/sha1" \
  -H "Content-Type: application/json" \
  -d '{"hashes": ["0beec7b5ea3f0fdbcbcc11dcfa04313f8902be7", "da39a3ee5e6b4b0d3255bfef95601890afd80709"]}'
```

### 7.3 Contextual Search Examples
```bash
# Get Children of SHA-1 (10 results, cursor 0)
curl "https://hashlookup.circl.lu/children/0beec7b5ea3f0fdbcbcc11dcfa04313f8902be7/10/0"

# Get Parents of SHA-1 (20 results, cursor 0)
curl "https://hashlookup.circl.lu/parents/0beec7b5ea3f0fdbcbcc11dcfa04313f8902be7/20/0"
```

### 7.4 Session Management Examples
```bash
# Create Session
curl "https://hashlookup.circl.lu/session/create/mySessionName"

# Get Session Data (requires hashlookup_session header)
curl "https://hashlookup.circl.lu/session/get/mySessionName" \
  -H "hashlookup_session: mySessionName"
```

### 7.5 Information Examples
```bash
# Get Database Info
curl "https://hashlookup.circl.lu/info"

# Get Top Stats
curl "https://hashlookup.circl.lu/stats/top"
```

### 7.6 DNS Query Alternative
```
# DNS TXT query format
dig TXT <hash>.dns.hashlookup.circl.lu
```

## 8. Additional Features

### 8.1 Offline Capability
- **Bloom Filter:** Monthly updated ~700MB Bloom filter available
- **File:** `hashlookup-full.bloom` from https://cra.circl.lu/hashlookup/hashlookup-full.bloom
- **Contains:** All SHA-1 values (no metadata)
- **Format:** DCSO bloom library format
- **Usage:** Local offline hash checking

### 8.2 Data Sources
- NIST NSRL (all RDS sets)
- Windows 10/11 builds
- Ubuntu, CentOS, Fedora, Kali Linux, OpenSUSE
- OpenBSD
- CDNJS
- Snap public repository

### 8.3 Trust Scoring
The API includes a trust scoring system (0-100) based on:
- Number of sources the hash appears in
- Reliability of those sources
- Historical data

## 9. Client Libraries and Tools
- **Python:** PyHashlookup
- **R:** hashlookup R package  
- **MISP:** MISP modules
- **Cortex:** TheHive Project analyzers
- **Munin:** Monitoring tool
- **Forensic Analyser:** hashlookup-forensic-analyser

## 10. Important Notes
- **Purpose:** Identifies *known files* but does NOT classify files as malicious/non-malicious
- **Context:** Provides contextual information for digital forensic analysis
- **Availability:** Free service on best-effort basis
- **Privacy:** Queries are shared publicly; use offline Bloom filter for sensitive work
- **Updates:** Database updated regularly with new software packages and OS builds