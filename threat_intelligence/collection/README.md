# Threat Intelligence Collection Scripts

A comprehensive Python toolkit for automated threat intelligence collection from 13 major sources. This project provides a unified interface to query multiple threat intelligence APIs simultaneously with built-in rate limiting, error handling, and data normalization.

## Features

- **13 Threat Intelligence Sources**: VirusTotal, AbuseIPDB, Google Safe Browsing, AlienVault OTX, Shodan, SecurityTrails, URLhaus, PhishTank, MalwareBazaar, ThreatFox, CIRCL hashlookup, Spamhaus, GreyNoise
- **Async/Await Support**: High-performance concurrent API queries
- **Rate Limiting**: Built-in rate limiting for each service
- **Error Handling**: Robust error handling with retry mechanisms
- **Data Normalization**: Standardized output format across all sources
- **Bulk Operations**: Support for batch processing multiple indicators
- **Flexible Configuration**: JSON-based configuration management
- **Comprehensive Logging**: Detailed logging and monitoring

## Installation

1. Clone or download the project files
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the configuration template:
   ```bash
   cp threat_intel_config.json.template threat_intel_config.json
   ```

2. Edit `threat_intel_config.json` and add your API keys:
   ```json
   {
     "virustotal_api_key": "YOUR_VIRUSTOTAL_API_KEY_HERE",
     "abuseipdb_api_key": "YOUR_ABUSEIPDB_API_KEY_HERE",
     "google_safebrowsing_api_key": "YOUR_GOOGLE_SAFE_BROWSING_API_KEY_HERE",
     "otx_api_key": "YOUR_ALIENVAULT_OTX_API_KEY_HERE",
     "shodan_api_key": "YOUR_SHODAN_API_KEY_HERE",
     "securitytrails_api_key": "YOUR_SECURITYTRAILS_API_KEY_HERE",
     "phishtank_app_key": "YOUR_PHISHTANK_APP_KEY_HERE",
     "circl_username": "YOUR_CIRCL_USERNAME_HERE",
     "circl_password": "YOUR_CIRCL_PASSWORD_HERE",
     "greynoise_api_key": "YOUR_GREYNOISE_API_KEY_HERE"
   }
   ```

## Supported Indicators

- **IP Addresses**: Malicious IPs, botnets, scanning activity
- **Domains**: Malware domains, phishing domains, suspicious domains
- **URLs**: Malicious URLs, phishing sites, malware distribution
- **File Hashes**: MD5, SHA1, SHA256, SHA512 hashes of malware

## API Sources

### 1. VirusTotal API
- **Scope**: Files, URLs, domains, IP addresses
- **Rate Limit**: 4 requests/minute (free), 500/day (public API)
- **Authentication**: API Key in X-API-Key header
- **Output**: Reputation scores, scan results, related samples

### 2. AbuseIPDB API
- **Scope**: IP addresses
- **Rate Limit**: 1000 requests/day
- **Authentication**: API Key in Key header
- **Output**: Abuse reports, confidence scores

### 3. Google Safe Browsing API v4
- **Scope**: URLs, domains, file hashes
- **Rate Limit**: 600 requests/10 minutes
- **Authentication**: API Key in key parameter
- **Output**: Threat matches, malware detection

### 4. AlienVault OTX
- **Scope**: IPs, domains, URLs, file hashes
- **Rate Limit**: 10,000 requests/day
- **Authentication**: API Key in X-OTX-API-KEY header
- **Output**: Threat pulses, malware families, IOCs

### 5. Shodan API
- **Scope**: IP addresses, network services
- **Rate Limit**: 100 requests/day (free tier)
- **Authentication**: API Key in key parameter
- **Output**: Host information, open ports, vulnerabilities

### 6. SecurityTrails API
- **Scope**: Domains, IP addresses
- **Rate Limit**: 100 requests/day (free tier)
- **Authentication**: API Key in apikey header
- **Output**: DNS records, historical data, subdomains

### 7. URLhaus API
- **Scope**: URLs, domains, IPs, file hashes
- **Rate Limit**: 1000 requests/hour
- **Authentication**: None (public API)
- **Output**: Malware URLs, samples, families

### 8. PhishTank API
- **Scope**: URLs
- **Rate Limit**: 1000 requests/hour
- **Authentication**: App Key in form data
- **Output**: Phishing detection, verified status

### 9. MalwareBazaar API
- **Scope**: File hashes, URLs, domains, IPs
- **Rate Limit**: 1000 requests/hour
- **Authentication**: None (public API)
- **Output**: Malware samples, signatures, families

### 10. ThreatFox API
- **Scope**: IOCs (IPs, domains, URLs, hashes)
- **Rate Limit**: 1000 requests/hour
- **Authentication**: None (public API)
- **Output**: IOCs, confidence scores, malware tags

### 11. CIRCL Hashlookup API
- **Scope**: File hashes (MD5, SHA1, SHA256, SHA512)
- **Rate Limit**: 100 requests/hour
- **Authentication**: HTTP Basic Auth
- **Output**: Hash information, VT links

### 12. Spamhaus
- **Scope**: IP addresses, domains
- **Rate Limit**: 1000 requests/hour
- **Authentication**: None (public DNSBL)
- **Output**: Blacklist status, spam categorization

### 13. GreyNoise API
- **Scope**: IP addresses
- **Rate Limit**: 1000 requests/hour
- **Authentication**: API Key in key header
- **Output**: Internet background noise, classification

## Usage Examples

### Command Line Interface

```bash
# Single indicator lookup
python threat_intel_manager.py --indicator "8.8.8.8" --type ip --verbose

# Bulk lookup from file
python threat_intel_manager.py --file indicators.txt --collectors virustotal urlhaus threatfox

# Specific indicator type
python threat_intel_manager.py --indicator "google.com" --type domain

# Limit number of collectors
python threat_intel_manager.py --indicator "192.0.2.1" --max-collectors 5

# Custom output
python threat_intel_manager.py --indicator "malware.com" --output malware_results.json --output-dir ./results
```

### Python API Usage

```python
import asyncio
from threat_intel_manager import ThreatIntelligenceManager

async def main():
    # Initialize manager
    manager = ThreatIntelligenceManager("threat_intel_config.json")
    
    # Single indicator lookup
    results = await manager.lookup_indicator("8.8.8.8", "ip")
    
    # Bulk lookup
    indicators = ["google.com", "8.8.8.8", "d41d8cd98f00b204e9800998ecf8427e"]
    results = await manager.bulk_lookup(indicators, "auto", delay_between_requests=2.0)
    
    # Print summary
    manager.print_summary(results)
    
    # Save results
    manager.save_results(results, "threat_intel_output.json")
    
    # Close collectors
    await manager.close()

asyncio.run(main())
```

### Individual Collector Usage

```python
import asyncio
from urlhaus_collector import URLhausCollector

async def main():
    async with URLhausCollector() as collector:
        # URL lookup
        results = await collector.lookup_url("http://malware-example.com/payload.exe")
        
        # Domain lookup
        results = await collector.lookup_domain("malware-example.com")
        
        # Recent malware
        results = await collector.get_recent_malware(limit=10)
        
        for result in results:
            print(f"Indicator: {result.indicator}")
            print(f"Source: {result.source}")
            print(f"Confidence: {result.confidence}")
            print(f"Tags: {result.tags}")

asyncio.run(main())
```

## Output Format

All collectors return standardized `ThreatIntelligenceData` objects:

```python
@dataclass
class ThreatIntelligenceData:
    source: str                    # Collector name
    indicator_type: str            # 'ip', 'domain', 'url', 'hash'
    indicator: str                 # The actual indicator value
    timestamp: datetime            # When the data was collected
    confidence: Optional[float]    # Confidence score (0.0-1.0)
    score: Optional[float]         # Numeric score
    tags: List[str]                # Relevant tags
    raw_data: Dict[str, Any]       # Original API response
    metadata: Dict[str, Any]       # Additional metadata
```

## Rate Limiting

Each collector implements its own rate limiting:

- Built-in request queuing
- Automatic delays between requests
- Respect for API-specific limits
- Error handling for rate limit responses

## Error Handling

- **Network timeouts**: Automatic retry with exponential backoff
- **Authentication errors**: Clear error messages
- **Rate limiting**: Automatic delays and retries
- **API errors**: Graceful degradation with error logging
- **Invalid data**: Validation and sanitization

## Data Normalization

All APIs normalize data to a common format:
- Consistent indicator types
- Standardized confidence scores (0.0-1.0)
- Unified tag system
- Normalized timestamps (UTC)
- Rich metadata preservation

## Performance Considerations

- **Concurrent requests**: Multiple APIs queried simultaneously
- **Connection pooling**: Reused HTTP connections
- **Rate limiting**: Prevents API blocking
- **Memory efficient**: Streaming data processing
- **Scalable**: Handles large indicator lists

## Security Best Practices

- **API Key Protection**: Store keys in configuration files with proper permissions
- **Network Security**: Use HTTPS for all API calls
- **Data Privacy**: Sanitize logs and outputs
- **Access Control**: Limit who can run the collection scripts
- **Audit Logging**: Track all API usage

## Testing

```bash
# Run individual collector tests
python urlhaus_collector.py
python virustotal_collector.py

# Run comprehensive tests
python -m pytest tests/ -v
```

## API Keys Setup

### VirusTotal
1. Register at https://www.virustotal.com/
2. Go to API Key section
3. Copy your API key

### AbuseIPDB
1. Sign up at https://www.abuseipdb.com/
2. Navigate to API section
3. Generate API key

### Google Safe Browsing
1. Create project in Google Cloud Console
2. Enable Safe Browsing API
3. Create API key

### AlienVault OTX
1. Register at https://otx.alienvault.com/
2. Go to API section
3. Generate API key

### Shodan
1. Create account at https://account.shodan.io/
2. Go to API Key section
3. Copy API key

### SecurityTrails
1. Register at https://securitytrails.com/
2. Navigate to API section
3. Generate API key

### PhishTank
1. Register at https://www.phishtank.com/
2. Go to API section
3. Register for API access

### CIRCL
1. Register at https://www.circl.lu/
2. Apply for hashlookup access
3. Note credentials

### GreyNoise
1. Sign up at https://www.greynoise.io/
2. Go to API section
3. Generate API key

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API keys are correct
   - Check account status and quotas
   - Ensure proper header format

2. **Rate Limiting**
   - Increase delay between requests
   - Reduce number of concurrent collectors
   - Check API-specific limits

3. **Network Issues**
   - Check internet connection
   - Verify firewall settings
   - Try different timeouts

4. **Data Issues**
   - Validate indicator formats
   - Check for special characters
   - Ensure proper encoding

### Debugging

Enable verbose logging:
```bash
python threat_intel_manager.py --indicator "test.com" --verbose
```

Check individual collector logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is provided as-is for educational and research purposes. Please respect the terms of service of each API provider.

## Contributing

Contributions are welcome! Please ensure:
- Code follows Python standards
- Tests are included
- Documentation is updated
- API rate limits are respected

## Disclaimer

This tool is for legitimate security research and threat intelligence gathering only. Users are responsible for ensuring compliance with all applicable laws and API terms of service. The authors are not responsible for any misuse of this software.