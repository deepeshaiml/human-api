# Security notes

This is a hackathon prototype and is not production-ready or security-certified. Use synthetic data only. Keep demo mode bound to localhost.

In short: the owner's consent does not give the requester access to files. The demo checks the requester's file access before search and again before showing saved evidence. The [reader guide](docs/READER_GUIDE.md) explains the terms and gives a simple example.

Security design and known gaps are documented in [the security architecture](docs/SECURITY_ARCHITECTURE.md). Report suspected vulnerabilities privately to the repository owner; do not include secrets or real employee content in issues.
