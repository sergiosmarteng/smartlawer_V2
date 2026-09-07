---
name: system-architecture
description: Design, review and document system architecture, covering system context, components, service boundaries, data flow, communication patterns, queues, event-driven design, caching, consistency, availability, scalability, fault tolerance, rate limiting, deployment topology, observability, disaster recovery, capacity planning and cost trade-offs.
license: MIT
compatibility: opencode
metadata:
  category: architecture
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - system-architecture
  support_for: []
  conflicts_with:
    - ai-system-architecture
---

# System Architecture

Use this skill when designing, reviewing, or documenting the architecture of a software system — including component decomposition, communication patterns, data flow, reliability, scalability, deployment, observability, and cost trade-offs.

The objective is to produce a coherent architecture that balances correctness, reliability, scalability, operational complexity, and cost across every layer of the system.

## When to Use This Skill

Load this skill when the task involves any of the following:

- designing or reviewing system architecture from scratch
- defining service boundaries and component responsibilities
- choosing between synchronous and asynchronous communication
- designing event-driven or queue-based systems
- planning caching strategy, invalidation, and consistency
- evaluating consistency, availability, and partition tolerance trade-offs
- designing for scalability, fault tolerance, and graceful degradation
- implementing rate limiting, throttling, and backpressure
- planning deployment topology, environments, and release strategy
- designing observability (logging, metrics, tracing) and alerting
- planning disaster recovery, backup, and restore procedures
- documenting capacity assumptions, throughput estimates, and cost budgets
- reviewing an existing architecture for reliability or scalability gaps

Do not load this skill for:
- AI-specific architecture decisions (use ai-system-architecture)
- production deployment readiness checks (use production-readiness)
- database schema or query design (use sqlalchemy-postgres)
- API endpoint design (use fastapi-backend or nextjs-frontend as appropriate)
- security architecture review (use security-review)

## System Context

### Scope Definition

- Define the system boundary: what is inside, what is outside, and what integrations exist.
- Document the primary users, actors, and external systems.
- Identify the key architectural drivers: constraints, quality attributes, and top priorities.

### C4 Context Level

- Draw a system context diagram showing the system as a single box.
- Show external actors (users, services, data sources) and their interactions.
- Annotate protocols (HTTP, gRPC, message queue, file transfer) for each interaction.

## Components

### Component Decomposition

Decompose the system into components based on:

| Principle | Description |
|---|---|
| Single responsibility | Each component has one clear purpose |
| Independent deployability | Components can be released independently |
| Data ownership | Each component owns its persistent data |
| Team alignment | Component boundaries match team ownership |
| Failure isolation | A failure in one component does not cascade |

### Component Boundaries

- Define the public API of each component (events, commands, queries).
- Document what each component explicitly does NOT do (negative boundaries).
- Enforce boundaries at the code level — no shared databases, no direct internal calls.

## Service Boundaries

### Bounded Contexts

- Map domains and subdomains following Domain-Driven Design.
- Define the ubiquitous language for each bounded context.
- Identify shared kernel, customer-supplier, and conformist relationships.

### Service Granularity

| Size | Characteristics | Best For |
|---|---|---|
| Monolith | Single deployable, shared data | Small teams, early stage |
| Macroservice | Few large services with clear ownership | Medium teams, established domains |
| Microservice | Many small services, each owning data | Large teams, independent scaling needs |

### Anti-Patterns

- Shared database across services (creates coupling).
- Too-fine granularity (increases coordination cost).
- Circular dependencies between services.
- Implicit contracts (document all service APIs explicitly).

## Data Flow

### Flow Patterns

- Request-response: caller waits for a response. Simple, synchronous.
- Fire-and-forget: caller sends and continues. No response expected.
- Event broadcast: one producer, many consumers. Loose coupling.
- Stream processing: continuous data flow with state. Complex but powerful.

### Data Flow Documentation

- Draw data flow diagrams for each major user journey.
- Show data at rest (databases, caches, object storage) and data in transit (network, queue).
- Annotate data volume, frequency, and latency requirements.
- Identify data transformation points and their ownership.

## Synchronous vs. Asynchronous Communication

### Decision Matrix

| Factor | Favor Sync | Favor Async |
|---|---|---|
| Response needed immediately | Yes | No |
| Caller can wait | Yes (low latency) | No (long processing) |
| Downstream reliability | High | Unreliable or variable |
| Traffic pattern | Predictable | Bursty or unpredictable |
| Consistency requirement | Strong | Eventual |

### Sync Communication

- Use for queries and commands that need immediate confirmation.
- Set timeouts at every layer — client, API gateway, service.
- Implement circuit breakers to protect downstream services.
- Use retries with exponential backoff for transient failures.

### Async Communication

- Use for long-running operations, cross-service notifications, and event propagation.
- Choose between message queues (point-to-point) and event streams (pub-sub).
- Design for at-least-once delivery — make consumers idempotent.
- Monitor queue depth, consumer lag, and processing time.

## Queues

### Queue Types

| Type | Characteristics | Examples |
|---|---|---|
| Point-to-point | One message consumed by one worker | RabbitMQ, SQS, Redis |
| Pub-sub | One message consumed by many subscribers | Kafka, SNS, Redis Pub/Sub |
| Stream | Ordered log of messages with replay | Kafka, Pulsar, Kinesis |

### Queue Design Considerations

- Set message TTL to prevent stale messages from building up.
- Configure dead-letter queues for messages that exceed max retries.
- Monitor queue depth and consumer lag — alert on sustained growth.
- Size queues for peak load plus headroom (2x-3x expected peak).
- Make message processing idempotent — the same message may be delivered more than once.

## Event-Driven Systems

### Event Types

| Event | Description | Example |
|---|---|---|
| Domain event | Something happened in the domain | "OrderPlaced" |
| Integration event | Cross-service notification | "PaymentCompleted" |
| Command | A request to perform an action | "SendEmail" |
| CQRS command | Write-side command in CQRS | "UpdateUserProfile" |

### Event Design Principles

- Events are facts — they describe something that already happened.
- Event schema must be versioned and backward-compatible.
- Producers publish events; consumers interpret them independently.
- Store events in an append-only log for audit and replay.

### Event Sourcing

- Store state changes as a sequence of events, not the current state.
- Rebuild state by replaying events from the beginning.
- Use snapshots to bound replay time.
- CQRS naturally pairs with event sourcing but is not required.

## Caching

### Cache Types

| Type | Location | Use Case | Eviction |
|---|---|---|---|
| Local (in-memory) | Application process | Hot data, low latency | LRU, TTL |
| Distributed | Redis, Memcached | Shared across instances | LRU, TTL, LFU |
| CDN | Edge network | Static assets, API responses | TTL, purge |
| Database query cache | Database server | Repeated queries | Update-based invalidation |
| HTTP cache | Browser, reverse proxy | GET responses | Cache-Control headers |

### Caching Strategy

| Strategy | Reads | Writes | Best For |
|---|---|---|---|
| Cache-aside | Check cache, miss → load from DB | Write to DB, invalidate cache | Read-heavy workloads |
| Read-through | Cache loads from DB on miss | Write to DB | Transparent caching |
| Write-through | Cache and DB updated together | Write to cache first | Consistency-critical |
| Write-behind | Write to cache, async write to DB | Fast writes | Write-heavy with tolerance |

### Cache Invalidation

- TTL-based: simplest, tolerate stale data for TTL duration.
- Event-based: invalidate on data change event.
- Version-based: use version keys and compare on read.
- Pattern-based: invalidate all keys matching a prefix.

### Cache Pitfalls

- Thundering herd: many requests miss cache simultaneously (mitigate with mutex or early refresh).
- Cache stampede: expired key, all requests recompute (mitigate with probabilistic early expiration).
- Stale data: cache returns outdated data (mitigate with short TTL or event-driven invalidation).

## Consistency

### Consistency Models

| Model | Guarantee | Performance | Use Case |
|---|---|---|---|
| Strong | All reads see latest write | Lower latency | Financial transactions |
| Eventual | Reads eventually see latest write | Higher throughput | Social feeds, analytics |
| Causal | Related operations seen in order | Moderate | Collaborative editing |
| Read-your-writes | Writer sees own writes | Moderate | User-facing apps |

### CAP Theorem Trade-Offs

- Partition tolerance is non-negotiable in distributed systems.
- Choose between consistency (CP) and availability (AP) during partitions.
- Design the system so that CP vs AP decisions are made per-operation, not globally.

### Consistency in Practice

- Use database transactions for strong consistency within a single service.
- Use idempotency keys for cross-service operations.
- Use sagas for multi-service transactions — compensate on failure.
- Use outbox patterns to guarantee at-least-once event publication.

## Availability

### Availability Levels

| Level | Uptime | Downtime/Year | Common Name |
|---|---|---|---|
| 99% | 3.65 days | "Three nines" | Internal tools |
| 99.9% | 8.76 hours | "Three nines" | Many SaaS products |
| 99.99% | 52.56 minutes | "Four nines" | Critical infrastructure |
| 99.999% | 5.26 minutes | "Five nines" | Telecom, payments |

### Achieving Availability

- Eliminate single points of failure at every layer.
- Deploy across multiple availability zones or regions.
- Use health checks and auto-remediation (restart, replace).
- Implement graceful degradation — partial functionality is better than none.
- Design for planned downtime: rolling updates, blue-green deployment.

## Scalability

### Scaling Patterns

| Pattern | Direction | When |
|---|---|---|
| Vertical scale up | More resources (CPU, RAM) on existing instances | Simple, but has hardware limits |
| Horizontal scale out | More instances behind a load balancer | Elastic, but requires stateless design |
| Sharding | Partition data across instances | Data exceeds single instance capacity |
| CQRS | Separate read and write paths | Different read/write volume patterns |

### Stateless Design

- Store session state in a distributed cache, not on the application instance.
- Any instance must be able to serve any request.
- Use sticky sessions only when unavoidable — they complicate failover.

### Backpressure

- When the system cannot keep up, signal the caller to slow down.
- Implement via: queue depth limits, HTTP 429 with Retry-After, TCP flow control.
- Dropping requests is better than unbounded queuing and eventual crash.

## Fault Tolerance

### Fault Handling Patterns

| Pattern | Purpose | Implementation |
|---|---|---|
| Retry | Recover from transient failures | Bounded retries with exponential backoff + jitter |
| Circuit breaker | Stop calling a failing dependency | Track failure rate, open circuit, half-open probe |
| Bulkhead | Isolate failures to one pool | Separate thread pools or connection pools per dependency |
| Timeout | Bound waiting time | Per-call timeout that fails fast |
| Fallback | Provide degraded response | Default value, cached response, alternative service |

### Graceful Degradation

- Define what partial functionality is acceptable when a dependency is unavailable.
- Disable non-critical features and return a degraded experience.
- Log every degradation event for capacity planning.

### Failure Modes to Design For

| Failure Mode | Symptom | Mitigation |
|---|---|---|
| Dependency slow | Increased latency chain-wide | Timeouts, circuit breakers |
| Dependency down | Requests fail | Fallback, cached response, degrade |
| Resource exhaustion | OOM, CPU spike | Limits, bulkheads, autoscaling |
| Network partition | Services unreachable | CAP trade-off, retry, degrade |
| Data corruption | Wrong results | Checksums, validation, backups |

## Rate Limiting

### Rate Limiting Algorithms

| Algorithm | Characteristics | Best For |
|---|---|---|
| Token bucket | Bursty but bounded | General purpose |
| Leaky bucket | Smooths traffic | Steady throughput |
| Fixed window | Simple, can burst at window boundary | Simple rate limits |
| Sliding window | Smooth, more accurate | Precise rate limits |
| Concurrency limit | Max in-flight requests | Protecting resources |

### Rate Limiting Placement

- **API gateway**: global rate limit per user/IP/tenant.
- **Service**: per-endpoint and per-user rate limits.
- **Database**: connection pool limits, query rate limits.
- **Downstream**: protect external APIs from over-calling.

### Rate Limiting Response

- Return HTTP 429 with a `Retry-After` header.
- Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
- Log rate-limited requests for abuse detection.

## Deployment Topology

### Environment Strategy

| Environment | Purpose | Configuration |
|---|---|---|
| Development | Local development | Minimal resources, debug mode |
| Staging | Pre-production validation | Production-like resources and data |
| Production | Live traffic | Full redundancy, monitoring |
| DR | Disaster recovery | Standby infrastructure |

### Deployment Patterns

| Pattern | Risk | Traffic Cutover | Rollback |
|---|---|---|---|
| Rolling update | Low | Gradual per-instance | Revert deployment |
| Blue-green | Low | Instant at load balancer | Switch back to blue |
| Canary | Very low | Percent-based | Stop canary |
| Feature flag | Minimal | Per-user toggle | Disable flag |

### Infrastructure as Code

- All infrastructure defined in version-controlled code (Terraform, CloudFormation, Pulumi).
- Environments are provisioned from the same code with different variables.
- No manual infrastructure changes — every change goes through code review and CI.

## Observability

### Three Pillars

| Pillar | What | Example Tools | Alert Condition |
|---|---|---|---|
| Logging | Discrete events | ELK, Loki, CloudWatch | Error log rate spike |
| Metrics | Aggregated measurements | Prometheus, Datadog | p99 latency > 500ms for 5 min |
| Tracing | Request flow across services | Jaeger, Zipkin, OpenTelemetry | Trace waterfall shows slow span |

### Logging

- Log at the boundary of every service (request received, response sent).
- Include correlation ID in every log entry.
- Log errors with stack traces and context.
- Do not log secrets, PII, or sensitive data.
- Use structured logging (JSON) for automated analysis.

### Metrics

| Category | Example Metrics |
|---|---|
| Traffic | Requests per second, active connections |
| Latency | p50/p95/p99 response time |
| Errors | Error rate by status code and component |
| Saturation | CPU, memory, disk, connection pool usage |

### Tracing

- Trace every external request across service boundaries.
- Propagate trace context via HTTP headers or message metadata.
- Sample traces to control cost (head-based or tail-based sampling).
- Use traces for latency breakdown and dependency analysis.

### Alerting

- Alert on symptoms (user-visible problems), not causes (internal metrics).
- Define runbooks for every alert — what to check and how to respond.
- Set alert thresholds high enough to avoid noise, low enough to catch real issues.
- Use alert fatigue as a signal to tune or remove rules.

## Disaster Recovery

### Recovery Objectives

| Metric | Definition | Target |
|---|---|---|
| RTO (Recovery Time Objective) | Maximum acceptable downtime | 1 hour (example) |
| RPO (Recovery Point Objective) | Maximum acceptable data loss | 15 minutes (example) |
| MTD (Maximum Tolerable Downtime) | Total acceptable outage duration | 4 hours (example) |

### Backup Strategy

| Data | Backup Frequency | Retention | Restore Test |
|---|---|---|---|
| Database | Full daily + WAL streaming | 30 days | Quarterly |
| Object storage | Cross-region replication | Indefinite | Annually |
| Configuration | Version-controlled | Forever | On every restore test |

### Recovery Plan

- Document step-by-step recovery procedures for each failure scenario.
- Test recovery at least annually — verify RTO and RPO targets are met.
- Automate recovery where possible (infrastructure as code, database restore scripts).
- Practice failure scenarios through game days and chaos engineering.

## Capacity Assumptions

### Capacity Planning

- Document expected throughput, data volume, and concurrency for the next 6-12 months.
- Estimate peak load (2-3x average for most systems).
- Plan for headroom (50% utilization target under normal load).
- Model growth rate and plan scaling triggers.

### Throughput Estimation

| Component | Current | 6-Month Projection | 12-Month Projection |
|---|---|---|---|
| API requests/sec | 100 | 300 | 1,000 |
| Database writes/sec | 50 | 150 | 500 |
| Storage growth/month | 10 GB | 30 GB | 100 GB |
| Concurrent users | 1,000 | 3,000 | 10,000 |

## Cost Trade-Offs

### Architecture Cost Factors

| Decision | Cost Impact | Operational Impact |
|---|---|---|
| Microservices vs. monolith | Higher infra, lower dev at scale | Higher ops complexity |
| Managed services vs. self-hosted | Higher variable cost | Lower ops burden |
| Multi-region deployment | 2-3x infrastructure cost | Higher availability |
| Reserved vs. on-demand instances | Lower cost with commitment | Less flexibility |
| Synchronous vs. async | Lower infra cost | Higher coupling risk |

### Cost Control

- Tag all resources with cost center, environment, and owner.
- Set budgets and alerts on unexpected spend.
- Rightsize instances based on actual utilization metrics.
- Use auto-scaling to match capacity to demand.
- Regularly review and decommission unused resources.

### Cost vs. Quality Trade-Offs

| Quality Attribute | Cost to Achieve | Cost of Ignoring |
|---|---|---|
| 99.99% availability | ~2x vs 99.9% | Revenue loss during downtime |
| Multi-region DR | ~2-3x infrastructure | Data loss during region failure |
| High performance (p99 < 100ms) | ~1.5x vs p99 < 500ms | User dissatisfaction |
| Comprehensive observability | Engineering time to set up | Longer incident resolution |

## Required Review Output

When reviewing a system architecture, produce this summary:

```text
System:
[Name, purpose, and primary stakeholders.]

System context:
[Scope, external actors, integration protocols.]

Components:
[List of components with responsibilities and boundaries.]

Data flow:
[Major data flows, volumes, latency requirements.]

Communication:
[Sync vs. async decisions, queue types, event design.]

Consistency & availability:
[Consistency model, availability target, CAP trade-offs.]

Scalability:
[Scaling strategy, stateless design, backpressure.]

Fault tolerance:
[Retry, circuit breaker, bulkhead, timeout, fallback, degradation plan.]

Rate limiting:
[Algorithms used, placement, response format.]

Caching:
[Cache types, invalidation strategy, eviction policy.]

Deployment:
[Environments, deployment pattern, IaC approach.]

Observability:
[Logging, metrics, tracing, alerting runbooks.]

Disaster recovery:
[RTO, RPO, backup strategy, recovery plan, test schedule.]

Capacity:
[Current and projected throughput, storage, concurrency.]

Cost:
[Key cost drivers, budgets, trade-offs documented.]

Issues found:
[List each finding with severity, location, impact, and recommended fix.]

Recommendations:
[Prioritized list of improvements with expected impact.]
```

## Completion Criteria

A system architecture review is complete only when:

- the system context is documented with scope, actors, and external dependencies
- components are decomposed with clear responsibilities and boundaries
- data flow is documented for each major user journey
- communication patterns (sync vs. async) are chosen with rationale
- queue and event-driven design follow at-least-once and idempotency principles
- caching strategy includes invalidation and eviction policy
- consistency and availability trade-offs are documented
- scalability strategy addresses stateless design and backpressure
- fault tolerance patterns (retry, circuit breaker, bulkhead, timeout, fallback) are defined
- rate limiting algorithm and placement are specified
- deployment topology and release pattern are documented
- observability covers logging, metrics, tracing, and alerting
- disaster recovery objectives (RTO, RPO) and recovery plan exist
- capacity assumptions are documented with projections
- cost trade-offs are evaluated with key drivers identified
- all findings are documented with severity, location, impact, and recommendation
