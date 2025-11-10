## Prometeo — Assistant guidance for contributors and AI agents

This file contains concise, project-specific directions to help an AI coding agent be productive in this repository.

Keep answers short and concrete. Prefer small, safe edits and tests-first verification.

1) Big-picture architecture (what to assume)
- Domain-Driven Design (DDD) structure. The `domain/` package holds the model: entities, value objects, aggregates, services, specifications and domain events. Example: `domain/aggregates/factura_aggregate.py` (aggregate root behavior) and `domain/services/inventario_service.py` (domain service for FIFO inventory operations).
- Infrastructure is under `infraestructure/persistence/` (note the folder name spelling). It contains persistence and integration adapters: `sql_repository.py`, `event_store_sql.py`, `rabbitmq_publisher.py`, `snapshot_sql.py` and projection handlers.
- Application layer is light: `application/main.py` shows example wiring of repos/services to run a scenario.
- Tests under `tests/` include both unit and integration tests. Integration tests may expect external services (RabbitMQ, MySQL).

2) Dataflow / event flow
- Aggregates (e.g., `FacturaAggregate`) validate invariants and emit domain events (`domain/events/*`).
- Events are persisted by an Event Store (`infraestructure/persistence/event_store_sql.py`) and used by projections/projection handlers found in `infraestructure/persistence/projection_handler.py` and `projection_sql.py`.
- For cross-process messaging the RabbitMQ publisher lives at `infraestructure/persistence/rabbitmq_publisher.py` and publishes JSON messages with routing keys like `facturacion.facturaemitida` (see `FacturaAggregate.emit` and `RabbitMQPublisher.publish`).

3) Project-specific conventions and patterns
- Language: Python 3 (dataclasses, Decimal, typing are used across code). Keep numeric monetary values as `decimal.Decimal` and convert to float only for serialization.
- Naming: Files and symbols often use Spanish domain terms (`factura`, `nota_credito`, `inventario`, `lote`, etc.). Follow existing names and the ubiquitous language.
- Aggregates: root classes expose `emit`/`crear_nueva`/`to_snapshot`/`from_snapshot`. Use these methods when creating or replaying state.
- Specifications pattern: validation is implemented in `domain/specifications/*`. Prefer reusing existing specifications (e.g., `factura_specifications.StockSuficienteParaFactura`) rather than inlining validation logic.

4) Integration and external dependencies
- RabbitMQ: integration tests (e.g., `tests/test_event_publisher_integration.py`) open real connections to `localhost`. Start a local RabbitMQ (default guest/guest) or mock `pika` for CI/unit runs.
- SQL / Event store: `event_store_sql.py` uses SQLAlchemy and expects a database URL. The sample `sql_repository.py` uses `mysql+mysqlconnector://user:pass@localhost/db_name`. For local runs, provide a test database or mock sessions.
- Python packages referenced: `sqlalchemy`, `pika`, `mysql-connector-python` (or `mysqlclient`), `decimal`. Add a `requirements.txt` if missing; tests run via Python's unittest framework.

5) Helpful run / debug commands (discoverable from code)
- Run unit tests: python -m unittest discover -v
- Run a single test module: python -m unittest tests.test_event_publisher_integration (note: this test expects RabbitMQ running and will block if not available)
- Quick interactive example: open `application/main.py` to see how services and repositories are wired.

6) Files to inspect first for most tasks
- `domain/aggregates/factura_aggregate.py` — aggregate/event emission patterns
- `domain/services/inventario_service.py` — FIFO inventory logic (business rules callers)
- `domain/specifications/` — validation rules used across aggregates/services
- `infraestructure/persistence/event_store_sql.py` — how DomainEvent objects are serialized and stored
- `infraestructure/persistence/rabbitmq_publisher.py` — publisher contract and expected message shape
- `tests/` — concrete examples of usage and edge-case tests

7) Example snippets (follow these shapes)
- Emitting events from an aggregate (see `FacturaAggregate.emit`): append domain events to a `_pending_events` list, include event_version and serialized `data`.
- Publishing: publisher expects a DomainEvent with `.event_type`, `.data`, `.occurred_on` and optionally `.event_id`; publisher serializes to JSON and uses routing key `facturacion.<lowercase event_type>`.

8) Common pitfalls to avoid
- Directory name mismatch: some files import `infrastructure` while the repository folder is `infraestructure` — double-check imports before refactors.
- Integration tests assume external services; do not run them in CI without starting dependencies or marking them as integration-only.
- Avoid converting Decimal to float for domain math; only convert at serialization boundaries.

9) When making changes
- Small, focused commits. Add/adjust unit tests for behavior changes. Run `python -m unittest` and fix failures before pushing.
- If adding persistence mappings, update `infraestructure/persistence/sql_repository.py` and add migrations or table-creation calls (EventStore creates its table on init).

10) If you need more context
- Read `README.md` — it contains design notes and DDD rationale used in this repo.
- Ask for clarification about environment variables and CI expectations (RabbitMQ/MySQL URLs, credentials) before changing integration tests.

---
If any section is unclear or you want more detail on a specific area (tests, event store schema, or wiring examples), tell me which file to expand and I will update this guidance.
