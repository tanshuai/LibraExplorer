# Legacy service acceptance

Run `python -m pytest integration/legacy_api_check.py` explicitly when the original MoveOnLibra service is available. This remains a real HTTP integration check of the existing testnet and proxy destination. The current destination does not resolve, so service acceptance remains blocked; CI must not pretend it verified the remote service.

Ordinary CI uses a local HTTP fixture to verify request headers, response parsing, actual read timeouts, and application error handling. It does not require a retired external API to test these client contracts.
