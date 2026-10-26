---
id: sciref-gtars-python-api
name: "Scientific Ref: Python API (`gtars==0.10.0`)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gtars): Python API (`gtars==0.10.0`)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gtars python api"
  - "python api (`gtars==0.10.0`)"
keywords:
  - "gtars"
  - "python"
  - "api"
  - "specialized"
  - "scientific"
  - "reference"
---

# Python API (`gtars==0.10.0`)

Research and runtime verification date: **2026-10-01**. The PyPI package requires
Python 3.10+ and contains a native PyO3 extension.

## Import surface

Public functionality is grouped into submodules:

```python
import gtars
from gtars.models import Region, RegionSet
from gtars.genomic_distributions import consensus
from gtars.tokenizers import Tokenizer, tokenize_fragment_file
from gtars.refget import RefgetStore, digest_fasta, digest_sequence
```

`gtars.__version__` is `0.10.0`. `Region`, `RegionSet`, `Tokenizer`, and
`RefgetStore` are not documented as top-level classes. Python 0.10.0 does not
export Python `uniwig`, `igd`, `scoring`, `fragsplit`, or `bbcache` submodules.

## Verified signatures

The installed 0.10.0 wheel reported:

```text
Region(chr, start, end, rest)
RegionSet(path)
RegionSet.from_regions(regions, strands=None)
RegionSet.from_vectors(chrs, starts, ends, strands=None)
RegionSet.count_overlaps(self, other)
RegionSet.coverage(self, other)
Tokenizer(path)
Tokenizer.from_bed(path)
Tokenizer.from_pretrained(path)
tokenize_fragment_file(file, tokenizer)
consensus(region_sets)
RefgetStore.open_local(path)
RefgetStore.open_remote(cache_path, remote_url)
RefgetStore.get_substring(self, seq_digest, start, end)
```

The shipped `.pyi` stubs omit some runtime methods (`from_vectors`, `disjoin`,
`strands`, and several refget load methods). The tagged PyO3 source and the
installed runtime are authoritative for those omissions.

## `Region`

```python
from gtars.models import Region

region = Region(
    chr="chr1",
    start=100,
    end=200,
    rest="peak_001\t500\t+",
)
assert len(region) == 100
assert (region.chr, region.start, region.end) == ("chr1", 100, 200)
```

`start` and `end` are Rust `u32`. Validate `0 <= start < end <= contig_length`
before construction. The constructor does not itself prove assembly or contig
compatibility. Equality compares only chromosome/start/end; trailing `rest`
content is not part of equality.

## `RegionSet` constructors

### Local file

```python
from pathlib import Path
from gtars.models import RegionSet

path = Path("reviewed-input.bed.gz")
if not path.is_file() or path.is_symlink():
    raise ValueError("expected a reviewed local regular file")
regions = RegionSet(str(path))
```

The Python build enables `gtars-core`'s HTTP feature. If the supplied string is
not an existing local file, core code attempts to open it as a URL. Therefore,
checking `is_file()` before construction is a security boundary, not just an
error-message improvement.

File parsing:

- accepts tab-separated BED-like input and `.gz`;
- skips `browser`, `track`, and `#` lines;
- treats a first row with a nonnumeric second field as a column header;
- requires at least three columns;
- stores columns 4+ as one tab-joined `Region.rest` string;
- rejects an empty region set;
- sorts in memory by lexicographic chromosome then numeric start.

The original file is not rewritten, but input row order is not preserved in the
object.

### In-memory regions

```python
from gtars.models import Region, RegionSet

regions = RegionSet.from_regions(
    [
        Region("chr1", 100, 200, None),
        Region("chr2", 300, 450, None),
    ],
    strands=["+", "-"],
)

same = RegionSet.from_vectors(
    ["chr1", "chr2"],
    [100, 300],
    [200, 450],
    strands=["+", "-"],
)
```

All coordinate vectors, and the optional strand vector, must have equal length.
When strands are omitted, the separate strand vector contains `"*"`.

## Properties and mutability

```python
n = len(regions)
first = regions[0]       # negative indices are supported
identifier = regions.identifier
file_digest = regions.file_digest
header = regions.header
strands = regions.strands

regions.sort()           # in-place; returns None; see strand caveat below
regions.to_bed("out.bed")
regions.to_bed_gz("out.bed.gz")
regions.to_bigbed("out.bb", "assembly.chrom.sizes")
```

- `identifier` is an MD5-like identifier over sorted first-three-column content.
- `file_digest` includes retained trailing columns. Neither value substitutes for
  an independently recorded SHA-256 provenance hash.
- `path` raises `ValueError` for a set created from regions/vectors.
- `sort()` reorders regions but does not reorder the separate `strands` vector
  in 0.10.0. Sort `(region, strand)` pairs before construction, or maintain the
  association externally; otherwise strand-dependent annotations can be silently
  reassigned. File loading already sets this vector to `"*"`.
- Writers overwrite/create the specified output; check output policy first.
- `to_bigbed` needs chromosome sizes matching every contig and bound.

## Interval statistics and structural operations

The following methods are current:

```python
widths = regions.widths()                 # list[int]
same_widths = regions.region_widths()     # alias
mean_width = regions.mean_region_width()  # runtime returns float
length = regions.get_nucleotide_length()
max_ends = regions.get_max_end_per_chr()
stats = regions.chromosome_statistics()

reduced = regions.reduce()
disjoint = regions.disjoin()
trimmed = regions.trim({"chr1": 248956422})
gaps = regions.gaps({"chr1": 248956422})
clusters = regions.cluster(max_gap=100)
```

`reduce()` merges overlapping **and adjacent** ranges. `trim()` drops unknown
contigs and clamps bounds. These transformations do not perform liftover and can
drop the separate strand vector.

`promoters(upstream, downstream)` is relative to each region's start in the
current implementation; it is not a safe substitute for a strand-aware TSS
workflow. Establish strand and TSS semantics independently.

`neighbor_distances()` and `nearest_neighbors()` can return fewer values than
input regions because singletons on a chromosome are skipped; results are not
row-aligned.

`distribution(n_bins=250, chrom_sizes=None)` uses observed maximum ends when
chromosome sizes are absent, making results non-comparable across files. Supply
the exact assembly dictionary. Unknown/out-of-bounds regions are skipped when
sizes are supplied, so summed counts may be lower than input count.

## Pairwise and all-vs-all operations

```python
a = RegionSet("a.bed")
b = RegionSet("b.bed")

concatenated = a.concat(b)          # no merge
union = a.union(b)                  # minimal merged set
difference = a.setdiff(b)           # subtract b bases from a
pairwise = a.pintersect(b)          # pair by index, not genomic all-vs-all
all_pieces = a.intersect

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

