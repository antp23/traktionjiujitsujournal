"""BJJ Tracker backend (v2 rebuild).

Layered FastAPI application: config → db → models/schemas → services → api.
The HTTP contract and SQLite schema are identical to v1; see
docs/rebuild/DEVELOPMENT_PLAN.md for the architecture rationale.
"""
