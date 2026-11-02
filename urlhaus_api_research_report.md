# URLhaus API Rate Limits and Alternative Data Access Methods

## Executive Summary

The URLhaus API documentation **does not explicitly document rate limits or quotas** for their API endpoints. However, they provide several **alternative data access methods** that don't require API authentication, including bulk malware batches, data feeds, and database browsing.

## Rate Limits and Quotas

### API Rate Limits
- **Status**: **NOT documented** in publicly accessible API documentation
- **Implication**: Rate limits may exist but are not publicly disclosed
- **Recommendation**: Implement conservative request throttling and monitor for throttling responses

### Feed Frequency Restrictions
For ASN, Country, and TLD feeds:
- **Frequency Limit**: Do not fetch feeds more often than **every 10 minutes**
- **Usage Warning**: Feeds are not intended for blocking/blacklisting or IOC use
- **Authentication**: Feeds require user session authentication (login required)

## Alternative Data Access Methods (No API Required)

### 1. Bulk Malware Batches

#### Hourly Malware Batches
- **Access**: `https://datalake.abuse.ch/urlhaus/hourly/`
- **Format**: ZIP archives named `YYYY-MM-DD-HH.zip`
- **Password**: `infected` (required to extract)
- **Authentication**: **None required** - publicly accessible
- **Size**: Ranges from 1.3MB to 148MB per hour
- **Structure**: Standard web directory with direct download links

#### Daily Malware Batches
- **Access**: `https://datalake.abuse.ch/urlhaus/daily/`
- **Format**: ZIP archives named `YYYY-MM-DD.zip`
- **Password**: `infected` (required to extract)
- **Authentication**: **None required** - publicly accessible
- **Size**: 645MB to 1.6GB per day
- **Data Span**: Historical data available from 2023 onwards

### 2. Database Browsing
- **Access**: `https://urlhaus.abuse.ch/browse/`
- **Authentication**: **None required**
- **Features**: Web interface for searching and viewing malicious URLs
- **Use Case**: Manual exploration and research of specific threats

### 3. URLhaus Feeds (Session Required)
**Note**: These feeds require user login/session but no API keys

#### ASN Feed
- **Access**: Via web interface at `https://urlhaus.abuse.ch/feeds/`
- **Input**: AS number (e.g., AS1234)
- **Formats**: CSV or JSON
- **Authentication**: Requires user session login

#### Country Feed
- **Input**: 2-letter country code (e.g., "CH", "US")
- **Formats**: CSV or JSON
- **Authentication**: Requires user session login

#### TLD Feed
- **Input**: Top-level domain (e.g., "com", "de")
- **Formats**: CSV or JSON
- **Authentication**: Requires user session login

### 4. Statistics and Hunting
- **Statistics**: `https://urlhaus.abuse.ch/statistics/`
- **Hunting Alerts**: `https://urlhaus.abuse.ch/hunting/`
- **Authentication**: None required for viewing

## Usage Recommendations

### For Bulk Data Access
1. **Use bulk malware batches** for comprehensive malware sample collection
2. **Implement automated downloads** using standard HTTP tools (wget, curl)
3. **Respect the 10-minute frequency limit** for feed access
4. **Extract files with password** `infected` for malware samples

### For Research and Analysis
1. **Browse the database** for manual investigation
2. **Use feeds with login** for specific filtering (ASN, Country, TLD)
3. **Download hourly batches** for near-real-time analysis
4. **Download daily batches** for historical research

### For Automation
```bash
# Example: Download all hourly batches from specific date range
wget -r -l1 -np -A "2025-10-*.zip" https://datalake.abuse.ch/urlhaus/hourly/

# Example: Download recent daily batches
wget -r -l1 -np -A "2025-10-*.zip" https://datalake.abuse.ch/urlhaus/daily/
```

## Security Considerations

1. **Malware Samples**: All bulk downloads contain live malware - use in isolated environments
2. **Password Protection**: ZIP files require password `infected` for extraction
3. **Data Handling**: Follow proper malware analysis protocols
4. **Rate Limiting**: Implement conservative access patterns even for bulk downloads

## Conclusion

While the URLhaus API requires authentication and doesn't disclose rate limits, they provide extensive **public access methods** for bulk data collection that don't require API keys. The bulk malware batches represent the most comprehensive and accessible data source for researchers who need large-scale threat intelligence data.