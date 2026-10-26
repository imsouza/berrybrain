---
id: sciref-get-available-resources-resource-semantics
name: "Scientific Ref: Resource Semantics"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (get-available-resources): Resource Semantics"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "get available resources resource semantics"
  - "resource semantics"
keywords:
  - "get"
  - "available"
  - "resources"
  - "resource"
  - "semantics"
  - "specialized"
  - "scientific"
  - "reference"
---

# Resource Semantics

Research and behavior cut-off: **2026-10-01**. See
[`sources.md`](sources.md) for the official documentation used.

## Core rule: inventory is not entitlement

Never treat a host-wide count as a promise that the current process can use it.
Interpret usable resources as the intersection of independently observed
constraints:

1. host inventory;
2. process affinity or processor-group scope;
3. cgroup/container constraints;
4. scheduler allocation;
5. accelerator visibility and device permissions; and
6. application runtime compatibility.

Missing evidence means **unknown**, not unlimited. Scheduler variables can
describe an allocation without proving that affinity or cgroup enforcement is
enabled. Conversely, a cgroup or affinity mask can be stricter than the
scheduler request.

## CPU

### Physical and logical CPUs

- A logical CPU is an operating-system scheduling unit. Simultaneous
  multithreading can expose multiple logical CPUs on one physical core.
- A physical-core count describes topology, not the number of independent
  workers the process may start.
- `psutil.cpu_count(logical=True)`, macOS `hw.logicalcpu`, and POSIX
  `SC_NPROCESSORS_ONLN` provide host/system inventory. They can exceed the
  CPUs usable by the process. `os.cpu_count()` is a fallback: Python 3.13+
  `-X cpu_count` or `PYTHON_CPU_COUNT` overrides both Python CPU-count APIs.
  The detector prefers independent inventory and keeps Python process count
  as a separate planning input.
- `os.process_cpu_count()` (Python 3.13+) is process-aware. On supported
  platforms, affinity APIs provide a more explicit process constraint.
- On Windows systems with multiple processor groups, a system-wide logical
  count and one process/thread group's usable count can differ. Windows 11
  and Server 2022 default affinity spans groups; do not assume every modern
  Windows process is capped at 64 logical CPUs.

The detector reports host logical and physical counts separately. It never
derives physical cores from a logical count.

### Affinity, cpusets, and quotas

- Process affinity limits the logical CPUs on which a process may execute.
- Linux `cpuset.cpus.effective` reports CPUs actually granted after parent
  constraints. The requested `cpuset.cpus` can differ.
- `/proc/self/status` exposes `Cpus_allowed_list`, but the detector prefers
  affinity APIs and cgroup effective cpusets.
- cgroup v2 `cpu.max` is `$MAX $PERIOD`. `max` means no local bandwidth limit.
  A finite ratio is CPU-time capacity, possibly fractional; it is not a core
  topology count.
- Parent cgroups also constrain children, so the detector takes the most
  restrictive finite visible ancestor quota. Membership is resolved through
  `/proc/self/mountinfo` cgroup2 root/mountpoint fields. A namespace or delegated
  mount may hide stronger ancestors. Missing files are not evidence of
  unlimited capacity; cgroup v1 is outside the collector's implemented scope.

For a `cpu.max` ratio of 1.5, the snapshot reports
`capacity_cores: 1.5` and a conservative CPU-bound worker ceiling of 1. A
workload may choose more threads for latency hiding, but it should expect
throttling and must not describe those threads as 1.5 physical cores.

### Python worker pools

- Current Python `multiprocessing.Pool` and `ProcessPoolExecutor` defaults use
  `os.process_cpu_count()` when available.
- Python 3.14 no longer uses `fork` as the default start method on any platform.
  Code that depends on a particular start method must request it deliberately.
- Process workers do not make each worker's native-library threads disappear.
  BLAS/OpenMP threads multiplied by process workers commonly oversubscribe an
  allocation.
- Windows `ProcessPoolExecutor` has a documented maximum of 61 workers.

Use the workload planner's worker and threads-per-worker values as conservative
ceilings, then benchmark a real representative workload. Do not run a synthetic
stress test merely to discover capacity.

## Memory

### Host and effective memory

- `psutil.virtual_memory().total` and `.available` describe system-visible
  memory, not necessarily the process limit.
- Linux `/proc/meminfo` `MemAvailable` is the standard-library fallback for a
  host-availability estimate.
- cgroup v2 `memory.current` is current cgroup usage.
- `memory.high` is a throttle/reclaim pressure boundary. Exceeding it does not
  itself invoke the cgroup OOM killer, and the value can be breached.
- `memory.max` is the hard cgroup limit. If usage cannot be reduced at that
  boundary, the cgroup OOM killer can run.
- Parent memory limits are hierarchical. Shared ancestor usage can reduce what
  remains for a child, so effective remaining memory is the minimum finite
  `limit - current` observed through the ancestor chain.
- Slurm memory variables describe requested/allocated memory, but strict
  enforcement depends on site configuration.

The detector keeps host total/available values, cgroup values, scheduler values,
and the conservative effective values distinct. A point-in-time "available"
value can change immediately and is not a reservation.

### macOS unified memory

On Apple silicon, CPU and integrated GPU share unified memory. Do not add a
fictional GPU VRAM amount to system RAM. The snapshot marks the memory model as
`unified_cpu_gpu` and leaves dedicated GPU memory null. Metal framework support
and model/operator support still require application-specific checks.

## Accelerators

Accelerator usability has separate layers:

1. **Hardware or management visibility** — a management query returns a device.
2. **Allocation visibility** — scheduler and named visibility variables permit
   a device or a subset.
3. **Device permission** — the process/container can open the required device
   interfaces.
4. **Driver/runtime compatibility** — driver, CUDA/ROCm/Metal runtime, and
   framework versions are compatible.
5. **Workload compatibility** — the requested operation and data type are
   implemented on that backend.

`nvidia-smi` success confirms NVIDIA management visibility only. It does not
prove that CUDA libraries exist or are compatible. NVIDIA documents driver and
runtime compatibility as a separate requirement.

AMD SMI or ROCm SMI success likewise does not prove HIP/ROCm runtime usability.
New deployments should prefer `amd-smi`; `rocm-smi` is retained as a read-only
fallback. The fixed AMD query selects `--asic --vram`, avoiding unrelated
static fields. Current JSON nests VRAM size as `{value,

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

