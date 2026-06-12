# Web token refresh (P1)

A JWT expiry currently drops the monitor to the login screen. Silently re-mint from stored credentials (or a refresh token) so a left-open dashboard keeps working.

## Surface
web + server.