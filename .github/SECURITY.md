# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x | ✅ Yes |
| 0.x | ❌ No |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not open a public issue**.

Instead, please email: **bishek@example.com** with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within **48 hours** and a fix will be released as soon as possible.

## Security Considerations for Pico W Deployments

- Always set `debug=False` in production — debug mode exposes internal code
- Never commit `config.py` with Wi-Fi credentials to version control
- Use `httponly=True` and `samesite="Strict"` for session cookies
- Restrict CORS `origins` to known domains in production
- The Pico W has no TLS support — use a reverse proxy for HTTPS
