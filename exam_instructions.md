# Enterprise Web Application Development Credit-by-Examination Instructions

**Theme: Task Management and Notifications.**

Build and demonstrate a multi-user application using Django, Django REST Framework (DRF), HTMX, PostgreSQL, Redis, and Celery. Demonstrate both working implementation and understanding of the concepts behind your work.

## Exam format and rules

- **Total exam limit: six hours**, including development, deployment, live demonstration, and the oral assessment. Reserve enough of the window to demonstrate and explain your work.
- **Part 1: Practical build and demonstration.** Complete the task-management and notification solution below.
- **Part 2: Post-build oral assessment.** Answer at least 22 questions covering the 11 topic areas: one conceptual question and one scenario question per area. Explain your implementation, diagnose failures, and discuss trade-offs.
- Before the exam, install required tools, including VS Code, Docker Desktop, and VS Code REST Client. Other VS Code extensions are permitted if they are not AI- or search-related.
- You may pre-download dependencies/container images and prepare official-documentation bookmarks.
- **No starter code or prepared exam-specific application code, `.http` requests, or solution configuration is allowed.** Create these during the exam.
- Official product documentation is permitted throughout. **AI tools and search engines are prohibited.** Disable AI assistance in your editor. Documentation access does not authorize generated solutions or copying an existing complete application.
- Choose your container-deployment approach. Application services must run in containers, not on the host. Host-based editors, Docker tooling, REST Client, and browsers are permitted.
- All 11 topic areas require implementation evidence. The criteria below define the depth; not every illustrative sub-bullet in the preparation guide is a separate mandatory feature.

Use the [student demonstration checklist](demonstration-checklist.md). Identifiers such as **A05.3** connect requirements, demonstrations, and rubric criteria.

## Part 1: Required solution

### Container and communication architecture

Deploy five separate containers:

| Container | Responsibility |
| --- | --- |
| HTMX web application | Serve pages/fragments; its server communicates with the Django API using JSON REST. |
| Django/DRF API | Authenticate, authorize, validate, serve JSON reads/status, and enqueue ordinary mutations. |
| Redis | Broker queued work; persist and recover across a container restart. |
| Celery worker | Execute authorized, idempotent mutations and notification processing through the ORM. |
| PostgreSQL | Store application data with persistent storage. |

Normal mutation flow:

```text
Browser/HTMX -> Web application server -> JSON REST API -> Redis -> Celery -> PostgreSQL ORM
```

The browser may exchange HTML with the web application server: HTMX normally swaps HTML fragments. The **web application server exchanges JSON with the Django application API**, then renders appropriate HTML. Sending JSON into an HTML swap target is not a completed frontend integration.

Application API endpoints return JSON bodies, including errors, when a body is returned. Appropriate bodyless responses are permitted. The frontend must not access application tables directly. API reads and worker mutations access PostgreSQL through the ORM.

Django admin is a framework administrative interface, not a JSON application API endpoint; its HTML pages are permitted. Application user/role screens must still follow the frontend-server-to-JSON-API boundary. Django admin must not become a synchronous-write or authorization bypass.

### Data, ownership, and task features

Implement at least **three related application models, excluding Django's User model**:

- **Task:** title (`CharField`), description (`TextField`), creation timestamp (`DateTimeField`), completion status (`BooleanField`), and assigned user (`ForeignKey` to User). Equivalent Python naming conventions are acceptable.
- **Notification:** recipient, source task or durable source-task reference, message, read status, and creation timestamp.
- **Another related application model of your choice.** An operation record linked to its requester and affected task is suitable; another meaningful model is acceptable.

Document task ownership. Ordinary users create/manage only their own tasks, notifications, and operation records; writable assignment/ownership fields must not enable cross-user access. Administrators may assign/manage tasks for any user and access all users' data. Define deletion behavior that does not leave invalid notification/operation references.

Provide `/dashboard/` with task listing, creation, editing, deletion, and completion controls. Update the page using HTMX without full-page reloads. Provide persisted notifications and a way to view and mark them read.

When a task changes from incomplete to complete, enqueue notification processing. Retain a Celery task named `notify_user_of_completion(user_id, task_title, task_details)`; optional task/event/correlation parameters may extend its signature. Dispatch with `.delay()` or `.apply_async()` when headers/options are needed. Publish dependent work only after the task update commits, or use another documented commit-safe approach.

An immediate simulated "Notification received!" alert is not success evidence. Show acceptance/pending first, then completion and notification receipt only when the corresponding work succeeds.

### Mutation, retry, and exception boundaries

All ordinary task, notification, user, and role mutations follow the queue/worker path, including web pages, direct API calls, and administrative paths. Synchronous CRUD with only a notification task is insufficient.

These narrow operations may run synchronously:

- Empty PostgreSQL database/account provisioning during container initialization.
- Schema migrations and initial administrator/account provisioning.
- Authentication bookkeeping, such as login timestamps.
- Operational metadata, enqueue coordination, and diagnostic logs needed to report acceptance/status/retries/failures without recursively queueing the status/logging mechanism.

Exceptions do not permit ordinary domain or subsequent user/role updates to bypass Celery. Ordinary reads remain synchronous.

For each queued mutation:

1. Authenticate, authorize, and validate before acceptance; invalid/forbidden input must not be enqueued.
2. Return acceptance, normally `202 Accepted`, an operation ID, and an authorized status resource.
3. Show pending while queued, executing, or retrying. A retrying substate and attempt count are encouraged.
4. Recheck relevant current permissions/ownership at execution and apply the mutation transactionally.
5. Retry transient failures until success or a documented finite maximum. Distinguish the initial attempt from retries. Validation/authorization failures are not transient.
6. Report terminal success/failure accurately in API and UI. Error responses include a correlation ID.
7. Make retries and repeated submissions idempotent using a stable operation/idempotency ID and database-enforced safeguards. Reusing a key for different input must not silently apply a different mutation.

**Suggested failure demonstration:** implement a disabled-by-default, exam-only trigger that checks the Celery retry count and deliberately raises a transient exception on the first two attempts, before mutation. Then allow success. Restrict the trigger to an administrator or trusted worker configuration. Also show exhausted retries using a controlled persistent failure. Do not use random failures.

Recover queued work after a Redis container restart. Persistence must survive restart, and recovered/replayed work must not duplicate effects or notifications. Document persistence/acknowledgment settings and their limitations; do not claim universal exactly-once delivery.

### Required accounts and access policy

Use Django authentication and create four distinct accounts:

| Account | Role | Required access |
| --- | --- | --- |
| User A | user | Own tasks, notifications, and operation records; no admin screens/APIs. |
| User B | user | Own data, independently isolated from User A. |
| No-role account | none | No application screens or protected application API access. |
| Administrator | admin | All application/admin screens and all users' data. |

Passwords must be hashed, not stored as plaintext or reversible encryption. Use Django password-setting/checking facilities. Salted hashing is recommended; no separate salting score is required.

For queued account creation/password changes, compute the Django-compatible password hash before persisting the command to Redis or an operation record; do not durably queue plaintext passwords. Hashing an unsaved credential is preprocessing, not a synchronous account mutation. Treat password hashes as sensitive data and exclude them from normal API output and logs.

JWTs contain **username and role claims** and are validated on every protected API request: signature, expiry, intended token type, and configured issuer/audience where used. Decoding without validation is insufficient. Account/role changes must not leave unauthorized access through stale claims.

Login/token issuance, such as `POST /api/token/`, cannot require an already-valid JWT or application role. A no-role account may authenticate but receives no protected application access. Initial admin provisioning is a bootstrap exception. Subsequent user creation/registration and role administration require admin authorization and queued mutations. Do not add public self-registration that assigns application roles.

Enforce frontend restrictions and independent API role/ownership checks. Hidden buttons are not authorization. Cover every exposed application endpoint/method, including operation status, notifications, users, and roles. Deny unauthenticated, invalid-token, and no-role requests; deny ordinary-user administration and cross-user access. Use consistent `401`, `403`, or non-disclosing `404` responses as appropriate, without data leakage.

### API contract and REST Client evidence

Implement the capabilities below. Except for `/dashboard/`, you may choose routes; document exact routes/methods. `POST /api/token/` is the recommended token route.

| Capability | Required methods/behavior | Access |
| --- | --- | --- |
| Login/token issuance | `POST`; verify credentials and issue JWT. | Public authentication exception |
| User registration/creation | `POST`; queue account creation without exposing passwords. | admin |
| User administration | List/detail reads; update/delete mutations. | admin |
| Role administration | List/detail reads; create/update/delete and user-role assignment mutations. | admin |
| Task CRUD | List/detail reads; create/update/delete, including completion. | user: own; admin: all |
| Notifications | List/detail reads; mark-read mutation. | user: own; admin: all |
| Operation status | Read pending/retrying/succeeded/failed state and safe errors. | user: own; admin: all |
| Additional exposed endpoints | Document every route/method, contract, and policy. | Explicit appropriate policy |

Use DRF serializers and views/ViewSets. Validate input, control writable ownership fields, handle errors explicitly, and exclude sensitive output fields. Implement scoped lists and at least one documented pagination or filtering feature.

Create `.http` files during the exam and execute them using **VS Code REST Client**. Cover **every exposed application API endpoint and supported method**, recording purpose, expected status/body, role/ownership policy, and execution evidence. Include valid calls and negative authentication, authorization, validation, nonexistent-object, and asynchronous-failure cases. Use variables for tokens/operation IDs; sanitize credentials and live tokens in submitted evidence.

### Structured logging and correlation contract

Implement a consistent machine-readable log schema with at least timestamp, severity, service/component, event/message, and correlation ID. Include operation ID, Celery task ID, retry attempt, and outcome when relevant. Detailed internal exceptions belong in restricted logs; user-facing errors carry safe messages and a correlation ID. Never log passwords, password hashes, complete tokens, or secrets.

The suggested custom middleware validates an incoming correlation ID or generates one, places it in response headers/errors, and passes it through frontend/API calls into Celery messages and operation records. Bound/sanitize untrusted IDs. Show a query/filter that reconstructs one originating request and its processing attempts/outcome. Later status polls may have their own request IDs, but their records must link to the original operation correlation ID.

Choose a queryable logging store and submit its executable correlation query/filter. If application logs are stored in PostgreSQL, write the query using the Django ORM. A schema document or a screenshot without executing the query is not trace evidence.

### Requirements by topic

Each topic has five criteria. Demonstrate working features and relevant source/configuration; oral explanation alone does not fulfill practical criteria.

#### A01. Django architecture and core concepts

- **A01.1:** Separate the Django project and modular apps with clear responsibilities.
- **A01.2:** Implement and trace frontend/API/worker lifecycle and communication boundaries.
- **A01.3:** Configure environment-driven settings and secrets without embedded credentials.
- **A01.4:** Use a container-appropriate WSGI/ASGI entry point/server and explain its role.
- **A01.5:** Demonstrate reusable components and separate configuration, request handling, and business logic.

#### A02. Models, ORM, and database architecture

- **A02.1:** Implement required fields and at least three related non-User models.
- **A02.2:** Generate/apply code-first migrations and show schema state through Django tooling.
- **A02.3:** Use ORM-only application access, justified provisioning exceptions, and sound relationships/deletion behavior.
- **A02.4:** Protect integrity/idempotency with transactions and database constraints.
- **A02.5:** Demonstrate a meaningful filtered/annotated/aggregated QuerySet, relevant index, and efficient related loading.

#### A03. Routing, views, and custom middleware

- **A03.1:** Implement named/namespaced frontend routes and organized API routes.
- **A03.2:** Use appropriate DRF views/ViewSets and reusable view behavior.
- **A03.3:** Handle methods, validation, missing resources, and explicit API errors.
- **A03.4:** Implement custom correlation middleware beyond built-in Django middleware behavior.
- **A03.5:** Propagate correlation IDs through success/error responses and background work; handle invalid incoming IDs safely.

#### A04. Templates, frontend integration, and UX

- **A04.1:** Implement `/dashboard/`, template inheritance, appropriate context, and static assets.
- **A04.2:** Complete task CRUD/completion using HTMX without full-page reloads.
- **A04.3:** Translate API JSON into frontend HTML and show usable form validation.
- **A04.4:** Show truthful pending/retrying/success/failure, including delay and retry exhaustion.
- **A04.5:** Render real notifications and mark-read changes; escape untrusted text and avoid misleading success.

#### A05. Authentication, authorization, and security

- **A05.1:** Implement Django credential verification and demonstrate stored password hashes.
- **A05.2:** Issue/validate JWTs with username/role claims and reject invalid/expired tokens.
- **A05.3:** Demonstrate the four-account matrix on frontend and all protected API paths.
- **A05.4:** Enforce isolation, safe assignment, scoped status/notifications, and current worker authorization.
- **A05.5:** Apply appropriate CSRF, XSS, session/token-handling, and secret-redaction protections.

#### A06. Django admin customization

- **A06.1:** Register domain models and customize list displays, filters, and search.
- **A06.2:** Provide a useful related-record inline or equivalent relationship-oriented admin display.
- **A06.3:** Implement a custom admin action or form validation for a real operational need.
- **A06.4:** Provide admin-only user/role screens and independently protected APIs.
- **A06.5:** Preserve queue, ownership, and role rules in all administration; default synchronous ORM admin writes are not acceptable ordinary mutation paths.

#### A07. APIs, serialization, and integration

- **A07.1:** Implement required API capabilities, methods, and JSON contracts.
- **A07.2:** Use DRF serializers for validation and safe output/writable fields.
- **A07.3:** Demonstrate server-to-server JSON and asynchronous acceptance/status semantics.
- **A07.4:** Implement scoped lists and documented pagination or filtering.
- **A07.5:** Document/execute every endpoint/method in REST Client `.http` files, including policy/error cases.

#### A08. Asynchronous tasks and services

- **A08.1:** Route ordinary domain/user/role mutations through Redis/Celery with only documented exceptions.
- **A08.2:** Commit completion safely and execute persisted notification processing.
- **A08.3:** Demonstrate bounded retries, two transient failures then success, and retry exhaustion.
- **A08.4:** Demonstrate idempotent retry/replay and repeated submission without duplicate effects.
- **A08.5:** Recover queued work after Redis restart with persistence and truthful operation states.

#### A09. Deployment, environments, and DevOps

- **A09.1:** Demonstrate all five containers; no host application substitutes.
- **A09.2:** Persist Redis/PostgreSQL and document startup/readiness/migrations.
- **A09.3:** Configure environment/secrets, static assets, and deployed error behavior.
- **A09.4:** Emit standard structured logs with correlation/operation/task identifiers.
- **A09.5:** Provide/execute a correlation query tracing frontend request, API, worker attempts, and outcomes.

#### A10. Testing and quality assurance

- **A10.1:** Author at least one meaningful automated unit test with an assertion.
- **A10.2:** Execute it in a container; show command and passing result.
- **A10.3:** Use deterministic setup/isolation and mock external dependencies where relevant.
- **A10.4:** Execute REST Client coverage of all documented endpoint/method combinations and negative policies.
- **A10.5:** Retain reproducible test/demo commands and authorization/retry/persistence/failure evidence.

One well-designed test may satisfy A10.1-A10.3. Additional tests are welcome; no coverage-percentage minimum is imposed. Integration tests, CI, and test-data techniques are oral topics, not requirements to add another service.

#### A11. Enterprise patterns and maintainability

- **A11.1:** Use an imported Python DI package with an actual IoC container, not just Django's app registry.
- **A11.2:** Register/resolve all application services through DI in applicable frontend/API/worker processes.
- **A11.3:** Use single-responsibility services and thin handlers with clear business/persistence boundaries.
- **A11.4:** Provide a Mermaid diagram of containers, JSON/HTML boundaries, queue flow, and correlation propagation.
- **A11.5:** Provide readable source and reproducible setup/deployment/migration/test/demo documentation.

Framework-created requests/models/internals need not be replaced with DI services. Additional repositories, DDD abstractions, external integrations, custom user models, or frontend frameworks are not required just to increase complexity.

## Part 2: Post-build oral assessment

Answer conceptual and scenario questions across A01-A11 with follow-up probes about your work. Explain mechanisms rather than naming packages: connect code to request lifecycle, ORM, security, retries, deployment, tests, and maintainability. Locate relevant code and explain failures/alternatives. Official documentation remains permitted. Execution and understanding are assessed separately.

## Required submission and demonstration evidence

Submit:

- Source, dependency manifests, Dockerfiles/build instructions, and deployment configuration created during the exam.
- Models/migrations, safe example configuration without real secrets, and startup/migration instructions.
- README or equivalent covering architecture choices, route/method/policy inventory, account-role labels, mutation exceptions, retry/idempotency, persistence settings, and demo commands.
- Mermaid diagram.
- REST Client `.http` files, expected outcomes, and sanitized execution evidence for every API endpoint/method.
- Unit test source, execution command, and result.
- Structured logging schema and executable correlation query/filter for the chosen store. PostgreSQL application log queries must use the ORM, not a raw SQL console.
- Completed [demonstration checklist](demonstration-checklist.md) with evidence locations/results.

Show required documents, not just describe them. Live-demonstrate authorization/ownership, tasks/notifications, retries/failures, Redis recovery, log traces, and containers. Screenshots alone do not replace live demonstration. Use safe data; do not print passwords or complete bearer tokens.

## Scoring and partial credit

| Assessment | Weight | Raw scoring |
| --- | --- | --- |
| Part 1: Oral understanding | 25% | 22 required questions, 4 points each: 88 raw points |
| Part 2: Practical implementation | 75% | 11 equal areas, 10 points each: 110 raw points |

Each Axx.1-Axx.5 criterion earns 0, 1, or 2 raw points for missing/incorrect, partial, or complete evidence. Each practical topic contributes exactly `75 / 11` percentage points; no weights applied before calculating the total.

```text
Overall score = (oral points / 88 * 25) + (practical points / 110 * 75)
```

Follow-up probes do not add to the denominator. 

## Official references and technical caveats

- [Django migrations](https://docs.djangoproject.com/en/stable/topics/migrations/): model changes propagate into an existing database's schema.
- [Django database setup](https://docs.djangoproject.com/en/stable/intro/tutorial02/): non-SQLite databases need provisioning before migrations.
- [Django passwords](https://docs.djangoproject.com/en/stable/topics/auth/passwords/): use hashing/checking facilities.
- [Django admin](https://docs.djangoproject.com/en/stable/ref/contrib/admin/): default save/delete behavior requires adaptation to this exam's queued-write rule.
- [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/): object checks do not automatically scope all lists or validate creation ownership.
- [HTMX](https://htmx.org/docs/): normally consumes HTML; the frontend server bridges JSON.
- [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html): retry, acknowledgment, and idempotency are distinct concerns.
- [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/): volumes alone are not broker persistence configuration.

Record the versions actually used; no particular framework version is pinned here.
