## Description
Brief description of changes made in this pull request.

## Type of Change
Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update (changes to documentation only)
- [ ] Security fix (patch for a security vulnerability)
- [ ] Performance improvement (non-breaking performance enhancement)
- [ ] Refactoring (code change that neither fixes a bug nor adds a feature)
- [ ] Test improvement (adding missing tests or correcting existing tests)

## Changes Made
List the specific changes made in this PR:

### Added
- What was added?

### Changed
- What was changed?

### Deprecated
- What functionality is being deprecated?

### Removed
- What functionality was removed?

### Fixed
- What was fixed?

### Security
- Security improvements made?

## Testing
Please describe the tests that you ran to verify your changes:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Load tests pass
- [ ] Security tests pass
- [ ] Manual testing completed
- [ ] Database migrations tested
- [ ] API endpoint testing completed

### Test Results
Include test execution results or screenshots:

### Manual Testing Steps
1. 
2. 
3. 

## Code Quality
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code has been performed
- [ ] Code is properly commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation have been made
- [ ] No new warnings introduced
- [ ] Code is backward compatible (or breaking changes are documented)

### Code Analysis Results
```bash
# Run these commands and include results:

# Python linting
flake8 [affected_files] || echo "No linting issues"

# Type checking
mypy [affected_files] || echo "No type errors"

# Security scan
bandit -r [affected_directories] || echo "No security issues"

# Code formatting check
black --check [affected_files] || echo "Code needs formatting"
```

## Documentation
- [ ] README updated (if applicable)
- [ ] API documentation updated
- [ ] Docstrings updated
- [ ] Configuration documentation updated
- [ ] Deployment documentation updated

### Documentation Changes
Brief description of documentation changes made:

## Security Considerations
Please review the following security aspects:

- [ ] No hardcoded passwords or API keys
- [ ] Input validation implemented
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection implemented
- [ ] CSRF protection for state-changing operations
- [ ] Rate limiting considered
- [ ] Authentication/authorization properly implemented
- [ ] No sensitive data in logs
- [ ] Encryption used where appropriate

### Security Review Checklist
- [ ] Threat model reviewed
- [ ] Data flow analyzed
- [ ] Access controls verified
- [ ] Error handling reviewed
- [ ] Logging security reviewed

## Performance Impact
- [ ] No performance impact
- [ ] Performance improvement
- [ ] Minor performance degradation (documented below)
- [ ] Major performance changes (performance tests required)

### Performance Analysis
Brief description of performance impact and testing:

## Backward Compatibility
- [ ] Fully backward compatible
- [ ] Backward compatible with documented migration path
- [ ] Breaking changes (migration guide included)

### Migration Guide
If breaking changes are included, provide migration instructions:

## Related Issues
Closes #issue_number

## Screenshots (if applicable)
Include screenshots or GIFs to demonstrate the changes:

## Additional Context
Add any other context about the pull request here:

### Environment Details
- Python version used for testing:
- Database versions tested:
- Deployment method tested:

### Dependencies
- New dependencies added:
- Dependency updates:
- Security implications of dependencies:

### Known Issues
List any known issues or limitations:

### Future Work
Suggested follow-up work:

---

## Review Checklist for Reviewers

### Code Review
- [ ] Code is readable and well-documented
- [ ] No obvious bugs or security issues
- [ ] Proper error handling implemented
- [ ] Code follows project conventions
- [ ] Tests are comprehensive and passing
- [ ] Performance impact is acceptable

### Security Review
- [ ] Authentication/authorization reviewed
- [ ] Input validation verified
- [ ] Data protection measures adequate
- [ ] Logging does not expose sensitive data
- [ ] Security best practices followed

### Documentation Review
- [ ] Code comments are clear and helpful
- [ ] README updates are accurate
- [ ] API documentation is complete
- [ ] Migration guide is clear (if applicable)

### Testing Review
- [ ] Unit tests cover the changes
- [ ] Integration tests verify functionality
- [ ] Edge cases are tested
- [ ] Test coverage is adequate

## Deployment Readiness
- [ ] Database migrations ready (if applicable)
- [ ] Configuration changes documented
- [ ] Environment variables documented
- [ ] Rollback plan prepared (if applicable)
- [ ] Monitoring and alerting updated

## Approval
- [ ] Technical Lead Approval: @username
- [ ] Security Team Approval: @username (if security changes)
- [ ] Product Owner Approval: @username (if product impact)

### Reviewer Comments
Use this space for reviewer comments and suggestions: