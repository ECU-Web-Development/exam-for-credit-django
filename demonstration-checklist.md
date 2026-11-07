# Student Demonstration Checklist

**Audience: Student.** Use with the [exam instructions](exam_instructions.md). Complete this checklist during the exam; do not bring a prepared solution or prepared request files.

Mark a box only after demonstrating the item. Record the source/configuration, request name, command, or document location supporting each criterion. Each item corresponds to a 2-point practical criterion; partial evidence can receive 1 point. Reuse evidence across topics where appropriate, but demonstrate each distinct requirement.

## Demonstration record

- Application/dependency versions:
- Deployment/start command:
- Web application URL:
- API URL:
- User A / User B / no-role / administrator account labels (no passwords):
- REST Client file location:
- Unit test command:
- Mermaid diagram location:
- Correlation-query location:

## A01. Django architecture and core concepts

- [ ] **A01.1:** Show the project, apps, and responsibilities of settings, routes, and application modules.
- [ ] **A01.2:** Trace a browser mutation through frontend server, JSON API, Redis, worker, and ORM; show a synchronous read.
- [ ] **A01.3:** Show environment-based settings and safe secret injection without displaying secret values.
- [ ] **A01.4:** Show the container's WSGI/ASGI entry point and application server configuration.
- [ ] **A01.5:** Show reused application components and separation of configuration, views, and business logic.

Evidence/results by criterion:

## A02. Models, ORM, and database architecture

- [ ] **A02.1:** Show Task, Notification, and a third related application model; do not count User toward the minimum.
- [ ] **A02.2:** Show migration files, apply them in a container, and display migration state through Django tooling.
- [ ] **A02.3:** Show ORM reads/writes and relationship/deletion behavior; identify only the documented provisioning exceptions.
- [ ] **A02.4:** Demonstrate transaction rollback/integrity protection and database-backed duplicate prevention.
- [ ] **A02.5:** Execute a meaningful QuerySet and show related-loading behavior and a relevant declared index.

Evidence/results by criterion:

## A03. Routing, views, and custom middleware

- [ ] **A03.1:** Show named/namespaced frontend URLs and the API route inventory.
- [ ] **A03.2:** Show DRF view/ViewSet behavior and an example of shared/reusable request handling.
- [ ] **A03.3:** Demonstrate method handling, invalid input, missing objects, and JSON error responses.
- [ ] **A03.4:** Show and execute custom correlation middleware, including its position in the middleware configuration.
- [ ] **A03.5:** Trace a valid correlation ID into responses and worker logs; show safe handling of a malformed incoming ID.

Evidence/results by criterion:

## A04. Templates, frontend integration, and UX

- [ ] **A04.1:** Open `/dashboard/`; show inherited templates, context data, and container-served static assets.
- [ ] **A04.2:** Create, edit, delete, and complete tasks through HTMX without full-page reloads.
- [ ] **A04.3:** Show frontend-server JSON API calls, HTML fragments, and useful form-validation feedback.
- [ ] **A04.4:** Delay worker processing and show pending/retrying, actual success, and terminal failure without false success.
- [ ] **A04.5:** Show a real persisted completion notification and a queued mark-read change; safely render untrusted task text.

Evidence/results by criterion:

## A05. Authentication, authorization, and security

- [ ] **A05.1:** Authenticate through Django and safely show that stored passwords are hashes, not plaintext, including queued account/password commands.
- [ ] **A05.2:** Inspect username/role claims without exposing complete tokens; demonstrate valid, invalid, and expired JWT requests.
- [ ] **A05.3:** Demonstrate all four accounts against frontend and protected API routes: no-role denial, user administration denial, and administrator access.
- [ ] **A05.4:** Demonstrate User A/User B isolation for lists, details, mutations, notifications, and status; reject forged assignments and a queued command whose authorization is revoked.
- [ ] **A05.5:** Show CSRF/XSS protections appropriate to the chosen transport, safe session/token handling, and redacted errors/logs.

Evidence/results by criterion:

## A06. Django admin customization

- [ ] **A06.1:** Show registered domain models and useful list display, filtering, and search.
- [ ] **A06.2:** Show a related-record inline or equivalent useful relationship-oriented display.
- [ ] **A06.3:** Execute a custom operational admin action or show custom form validation.
- [ ] **A06.4:** Demonstrate user/role management using the administrator and denied access using ordinary/no-role accounts.
- [ ] **A06.5:** Show that admin actions, saves/deletes, and application administration cannot bypass queued mutation or permission rules.

Evidence/results by criterion:

## A07. APIs, serialization, and integration

- [ ] **A07.1:** Execute the required token, account, role, task, notification, and operation-status capabilities.
- [ ] **A07.2:** Show serializer validation, controlled ownership fields, and output that excludes passwords/secrets.
- [ ] **A07.3:** Show JSON server-to-server communication, accepted-operation responses, and authorized status lookup.
- [ ] **A07.4:** Demonstrate scoped collection results and pagination or filtering.
- [ ] **A07.5:** Open `.http` files in VS Code REST Client and execute every application endpoint/method with documented expected outcomes and policy/error cases.

Evidence/results by criterion:

## A08. Asynchronous tasks and services

- [ ] **A08.1:** With the worker paused, submit task and administrative mutations; show acceptance but no ordinary domain change until worker execution.
- [ ] **A08.2:** Complete a task; show committed task state and the real notification worker/persisted result.
- [ ] **A08.3:** Enable the controlled failure trigger: fail twice then succeed; separately exhaust the finite retry limit and show failure.
- [ ] **A08.4:** Replay/retry and repeat an identical submission; show no duplicate effect/notification and explicit handling of conflicting key reuse.
- [ ] **A08.5:** Pause workers, enqueue work, restart Redis, resume workers, and show recovered work completing once with truthful status.

Evidence/results by criterion:

## A09. Deployment, environments, and DevOps

- [ ] **A09.1:** Show the five running containers and reach the application/API through their published endpoints.
- [ ] **A09.2:** Show Redis persistence configuration/volume, PostgreSQL persistence, service readiness, and migration/startup steps.
- [ ] **A09.3:** Show safe example environment configuration, static hosting, and deployed errors without debug/secret leakage.
- [ ] **A09.4:** Show structured logs using a documented schema with correlation and operation/task identifiers.
- [ ] **A09.5:** Execute a saved query/filter for one correlation ID showing frontend/API events, worker attempts, and outcome, linked to status responses.

Evidence/results by criterion:

## A10. Testing and quality assurance

- [ ] **A10.1:** Show at least one student-authored unit test and its meaningful assertion.
- [ ] **A10.2:** Run the test in a container and show the command and passing output.
- [ ] **A10.3:** Show deterministic test setup, isolation, and suitable dependency mocking where applicable.
- [ ] **A10.4:** Compare the route/method inventory to executed REST Client requests, including negative authorization and validation cases.
- [ ] **A10.5:** Show repeatable test/demo commands and retained evidence for retries, failure, restart recovery, and permissions.

Evidence/results by criterion:

## A11. Enterprise patterns and maintainability

- [ ] **A11.1:** Show the imported DI framework, actual IoC container, and service registrations.
- [ ] **A11.2:** Show service resolution in frontend/API/worker and one test override or substitution.
- [ ] **A11.3:** Follow a thin handler into single-responsibility business and ORM services.
- [ ] **A11.4:** Open the Mermaid diagram and match it to the deployed containers, protocols, queue, and correlation flow.
- [ ] **A11.5:** Open reproducible deployment/migration/test documentation and explain how another person would run the submission.

Evidence/results by criterion:

## Required live sequences

Use request names from your `.http` files and label evidence with the relevant Axx.y identifiers.

### Authorization and ownership

- [ ] Administrator can reach all application/admin screens and read both users' data.
- [ ] User A and User B can each use the system but cannot reach admin screens/APIs.
- [ ] Each user is denied the other's tasks, notifications, and operation status through direct requests as well as UI.
- [ ] The no-role account is denied protected application access even after successful authentication.
- [ ] Missing, tampered, and expired JWTs are rejected; forged role/ownership inputs do not grant access.
- [ ] A queued operation cannot execute with permissions revoked after acceptance.
- [ ] Every protected endpoint/method has the appropriate policy demonstrated; token issuance is the documented public exception.

### Asynchronous correctness and observability

- [ ] Acceptance is not displayed as completion; pending work has not already changed domain data.
- [ ] Two controlled transient failures lead to bounded retries and eventual success.
- [ ] Persistent failure exhausts retries, records a safe error/correlation ID, and shows terminal UI failure.
- [ ] Duplicate submissions/replays produce no duplicate mutation or notification.
- [ ] Queued work survives Redis restart and completes after workers resume.
- [ ] One saved query/filter reconstructs the correlated request/worker/outcome trace.

## Submission and oral readiness

- [ ] Submit source, dependencies, container configuration, models/migrations, and safe example settings.
- [ ] Submit README/equivalent, Mermaid diagram, `.http` requests/results, unit test/result, and logging schema/query.