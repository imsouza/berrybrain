---
id: sci-get-available-resources
name: "Scientific: get-available-resources"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Detects host inventory and effective CPU, memory, disk, scheduler, container, and accelerator limits when a user asks for resource-aware planning or before a clearly resource-sensitive local workload. Produces a redacted JSON snapshot and conservative planning helpers without str"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "get available resources"
  - "get-available-resources"
keywords:
  - "get"
  - "available"
  - "resources"
  - "detects"
  - "host"
  - "inventory"
  - "effective"
  - "memory"
  - "disk"
---

# Get Available Resources

Build a conservative picture of resources available to the **current process**.
Keep host inventory, process affinity, cgroup/container limits, scheduler
allocation, and accelerator runtime usability separate.

## Safety contract

Follow these rules:

- Run detection when the user requests it or a specific workload needs resource
  planning. Do not persist a fingerprint for every scientific task.
- Use stdout by default. Persist only when the user chooses an explicit generic
  local filename.
- Do not run stress tests, benchmarks, large allocations, write probes, device
  resets, driver installation, or clock/power changes.
- Do not dump the environment. Read only the named Slurm and accelerator
  variables implemented by the detector.
- Do not report hostnames, absolute paths, cgroup paths, job IDs, device UUIDs,
  PCI addresses, or raw visibility-variable values.
- Treat a missing observation as unknown. Never convert unknown to unlimited.
- Never infer that a visible host CPU, memory pool, or GPU is usable inside a
  scheduler allocation or container.

The bundled detector uses only fixed executable/argument tuples, no shell,
short timeouts, bounded stdout/stderr, and partial-failure warnings.

## Quick start

Run from this skill directory.

### Ephemeral stdout snapshot

```bash
python scripts/detect_resources.py
```

The command emits only JSON to stdout. Redirect it only when ordinary shell
permissions are acceptable.

### Explicit private file

```bash
python scripts/detect_resources.py --output resource-snapshot.json
```

Explicit output is restricted to one `.json` filename in the current
directory, uses mode 0600 on POSIX, rejects symlinks and path traversal, and
refuses overwrite unless `--force` is supplied. Forced output also rejects
hard links and non-regular files. Windows privacy additionally depends on the
directory ACL.

### Optional psutil enhancement

The standard-library detector works without installation. For broader
cross-platform physical-core, affinity, available-memory, swap, and disk
coverage:

```bash
uv run --no-project --with "psutil==7.2.2" python scripts/detect_resources.py
```

The import is lazy. Failure to import psutil becomes a warning, not a fatal
error.

### Skip management-tool probes

```bash
python scripts/detect_resources.py --skip-accelerators
```

Use this when accelerator discovery latency is undesirable. The detector still
summarizes the presence and state of allowlisted visibility variables without
returning their values.

## Required interpretation

### CPU

Read these as different facts:

- `cpu.host.logical`: system-visible scheduling units.
- `cpu.host.physical`: physical topology, or null; never inferred from logical
  count.
- `cpu.process.affinity_logical`: current affinity-set size when supported.
- `cpu.cgroup_v2.cpuset_logical`: effective cgroup cpuset size.
- `cpu.cgroup_v2.quota_cores`: finite `cpu.max` capacity, possibly fractional.
- `scheduler.allocation.cpu_per_process`: bounded Slurm per-task
  interpretation when scope is clear.
- `cpu.effective.capacity_cores`: minimum positive observed constraint.
- `cpu.effective.worker_ceiling`: conservative floor for CPU process workers.

A quota of 1.5 is CPU-time capacity, not 1.5 physical cores. Affinity and
cpusets constrain placement; quota constrains bandwidth.

### Memory

Keep these separate:

- host total/available memory;
- current cgroup usage, hard `memory.max`, and remaining hierarchical capacity;
- `memory.high`, which is a pressure/throttle boundary rather than a hard cap;
- scheduler memory allocation and its scope; and
- conservative effective hard limit and available estimate.

On Apple silicon, `memory.model` is `unified_cpu_gpu`. Do not add integrated GPU
memory to RAM or describe it as separate VRAM.

### Accelerators

Each device is a backend **candidate**:

- NVIDIA GPU → CUDA candidate;
- AMD GPU → ROCm candidate;
- Apple integrated GPU → Metal candidate.

Management-query visibility does not establish:

1. scheduler/container permission;
2. device-node access;
3. driver/runtime compatibility;
4. framework package compatibility; or
5. operator/data-type support.

Therefore `runtime_usable_devices` remains null and each device says
`runtime_compatibility: not_tested`. Visibility/allocation counts constrain
the observed management records, not the number of framework devices. MIG and AMD partition enumeration can differ.
AMD `reported_total_bytes` is a device-reported memory pool; its relationship
to host RAM is not established, so it is never added to the RAM budget.

### Disk

`capacity_bytes`, filesystem `free_bytes`, user-available blocks, and a
non-writing permission check are distinct. Filesystem or project quotas can
still be stricter. The absolute working path is always redacted.

The disk snapshot covers the working filesystem only, matching
[psutil's path-specific semantics](https://psutil.readthedocs.io/stable/index.html#psutil.disk_usage).
If scratch, caches, and final outputs use different filesystems, inspect each
from its target directory and label the reports by role. Budget temporary and
final copies that coexist; free space on the input filesystem does not establish
space on the output filesystem.

### Scheduler and container

Slurm variables describe allocation scope, but enforcement depends on site
configuration such as task affinity or cgroups. Prefer affinity and cgroup
observations as enforcement evidence.

Container markers identify context; cgroup controls identify limits. A
container with no finite cgroup value can still see host inventory, and a
non-root cgroup is not automatically labeled a container.

See [`references/resource_semantics.md`](references/resource_semantics.md) for
the detailed platform rules.

## Plan a workload

The planner consumes a validated snapshot and performs no work:

```bash
python scripts/plan_workload.py resource-snapshot.json \
  --workload cpu \
  --tasks 100 \
  --memory-per-worker-mib 2048
```

Optional controls:

- `--workers N`: explicit upper bound.
- `--reserve-memory-mib N`: memory kept outside the worker budget.
- `--workload cpu|mixed|io`: selects a bounded worker heuristic.
- `--accelerator none|any|cuda|rocm|metal`: requests a candidate backend
  decision without claiming usability.
- `--output plan.json`: explicit private local output; stdout is default.

A known memory budget that cannot fit one worker returns zero workers and
`recommendation.status: insuf

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

