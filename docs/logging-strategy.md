# DesktopAI Logging Strategy

## Purpose

Logs help diagnose issues, monitor execution, and support debugging.

---

# Log Levels

DEBUG

Detailed development information.

INFO

Normal application events.

WARNING

Unexpected but recoverable situations.

ERROR

Operations that failed.

CRITICAL

Application cannot continue.

---

# Log Files

logs/

- app.log
- scanner.log
- database.log
- ai.log

---

# Logging Rules

Every module should use the centralized logger.

Never print errors directly to the console.

Sensitive user information must never be written to logs.

---

# Example

INFO

Application started.

INFO

Scanning folder:

Downloads

WARNING

Permission denied.

ERROR

Database connection failed.