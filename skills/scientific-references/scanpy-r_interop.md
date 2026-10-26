---
id: sciref-scanpy-r-interop
name: "Scientific Ref: R Interoperability for Scanpy"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scanpy): R Interoperability for Scanpy"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scanpy interop"
  - "r interoperability for scanpy"
keywords:
  - "scanpy"
  - "interop"
  - "specialized"
  - "scientific"
  - "reference"
  - "interoperability"
---

# R Interoperability for Scanpy

Many single-cell datasets arrive as R objects (`.rds`, `.RData`, Seurat, or SingleCellExperiment) even when the downstream analysis should happen in Scanpy. Agents should convert these inputs to AnnData `.h5ad` first, then continue with normal Scanpy workflows.

Reviewed 2026-10-01 against the linked official R/Seurat/zellkonverter interfaces.
R installation and conversions below are illustrative; this refresh did not execute an R environment.

## Operating Principles

1. **Do not parse Seurat `.rds` directly in Python.** Use R to deserialize R objects and write `.h5ad`.
2. **Prefer `.h5ad` as the Python handoff format.** After conversion, all QC, clustering, plotting, and exports should use Scanpy/AnnData.
3. **Inspect before converting.** Determine whether the R object is Seurat, SingleCellExperiment, or a list/container; do not assume from the filename.
4. **Preserve raw counts and metadata.** Keep cell metadata (`obs`), gene metadata (`var`), raw counts/layers, and dimensional reductions when available.
5. **Use noninteractive commands.** Agents should use `Rscript -e` or script files, set CRAN repos explicitly, and pass `ask = FALSE`, `update = FALSE` for Bioconductor installs.

## Detect R and the Platform

Use these checks before installing anything:

```bash
uname -s 2>/dev/null || true
command -v Rscript || command -v R || true
Rscript --version 2>/dev/null || R --version 2>/dev/null || true
```

On Windows from PowerShell:

```powershell
Get-Command Rscript -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
Get-Command R -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
```

If Git Bash cannot find R on Windows, query PowerShell or common install paths:

```powershell
Get-ChildItem "C:\Program Files\R" -Filter Rscript.exe -Recurse -ErrorAction SilentlyContinue |
  Select-Object -First 1 -ExpandProperty FullName
```

Then call the discovered executable with quotes, for example:

```bash
"/c/Program Files/R/R-4.6.0/bin/Rscript.exe" --version
```

## Install R by OS

Prefer existing system package managers. If installation requires GUI approval, admin credentials, or an unavailable package manager, stop and report the blocker.

### macOS

Use Homebrew when available:

```bash
brew install --cask r-app
```

For packages with compiled code, install command-line build tools if the system asks for compilers:

```bash
xcode-select --install
```

Some R packages with Fortran code may require the CRAN macOS toolchain from `https://mac.R-project.org/tools/`. Prefer CRAN binary packages where possible to avoid compiler work.

### Linux

Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y \
  r-base r-base-dev build-essential gfortran \
  libcurl4-openssl-dev libssl-dev libxml2-dev libhdf5-dev \
  libharfbuzz-dev libfribidi-dev libfontconfig1-dev libfreetype6-dev \
  libpng-dev libtiff5-dev libjpeg-dev
```

Fedora/RHEL-like systems:

```bash
sudo dnf install -y \
  R R-devel gcc gcc-c++ gcc-gfortran make \
  libcurl-devel openssl-devel libxml2-devel hdf5-devel \
  harfbuzz-devel fribidi-devel fontconfig-devel freetype-devel \
  libpng-devel libtiff-devel libjpeg-turbo-devel
```

If `sudo` is unavailable, use a managed environment such as Conda/Mamba if already present:

```bash
conda install -c conda-forge r-base r-essentials
```

### Windows

Use `winget` from PowerShell when available:

```powershell
winget install --id RProject.R -e
```

Install Rtools only if packages need compilation:

```powershell
winget install --id RProject.Rtools -e
```

After installation, open a new shell or locate `Rscript.exe` under `C:\Program Files\R\R-*\bin\`. In Git Bash, call Windows executables through quoted paths or PowerShell; do not assume `/usr/bin/R` exists.

## Install Conversion Packages

Create a project-local R library when you do not want to alter the user's global R library:

```bash
mkdir -p .r-lib
export R_LIBS_USER="$PWD/.r-lib"
```

Install the core conversion stack:

```bash
Rscript -e 'options(repos = c(CRAN = "https://cloud.r-project.org")); install.packages(c("BiocManager", "remotes"), Ncpus = max(1, parallel::detectCores() - 1)); BiocManager::install(c("SingleCellExperiment", "zellkonverter"), ask = FALSE, update = FALSE)'
```

Install Seurat support only when the input is a Seurat object:

```bash
Rscript -e 'options(repos = c(CRAN = "https://cloud.r-project.org")); install.packages(c("Seurat", "SeuratObject"), Ncpus = max(1, parallel::detectCores() - 1))'
```

Optional SeuratDisk fallback for h5Seurat-to-h5ad conversion:

```bash
Rscript -e 'options(repos = c(CRAN = "https://cloud.r-project.org")); if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes"); remotes::install_github("mojaveazure/seurat-disk", upgrade = "never")'
```

Avoid `sceasy` as the first choice. It can work, but it depends on `reticulate`/Python environment coupling and has more version-specific failure modes. Use it only after `zellkonverter` and SeuratDisk paths fail.

## Inspect R Inputs

For `.rds` files:

```bash
Rscript -e 'obj <- readRDS("input.rds"); print(class(obj)); if (is.list(obj) && !is.data.frame(obj)) print(names(obj))'
```

For `.RData`/`.rda` files:

```bash
Rscript -e 'e <- new.env(parent = emptyenv()); load("input.RData", envir = e); print(ls(e)); print(lapply(as.list(e), class))'
```

The script below takes one `.rds`, not an `.RData` workspace. Select the intended
Seurat or SingleCellExperiment object from `e`, then `saveRDS(e[["object_name"]], "input.rds")`.
A bare SummarizedExperiment must first be explicitly converted to SingleCellExperiment. If there is ambiguity, ask the user which object to convert.

## Convert `.rds` to `.h5ad`

Use this script as the default conversion path. It handles SingleCellExperiment directly and converts Seurat objects through SingleCellExperiment before writing `.h5ad`.

```r
#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript convert_rds_to_h5ad.R input.rds output.h5ad [assay]", call. = FALSE)
}

input <- normalizePath(args[[1]], mustWork = TRUE)
output <- args[[2]]
assay <- if (length(args) >= 3) args[[3]] else NULL

options(repos = c(CRAN = "https://cloud.r-project.org"))

ensure_pkg <- function(pkg, bioc = FALSE) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (bioc) {
      if (!requireNamespace("BiocManager", quietly = TRUE)) {
        install.packages("BiocManager")
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

