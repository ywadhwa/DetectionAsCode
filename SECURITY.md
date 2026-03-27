# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email your findings to the repository maintainer (see GitHub profile for contact)
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Resolution**: We aim to resolve critical issues within 7 days
- **Disclosure**: We will coordinate with you on public disclosure timing

### Scope

This security policy applies to:
- Sigma rule validation and conversion logic
- Pipeline configurations and scripts
- Web UI components
- Backend adapters (ADX, Elasticsearch, Splunk)

### Out of Scope

- Vulnerabilities in third-party dependencies (report these upstream)
- Security issues in Sigma rules themselves (these are detection logic, not code)
- Issues requiring physical access or social engineering

## Security Best Practices for Users

When using this repository:

1. **Never commit secrets**: Use environment variables or secret managers
2. **Review rules before deployment**: Validate Sigma rules match your environment
3. **Use least privilege**: Configure backend connections with minimal required permissions
4. **Keep dependencies updated**: Regularly update Python packages

## Acknowledgments

We appreciate security researchers who help improve this project. Contributors who report valid vulnerabilities will be acknowledged (with permission) in our release notes.
