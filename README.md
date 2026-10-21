# Payments Service Kit — Clean Architecture Reference

A compact, production‑minded payment layer built around explicit contracts (Protobuf/gRPC), thin HTTP adapters (FastAPI routers), isolated provider integrations, and a disciplined SQLAlchemy persistence tier.

## Core principles

- Contract‑driven design: Protobuf specs define the surface; routers and clients conform to it.
- Separation of concerns: transport, authN/Z, provider logic, and data access live in distinct modules.
- Strong, explicit types: Pydantic, Marshmallow SQLAlchemy, and Enums reduce invalid states.
- Fail‑safe posture: defensive parsing and sanitized error propagation by default.

## Architecture overview

```
Clients → FastAPI Routers (routers/*) → gRPC Stubs (proto.*_pb2_grpc) → Backing Services
                                     ↙                                  ↘
                            SQLAlchemy Persistence (sql/*)      Provider Adapters (actions/*)

Authorization (voter/*) and Utilities (helper/*) cross-cut at the edges
```

## Strength signals in this codebase

- Typed boundaries and validation
  - Pydantic request models and Marshmallow SQLAlchemy schemas for ORM serialization.
  - `t.Literal` and `Enum` usage constrain inputs (e.g., payment method, order direction).
- Provider isolation
  - `actions/authnet.py` wraps Authorize.Net SDK with small, testable methods and env‑scoped config (TEST/LIVE).
- AuthN/Z done right
  - `JWTBearer` guards HTTP routes; voter (`voter/transaction.py`) enforces ownership checks.
- Error hygiene and response shaping
  - gRPC `RpcError` → FastAPI `HTTPException` with scrubbed messages; `MessageToDict` + case conversion utilities ensure consistent payloads.
- Data layer discipline
  - Engine config with `pool_pre_ping`, small pool, `READ COMMITTED` isolation, and `scoped_session` for thread safety.
  - CRUD with safe dynamic ordering, pagination, cross‑table filtering, and date windowing.
- 12‑factor configuration
  - `python‑decouple` pulls DB and provider settings from environment variables.

## Key modules (evidence → capability)

- `routers/transactions.py`, `routers/user.py` → Thin HTTP adapters; typed params; JWT integration; gRPC orchestration.
- `actions/authnet.py` → Encapsulated Authorize.Net flows (`CreateCustomerProfile`, `ChargeCreditCard`, etc.).
- `voter/transaction.py` → Isolated authorization policy (add/edit/view) using logged‑in user context.
- `sql/database.py` → Engine/session setup with pooling, pre‑ping, isolation level, scoped sessions.
- `sql/crud/transactions.py` → Query composition: filters, sorting, pagination, joins (user, invoice).
- `sql/models/users.py`, `sql/schemas/user/user.py` → ORM entity and corresponding schema set.
- `enumerations/user_payment_methods.py` → Enum source of truth for payment types and status lifecycle.
- `proto/transactions/transactions.proto` → Contract for transactions, settlements, refunds, and listing API.

## Notable implementation details

- Defensive parsing: guarded `ast.literal_eval` for stringified detail values in transaction payloads.
- Consistent case conversion: camelCase ↔ snake_case bridging at the API boundary.
- Pagination metadata and stable ordering exposed from the CRUD layer into list responses.

## API quick tour

- Users: create, read by id, update profile, update password, update timezone.
- Transactions: checkout, profile payment, read by id, list with filters, read settlement, refund (full/partial), cancel refund, read refund by transaction id.

## Configuration (env‑first)

- Database: `DB_ENGINE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_URL`, `MYSQL_PORT`, `MYSQL_DB`
- Authorize.Net: `AUTH_ENVIRONMENT`, `AUTH_TEST_*`, `AUTH_LIVE_*`
- Auth and channels: provided via `helper` utilities consumed by routers

## Extending with a new payment provider

1) Add enum entry in `enumerations/user_payment_methods.py`.
2) Implement an adapter in `actions/` mirroring the provider’s SDK with small methods and deterministic returns.
3) Extend the gRPC backend (per `proto/`) and consume via the router using the existing stub pattern.

## Why this stands out

- The code makes illegal states hard to represent through strong typing and enums.
- Boundaries are explicit and enforced by contracts, not convention.
- Operationally safe defaults in the DB layer and error handling reduce production risk.
- Clear extension seams enable adding providers or endpoints without cross‑layer churn.
