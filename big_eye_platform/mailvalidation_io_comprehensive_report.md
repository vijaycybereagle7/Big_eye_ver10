# MailValidation.io / IPQualityScore Email Validation API - Comprehensive Research Report

**Date**: October 29, 2025  
**Original Target URL**: https://mailvalidation.io/ (redirects from https://isitarealemail.com/)  
**Actual Service Provider**: IPQualityScore (IPQS)  
**Research Status**: ✅ **SUCCESSFUL**

## Executive Summary

MailValidation.io is a front-end service that redirects to **IPQualityScore (IPQS)**, a comprehensive fraud detection and email validation platform. IPQS offers enterprise-grade email validation with 99.9% accuracy, supporting worldwide email providers with advanced SMTP verification and fraud prevention capabilities.

---

## 🏢 Service Overview

### **Service Provider**: IPQualityScore (IPQS)
- **Website**: https://www.ipqualityscore.com/
- **Primary Email Validation**: https://www.ipqualityscore.com/email-verification
- **API Documentation**: https://www.ipqualityscore.com/documentation/email-validation-api/overview

### **Service Redirect Discovery**
- `https://isitarealemail.com/` → `https://mailvalidation.io/` → `https://www.ipqualityscore.com/login`
- This indicates MailValidation.io operates as a branded interface or reseller for IPQualityScore's services

---

## 💰 Pricing Structure

### **Free Plan** - $0/Month
- **Monthly Lookups**: 1,000
- **Daily Lookups**: 35
- **Features**: Enterprise-grade email validation with 99.9% accuracy
- **CSV Uploads**: 3 per day
- **Custom Rules**: 10
- **SLA**: None

### **Startup Plan** - As low as $99/Month
- **Monthly Lookups**: 5,000
- **Daily Lookups**: 250
- **Features**: All Free plan features
- **CSV Uploads**: 3 per day
- **Custom Rules**: 100
- **SLA**: None

### **SMB Basic Plan** - As low as $499/Month
- **Monthly Lookups**: 10,000
- **Lookups per Second**: 20
- **Features**: All Startup features
- **CSV Uploads**: 3 per day
- **Custom Rules**: 1,000
- **SLA**: None

### **SMB+ Plan** - As low as $999/Month
- **Monthly Lookups**: 75,000
- **Lookups per Second**: At least 20
- **Features**: All SMB Basic features
- **CSV Uploads**: 3 per day
- **Custom Rules**: 5,000
- **SLA Guarantee**: 99.5%

### **Enterprise Plan** - Custom/Month
- **Monthly Lookups**: Custom
- **Lookups per Second**: Enterprise Rate Limits (higher bursts)
- **Features**: All SMB+ features + User Activity Checks
- **CSV Uploads**: Unlimited
- **Custom Rules**: 25,000
- **SLA Guarantee**: 99.9%

---

## 🔧 Validation Methods & Capabilities

### **Core Validation Features**
- **Deep Checks**: Advanced mailbox verification for spam traps, catch-all domains, syntax errors, and invalid addresses
- **Deliverability Estimation**: High/low deliverability rate assessment
- **Disposable Email Detection**: Identifies and blocks temporary mail services
- **Spam Trap Detection**: Detects honeypot email addresses to protect sender reputation
- **Email Age Lookup**: Estimates the email account creation date
- **Abuse History Analysis**: Identifies emails involved in chargebacks, fake accounts, account takeover, SPAM, or trial abuse
- **DNS Validation**: Validates DNS records including SPF, DMARC, MX records, and A records

### **Advanced Features**
- **Email Risk Scoring**: Comprehensive fraud/quality scoring (0-100 scale)
- **Email List Cleaning**: Bulk email hygiene services
- **Domain Reputation**: Domain trust and velocity analysis
- **Email Bounce Checker**: Delivery failure detection
- **Reverse Email Lookup**: Email-to-identity mapping
- **Email Verification Database**: On-premise deployment options
- **Email Spam Test**: Deliverability optimization
- **Leaked Email Checker**: Data breach identification

---

## 📡 SMTP Verification Capabilities

### **SMTP Integration**
- **SMTP Score**: Direct scoring from SMTP verification reflecting mailbox quality
- **Timeout Handling**: Configurable timeout (1-60 seconds, default 7 seconds) for mail provider responses
- **Advanced Mailbox Verification**: SMTP interactions for comprehensive validation
- **DNS Record Support**: MX records and A records for SMTP server verification
- **SPF/DMARC Validation**: Authentication record verification for deliverability

### **SMTP Configuration Options**
- **Fast Mode**: Skip SMTP checks for faster results (syntax, DNS, and risk scoring only)
- **Timeout Control**: Adjustable 1-60 second timeout window
- **Abuse Strictness**: Machine learning detection sensitivity (0-2 scale)
- **Spam Trap Detection**: SMTP-based honeypot identification

---

## 🚀 API Technical Specifications

### **Authentication**
- **Method**: API Key included directly in URL path
- **Alternative Methods**: 
  - GET parameter `key`
  - POST parameter `key`
  - HTTP Header `IPQS-KEY`

### **Endpoints**
```
JSON: https://www.ipqualityscore.com/api/json/email/YOUR_API_KEY_HERE/USER_EMAIL_HERE
XML:  https://www.ipqualityscore.com/api/xml/email/YOUR_API_KEY_HERE/USER_EMAIL_HERE
```

### **HTTP Method**: GET

### **Query Parameters**

#### **Required Parameters**
- `YOUR_API_KEY_HERE`: Your API key
- `USER_EMAIL_HERE`: Email address to validate

#### **Optional Parameters**
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `timeout` | integer | 1-60 | 7 | Maximum seconds to wait for mail provider response |
| `fast` | boolean | true/false | false | Set to 'true' for faster results, 'false' for higher accuracy |
| `suggest_domain` | boolean | true/false | false | Forces typo analysis for domain correction |
| `strictness` | integer | 0-2 | 1 | Controls spam trap detection sensitivity |
| `abuse_strictness` | integer | 0-2 | 0 | Adjusts abusive email pattern detection |
| `strictness` | integer | 0-2 | - | Additional strictness control |
| `abuse_strictness` | integer | 0-2 | - | ML-based abuse detection sensitivity |

### **Response Parameters**

#### **Primary Validation Results**
- `valid` (boolean): Email validity indication
- `timed_out` (boolean): Request timeout status
- `deliverability` (string): Estimated deliverability rate
- `smtp_score` (integer): SMTP verification score
- `overall_score` (integer): Overall fraud/quality score
- `catch_all` (boolean): Catch-all domain detection
- `generic` (boolean): Generic email detection
- `common` (boolean): Common provider detection

#### **Security & Risk Assessment**
- `disposable` (boolean): Disposable email service detection
- `honeypot` (boolean): Honeypot/spam trap detection
- `frequent_complainer` (boolean): High complaint rate detection
- `suspect` (boolean): Suspicious characteristics flag
- `recent_abuse` (boolean): Recent abusive activity
- `fraud_score` (integer 0-100): Fraud risk score
- `leaked` (boolean): Data breach involvement
- `risky_tld` (boolean): Risky Top-Level Domain

#### **Technical Details**
- `dns_valid` (boolean): DNS record validation
- `spf_record` (boolean): SPF record presence
- `dmarc_record` (boolean): DMARC record presence
- `mx_records` (array): Mail exchange records
- `a_records` (array): A records
- `suggested_domain` (string): Domain correction suggestion
- `sanitized_email` (string): Cleaned email format

#### **Analytics & Activity**
- `domain_velocity` (string): Domain usage velocity
- `domain_trust` (string): Domain trust level
- `user_activity` (string): User activity level
- `first_seen` (object): First observation timestamp
- `domain_age` (object): Domain creation age
- `spam_trap_score` (string): Spam trap likelihood assessment

### **Enterprise Plus Features**
- `associated_names`: Associated names (Enterprise Plus plan)
- `associated_phone_numbers`: Associated phone numbers (Enterprise Plus plan)

---

## ⚡ Rate Limits & Performance

### **Rate Limiting by Plan**
- **Free**: 1,000/month, 35/day
- **Startup**: 5,000/month, 250/day
- **SMB Basic**: 10,000/month, 20 per second
- **SMB+**: 75,000/month, 20+ per second
- **Enterprise**: Custom limits, enterprise-grade bursts

### **Performance Characteristics**
- **Accuracy**: 99.9% accuracy rate
- **Timeout Configurable**: 1-60 seconds (default 7 seconds)
- **Fast Mode**: Available for quick validation (skips SMTP checks)
- **Global Support**: Worldwide support for any email provider
- **Real-time Validation**: Suitable for registration and checkout validation

---

## 🛡️ Error Handling

### **API Error Response Format**
```json
{
  "success": false,
  "message": "Error description",
  "request_id": "Unique identifier"
}
```

### **Common Error Messages**
- "You have insufficient credits to make this query."
- "Invalid email address."
- "API key authentication required."

### **HTTP Status Codes**
- Standard HTTP error codes apply
- Rate limiting and quota exceeded responses included

---

## 📚 Additional API Resources

### **Documentation Links**
- **Overview**: `/documentation/email-validation-api/overview`
- **Advanced Options**: `/documentation/email-validation-api/advanced-options`
- **Response Parameters**: `/documentation/email-validation-api/response-parameters`
- **Features & Use Cases**: `/documentation/email-validation-api/features-and-use-cases`
- **Disposable Email Detection**: `/documentation/email-validation-api/disposable-email-detection`
- **Spam Trap Detection**: `/documentation/email-validation-api/spam-trap-detection`

### **Related Services**
- Free Email Verifier
- Disposable Email Address Detection
- Spam Trap Email Address Test
- Email Risk Scoring
- Email Address Fraud Prevention
- Email Age Checker
- Email List Cleaning
- Domain Reputation
- Email Bounce Checker
- Reverse Email Lookup
- Email Verification Database
- Email Spam Test Checker

---

## 🎯 Key Use Cases

### **Real-time Validation**
- User registration verification
- Checkout process validation
- Form submission validation
- Account creation fraud prevention

### **Bulk Processing**
- CSV file upload for batch validation
- Email list cleaning and hygiene
- Marketing campaign optimization
- Database cleanup and maintenance

### **Fraud Prevention**
- Fake account detection
- Spam trap avoidance
- Chargeback prevention
- Trial abuse detection
- Account takeover prevention

---

## 📊 Competitive Advantages

1. **99.9% Accuracy**: Enterprise-grade validation accuracy
2. **Global Coverage**: Worldwide support for any email provider
3. **Comprehensive Scoring**: Multi-layered risk assessment
4. **Flexible Pricing**: Free tier available with scaling options
5. **Advanced DNS Support**: SPF, DMARC, MX, and A record validation
6. **Real-time Performance**: Suitable for live transaction validation
7. **On-premise Options**: Enterprise deployment capabilities
8. **ML-powered Detection**: Advanced abuse and fraud detection

---

## 📸 Screenshots Captured

1. **`mailvalidation_io_main_page.png`** - Cloudflare challenge page
2. **`mailvalidation_io_after_wait.png`** - Initial wait period
3. **`mailvalidation_io_extended_wait.png`** - Extended verification attempt
4. **`mailvalidation_io_after_refresh.png`** - Post-refresh redirect to IPQS

---

## 📋 Research Methodology

### **Navigation Path**
1. Initial access to `https://mailvalidation.io/`
2. Encountered Cloudflare security verification
3. Page refresh triggered redirect to IPQualityScore
4. Systematic extraction from key IPQS pages:
   - Plans & Pricing page
   - API Documentation overview
   - Advanced options documentation
5. Comprehensive content analysis and organization

### **Data Sources Extracted**
- IPQualityScore Plans & Pricing
- Email Validation API Documentation
- Advanced API Options
- Service capability descriptions
- Technical specifications

---

## ✅ Conclusion

MailValidation.io serves as a branded interface for **IPQualityScore's comprehensive email validation API**. The service offers enterprise-grade validation with advanced SMTP verification, comprehensive fraud detection, and flexible pricing starting from a free 1,000 monthly lookups tier. The API provides detailed technical specifications, robust error handling, and extensive validation methods suitable for both real-time and bulk email processing applications.

**Key Strengths**:
- High accuracy (99.9%)
- Comprehensive feature set
- Flexible pricing options
- Advanced fraud prevention
- Global email provider support
- Real-time processing capability

---

*Research conducted by MiniMax Agent on October 29, 2025*  
*Service Discovery: MailValidation.io → IPQualityScore*