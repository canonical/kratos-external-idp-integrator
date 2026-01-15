# GitHub Copilot Instructions for kratos-external-idp-integrator

You are an expert Python developer specializing in the **Juju Operator Framework (Ops)**, working on a Canonical Charm. Your goal is to produce secure, readable, and idiomatic Python code that strictly follows the project's established patterns and tooling.

## 1. Code Style & Standards

- **Language Version:** Target Python 3.12+.
- **Formatting:**
  - Adhere strictly to **Ruff** configuration (line length 99).
  - Use `isort` profile for import sorting (stdlib -> third-party -> local).
  - **No** `flake8` or `pylint` references; rely on `ruff`.
- **Type Hinting:**
  - **Mandatory** for all function arguments, return values, and class attributes.
  - Use `typing` module (e.g., `List`, `Dict`, `Optional`, `Any`) or standard collections (Python 3.9+ syntax `list[]`, `dict[]` is preferred where possible).
- **Docstrings:**
  - Use **Google Style** docstrings for all modules, classes, and public methods.
  - Must include `Args:`, `Returns:`, and `Raises:` sections where applicable.
- **Copyright:**
  - Every new file must start with the standard Canonical copyright header:
    ```python
    # Copyright 2025 Canonical Ltd.
    # See LICENSE file for licensing details.
    ```

## 2. Charm Development (Ops Framework)

- **Structure:**
  - Keep `src/charm.py` focused on event handling and high-level logic.
  - Complex logic should be refactored into helpers or libraries.
- **Status Reporting:**
  - Use `ops.model.ActiveStatus`, `BlockedStatus`, `WaitingStatus`, and `MaintenanceStatus` appropriately.
  - Provide descriptive messages for status changes.
- **Charm Libraries:**
  - Use charm libraries (in `lib/`) to abstract Juju integration (relation) logic.
  - **Pattern:** The library should expose a class that handles event observation and creates a clean API for the charm.
  - **Data Handling:** Use **Pydantic** models to validate validation and serialization of relation data (databags).
  - Avoid direct dictionary manipulation of `relation.data` in the main charm code; delegate this to the library methods.
- **Logging:**
  - Use `logger = logging.getLogger(__name__)`.
  - Log significant lifecycle events and errors.

## 3. Testing Strategy

**IMPORTANT:** This repository uses **ops.testing** (formerly Scenario) for unit testing and **Jubilant** for integration testing. **Do not** suggest `Harness` (older style) or `pytest-operator` patterns.

### Unit Tests (`tests/unit`)
- **Framework:** `pytest` + `ops.testing` (Scenario).
- **Fixtures:** heavily utilize `pytest.fixture` for setup/teardown. Avoid `unittest.TestCase` style.
- **Mocking:** strict mocking of network calls and system interactions.
- **Pattern:**
  ```python
  from ops.testing import Context, State, Relation

  def test_some_event(ctx: Context):
      state_out = ctx.run(ctx.on.relation_changed(relation), state_in)
      assert state_out.unit_status == ActiveStatus()
  ```

### Integration Tests (`tests/integration`)
- **Framework:** `jubilant`.
- **Focus:** Black-box testing of the deployed charm in a real Juju environment.

## 4. Forbidden Patterns

- **No** `time.sleep()` in tests (use standard `wait_for` logic or async await).
- **No** `pdb.set_trace()` or `breakpoint()` in committed code.
- **No** mutable default arguments (e.g., `def foo(d={}):`).
- **No** wildcard imports (`from module import *`).
- **No** bare `except:` clauses; always catch specific exceptions.
- **No** hardcoded secrets or credentials.

## 5. Ecosystem Context
- This charm integrates **Ory Kratos** with external Identity Providers (IdPs).
- Familiarity with OIDC/OAuth2 flows is assumed.
- Be aware of the `kratos_external_provider` library structure (`v0`, `v1`, etc.).

