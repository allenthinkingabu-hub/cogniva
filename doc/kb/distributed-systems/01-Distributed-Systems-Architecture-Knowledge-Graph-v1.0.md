# Distributed Systems Architecture Knowledge Graph (v1.0)

> **Knowledge Base Scope**: Cogniva Infrastructure & Distributed Systems Theory Core Framework  
> **Document Code**: `DIST-SYS-ARCH-KG-v1.0-EN`  
> **Corresponding Chinese Version**: [01-分布式系统架构体系全景知识图谱-v1.0.md](./01-分布式系统架构体系全景知识图谱-v1.0.md)  
> **Production Real-World Implementation**: [Hook 1 on_run_load Admission Barrier & Distributed Lease Implementation](../agent/deep-dive/topics/01-lifecycle-hooks/08-Hook1-on_run_load-准入屏障与分布式租约落地实战.md) | [Zombie Run Mechanism & Tombstone Verification Appendix](../agent/deep-dive/topics/01-lifecycle-hooks/appendix/08-附录-僵尸任务产生机理与墓碑机制-STE100规范解构.md)

---

## 0. Layered Topology of the Knowledge Graph (Level 0 Overview)

```
                     [Level 0: Distributed Systems Engineering Overview]
                                             │
 ┌───────────────────────┬───────────────────┴───┬───────────────────────┐
 ▼                       ▼                       ▼                       ▼
[Pillar I: Network Fabric][Pillar II: Consensus]  [Pillar III: Runtime]   [Pillar IV: Storage]
(Bitstream Transport)    (Theoretical Foundation)(★ Execution & Control) (Replication & Disk)
                                                 │
                                                 ▼
               ┌─────────────────────────────────┴─────────────────────────────────┐
               ▼                                 ▼                                 ▼
   [Level 2.1: Capacity & Volume]      [Level 2.2: State Isolation]      [Level 2.3: Lifecycle & Time]
    ├── Distributed Flow Control        ├── Distributed Concurrency Ctrl  ├── Distributed Lifecycle Ctrl
    └── Adaptive Load Shedding          └── Distributed Mutual Exclusion  └── Distributed Saga Orchestration
```

---

## 1. Top-Level Structure: Six Foundational Pillars (Level 1)

In classical computer systems science (Tanenbaum & Van Steen, 2017; Kleppmann, 2017), distributed systems consist of **Six Foundational Pillars**:

```
                       [Six Foundational Pillars of Distributed Systems (Level 1)]
                                                    │
  ┌──────────────────┬──────────────────────────────┼──────────────────┬──────────────────┐
  ▼                  ▼                              ▼                  ▼                  ▼
Pillar I           Pillar II                      Pillar III         Pillar IV          Pillars V & VI
Networking         Consensus & Consistency        Runtime Control    Storage & Replic.  Resilience & Obs.
```

### 1. Pillar I · Distributed Networking & RPC Fabric
* **Responsibility**: Establishes reliable communication links, data serialization, and message routing across physical nodes.
* **Core Components**:
  * **Transport Protocols**: TCP, QUIC, HTTP/2, gRPC.
  * **Serialization Engines**: Protocol Buffers, Avro, JSON, FlatBuffers.
  * **Distributed Message Buses**: Kafka (Append-only partitioned log), RabbitMQ (AMQP), Pulsar (Tiered storage).
  * **Communication Topologies**: Peer-to-Peer Gossip protocols, Service Mesh (Envoy Sidecar data planes).

### 2. Pillar II · Distributed Clocks, Consensus & Consistency Foundation
* **Responsibility**: Guarantees deterministic state ordering and replicated state machines without shared physical memory.
* **Core Components**:
  * **Distributed Clocks**: Lamport Logical Clocks (partial order "happens-before"), Vector Clocks (causal order), TrueTime (GPS + atomic clocks), Hybrid Logical Clocks (HLC).
  * **Strong Consensus Protocols**: Paxos, Multi-Paxos, Raft, Zab (ZooKeeper).
  * **Byzantine Fault Tolerance**: Practical Byzantine Fault Tolerance (PBFT).
  * **Consistency Spectrum**: Strict Serializability (1SR), Linearizability, Causal Consistency, Eventual Consistency.

### 3. Pillar III · Distributed Computing Runtime & Scheduling Control
* **Responsibility**: **[★ Core Governance Domain]** Controls concurrency, capacity limits, state mutual exclusion, and task lifecycles during distributed workload execution (e.g., AI Agent Harness, cluster schedulers).
* **Six Peer Control Paradigms**: Distributed Flow Control, Distributed Concurrency Control, Distributed Lifecycle Control, Mutual Exclusion & Leader Election, Job Scheduling & Sharding, and Distributed Saga Orchestration (detailed in Section 2).

### 4. Pillar IV · Distributed Storage & Data Management
* **Responsibility**: Horizontal data partitioning, high-availability multi-replica replication, and persistent retrieval.
* **Core Components**:
  * **Storage Engines**: LSM-Tree (Write-optimized, e.g., RocksDB), B+ Tree (Read-optimized).
  * **Partitioning Strategies**: Consistent Hashing, Range Partitioning.
  * **Replication Models**: Single-Leader synchronous replication, Semi-Synchronous replication, Quorum consensus replication (NWR).
  * **Distributed Caches**: Redis Cluster, Memcached, Cache-Aside consistency models.

### 5. Pillar V · Distributed Fault Tolerance & Resilience Engineering
* **Responsibility**: Guarantees continuous availability and self-healing under network partitions, process pauses, and node crashes.
* **Core Components**:
  * **Bulkhead Isolation**: Physical isolation of resource pools to stop cascading failures.
  * **Circuit Breakers**: Self-healing finite state machines (Closed / Open / Half-Open).
  * **Timeouts & Retries**: Exponential Backoff with Full Jitter.
  * **Suicide & Fencing (STONITH)**: Prevents delayed nodes from executing dirty split-brain writes.

### 6. Pillar VI · Distributed Observability & Platform Governance
* **Responsibility**: Delivers end-to-end distributed trace transparency and system health metrics.
* **Core Components**:
  * **Distributed Tracing**: W3C TraceContext, OpenTelemetry standards (TraceID, SpanID, Baggage).
  * **Metric Methodologies**: Prometheus RED method (Rate, Errors, Duration), USE method.
  * **Deterministic State Replay**: Event-log based time-travel debugging.

---

## 2. Core Operational Hub: Six Peer Control Paradigms (Level 2)

Under **[Pillar III: Distributed Computing Runtime & Scheduling Control]**, there exist **Six Orthogonal Peer Control Paradigms**:

```
                       [Six Peer Runtime Control Paradigms]
                                         │
   ┌─────────────────┬───────────────────┼───────────────────┬─────────────────┐
   ▼                 ▼                   ▼                   ▼                 ▼
[1. Flow Control] [2. Concurrency Ctrl][3. Lifecycle Ctrl] [4. Mutual Excl.]  [5. Job Sched.]
(Capacity/Volume) (State Isolation)    (Temporal Validity) (Role Uniqueness)  (Work Sharding)
```

| Control Paradigm | Governed Dimension | Core Question | Fatal Failure Prevented |
| :--- | :--- | :--- | :--- |
| **1. Distributed Flow Control**<br>*(流量控制)* | **Macro Capacity & Volume**<br>(宏观容量与吞吐) | "Can the physical cluster support this concurrent workload volume right now?" | Cluster overload, OOM cascading crashes, noisy-neighbor starvation. |
| **2. Distributed Concurrency Control**<br>*(并发控制)* | **Micro Data State Isolation**<br>(微观状态正确性) | "Who has the exclusive right to modify this specific business entity?" | Race conditions, split-brain dual-master conflicts, duplicate payments. |
| **3. Distributed Lifecycle Control**<br>*(生命周期控制)* | **Temporal Validity & Time**<br>(时效与事件有效性) | "Is this picked-up task still alive and valid at this exact moment?" | Queue delays causing dead/aborted tasks to execute ghost operations (Zombie Runs). |
| **4. Distributed Mutual Exclusion & Election**<br>*(互斥选主)* | **Execution Topology & Roles**<br>(拓扑与角色唯一性) | "Who is the single authoritative Master or Coordinator across the cluster?" | Split-brain dual coordinators issuing conflicting execution commands. |
| **5. Distributed Job Scheduling & Sharding**<br>*(作业调度与分片)* | **Work Topology & Load Balancing**<br>(负载均衡与任务分布) | "How can millions of tasks be evenly distributed to workers without starvation?" | Hotspot skew, worker thread starvation, long-tail latency. |
| **6. Distributed Saga Orchestration**<br>*(长事务编排补偿)* | **Cross-Service Atomicity**<br>(业务最终一致性) | "How do we reliably compensate when one step in a multi-service workflow fails?" | Partial service commits, irreversible state hangs, accounting corruption. |

---

## 3. Microscopic Primitives: Algorithms & Concrete Implementations (Level 3)

### 1. Distributed Flow Control Primitives
* **Token Bucket Algorithm**: An independent timer injects tokens at a constant rate; allows burst traffic but throttles requests when the bucket is empty.
* **Leaky Bucket Algorithm**: Enforces constant egress processing speed to completely smooth out traffic spikes.
* **Distributed Sliding Window Counter**: Uses Redis `ZSET` to record request timestamps and `ZREMRANGEBYSCORE` to enforce millisecond-precision rate limiting.
* **Backpressure**: When consumer queue backlog exceeds high-watermark thresholds, workers signal upstream producers to pause or reduce batch sizes.
* **Adaptive Load Shedding**: Evaluates node CPU utilization (e.g., > 85%) and P99 latency to shed low-priority requests proactively.

### 2. Distributed Concurrency Control Primitives
* **Distributed Lease with TTL**: A time-bounded mutual exclusion lock (e.g., Redis `SET run:lease:{id} {worker_id} NX EX 30`) that expires automatically on node crashes.
* **Watchdog Heartbeat Thread**: An asynchronous local background thread that issues `EXPIRE` renewals to Redis every $1/3$ of the lease duration.
* **Monotonically Increasing Fencing Tokens**: Lock servers issue incremented numbers with each lease; storage engines reject writes bearing stale tokens.
* **Compare-And-Swap (CAS) Optimistic Locking**: `UPDATE runs SET status='RUNNING', v=v+1 WHERE id=:id AND v=:old_v`; validates execution safety based on affected row count.
* **Serializable Snapshot Isolation (SSI)**: Multi-version concurrency engine that detects dangerous read-write dependency cycles and aborts conflicting younger transactions.

### 3. Distributed Lifecycle Control Primitives
* **Soft-Deletion Tombstone Records**: When a user cancels an order, the system writes `is_cancelled = true, tombstone_at = NOW()`, preserving physical state.
* **Out-of-band Invalidation Probing**: Workers pulling tasks from message queues must query the read-only database for tombstone markers before invoking any LLMs or tools.
* **Cancellation Context Propagation**: Carries cancellation signals across network RPC boundaries (e.g., Go `context.WithCancel`, .NET `CancellationToken`).
* **Tombstone Compaction GC**: Triggers physical purge after a retention period (e.g., 7 to 30 days) to prevent index bloat.
* **Transactional Outbox Pattern**: Writes task finalization events into the database in the same transaction as state updates; CDC engines publish events reliably.

### 4. Distributed Mutual Exclusion & Election Primitives
* **Ephemeral Sequential Nodes (ZooKeeper)**: Nodes register sequence znodes under `/election`; the node with the lowest sequence number becomes Master.
* **etcd Lease Election (Campaign & Proclaim)**: Uses etcd software transactional memory (STM) to claim and renew the leader key.
* **Paxos Majority Quorum**: Two-phase Prepare/Accept voting rounds; requires signatures from more than half of the cluster nodes ($N/2 + 1$).

### 5. Distributed Job Scheduling & Sharding Primitives
* **Consistent Hash Ring with Virtual Nodes**: 2^32 cyclic hash space where physical workers map to 100~200 virtual points to minimize distribution skew.
* **Work-Stealing Deque**: Workers maintain local double-ended queues; idle workers steal tasks from the tail of busy peers' queues.
* **Partition Leases**: Grants ownership leases per partition or shard to prevent duplicate consumption during cluster autoscaling.

### 6. Distributed Saga Orchestration Primitives
* **Orchestrator Pattern**: A centralized workflow state machine executes forward actions sequentially; executes reverse compensation steps if a step fails.
* **Idempotency Tokens (`operation_ref`)**: Generates `SHA256(run_id, step, action_type)` before invoking sensitive APIs to allow deterministic reconciliation on timeouts.
* **Suspension & Empty Compensation Defense**: If a compensating request arrives before the forward request, the system registers a tombstone to discard the delayed forward call.

---

## 4. Practical Mapping: AI Agent Harness Implementation

In the Cogniva AI Agent Controlled Host Runtime (L2 Harness), the first physical admission gate [`on_run_load`](../agent/deep-dive/topics/01-lifecycle-hooks/08-Hook1-on_run_load-准入屏障与分布式租约落地实战.md) implements these three peer control paradigms directly:

```
[Kafka Event Enters Harness Worker]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  【Hook 1: on_run_load Admission Pipeline】            │
│                                                        │
│  Gate 1: 【Distributed Flow Control】(Feature 4)        │
│  * Mechanism: Tenant concurrency counter & SLA limit   │
│  * Target: Capacity safety; backpressure on exceed     │
│                                                        │
│  Gate 2: 【Distributed Concurrency Control】(Feature 2)│
│  * Mechanism: Atomic 30s distributed lease (NX EX 30)  │
│  * Target: Data isolation; suicide on acquisition fail │
│                                                        │
│  Gate 3: 【Distributed Lifecycle Control】(Feature 3)  │
│  * Mechanism: Soft-deletion tombstone verification     │
│  * Target: Temporal validity; abort on tombstone hit   │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼ (All Gates Passed)
                 [Enter Hook 2: before_context]
```

* 🔗 **Direct Implementation Links**:
  * [Hook 1 on_run_load Admission Barrier & Distributed Lease Implementation](../agent/deep-dive/topics/01-lifecycle-hooks/08-Hook1-on_run_load-准入屏障与分布式租约落地实战.md)
  * [Hook 7 before_checkpoint Concurrency Consistency & CAS Fencing Token Guard](../agent/deep-dive/topics/01-lifecycle-hooks/10-Hook7-before_checkpoint-并发一致性与CAS乐观锁防脑裂落地实战.md)
  * [Appendix: Zombie Run Mechanism & Tombstone Verification (ASD-STE100)](../agent/deep-dive/topics/01-lifecycle-hooks/appendix/08-附录-僵尸任务产生机理与墓碑机制-STE100规范解构.md)
  * [Appendix: Resume Run vs. Failover Recovery Deep Dive](../agent/deep-dive/topics/01-lifecycle-hooks/appendix/08-附录-断点续跑与故障转移接管深度解构.md)
  * [Appendix: State & Checkpoint Rehydration Architecture & Implementation Overview](../agent/deep-dive/topics/01-lifecycle-hooks/appendix/08-附录-历史检查点与状态反序列化架构设计与工程落地全景.md)

---

## 5. Authoritative References & Classical Citations

The architectural boundaries, mathematical models, and terminology in this knowledge graph adhere to the following classical computer science works:

1. **Foundations of Distributed Systems & Database Theory**:
   * **Bernstein, P. A., Hadzilacos, V., & Goodman, N. (1987).** *Concurrency Control and Recovery in Database Systems*. Addison-Wesley. *(Mathematical foundations of serializability, 2PL, and deadlock detection)*.
   * **Tanenbaum, A. S., & Van Steen, M. (2017).** *Distributed Systems: Principles and Paradigms* (3rd ed.). CreateSpace. *(Definitive six-pillar taxonomy, RPC communication, and fault-tolerance models)*.
   * **Kleppmann, M. (2017).** *Designing Data-Intensive Applications*. O'Reilly Media. *(Chapters 8 & 9: Distributed lock timeouts, GC pause split-brain, and fencing token validation)*.
2. **Distributed Leases & Lock Services**:
   * **Gray, C., & Cheriton, D. (1989).** "Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency." *ACM SIGOPS Operating Systems Review (SOSP '89)*, 23(5), 202-210. *(Foundational paper introducing distributed leases with TTL)*.
   * **Burrows, M. (2006).** "The Chubby Lock Service for Loosely-Coupled Distributed Systems." *OSDI '06*. *(Design of coarse-grained distributed locks and heartbeat sessions)*.
3. **Clocks, Ordering & Consensus**:
   * **Lamport, L. (1978).** "Time, Clocks, and the Ordering of Events in a Distributed System." *Communications of the ACM*, 21(5), 558-565. *(Turing Award paper establishing logical clocks and causal partial ordering)*.
   * **Ongaro, D., & Ousterhout, J. (2014).** "In Search of an Understandable Consensus Algorithm." *USENIX ATC '14*. *(Raft consensus protocol)*.
4. **Flow Control & Lifecycle Standards**:
   * **Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (2016).** *Site Reliability Engineering: How Google Runs Production Systems*. O'Reilly Media. *(Chapter 21: Handling Overload - client-side throttling and adaptive load shedding)*.
   * **Kubernetes Architecture Documentation.** *Pod Lifecycle & Graceful Deletion via DeletionTimestamp* *(Industry reference for tombstone patterns and cooperative termination)*.
