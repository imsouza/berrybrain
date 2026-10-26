---
id: sciref-scientific-slides-beamer-guide
name: "Scientific Ref: LaTeX Beamer Guide for Scientific Presentations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-slides): LaTeX Beamer Guide for Scientific Presentations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific slides beamer guide"
  - "cientifico slides beamer guide"
  - "latex beamer guide for scientific presentations"
keywords:
  - "scientific"
  - "slides"
  - "beamer"
  - "guide"
  - "cientifico"
  - "specialized"
  - "reference"
  - "latex"
---

# LaTeX Beamer Guide for Scientific Presentations

## Overview

Beamer is a LaTeX document class for creating presentations with professional, consistent formatting. It's particularly well-suited for scientific presentations containing equations, code, algorithms, and citations. This guide covers Beamer basics, themes, customization, and advanced features for effective scientific talks.

Current upstream: [Beamer 3.78](https://ctan.org/pkg/beamer), reviewed 2026-09-30.
The snippets below are illustrative fragments: combine their required packages in the
preamble, provide figures and `references.bib`, and compile in your TeX distribution.
The bundled templates were smoke-compiled with local Beamer 3.72 / TeX Live 2025; that is not a complete layout or
bibliography validation. Dense placeholder layouts in the
seminar and defense templates emit overfull-box warnings and need content-specific
rendering and adjustment. Beamer currently does not support tagged PDF; provide a
semantic alternative when accessibility requires it.

## Why Use Beamer?

### Advantages

**Professional Quality**:
- Consistent, polished appearance
- Beautiful typography (especially for math)
- Publication-quality output
- Professional themes and templates

**Scientific Content**:
- Native equation support (LaTeX math)
- Code listings with syntax highlighting
- Algorithm environments
- Bibliography integration
- Cross-referencing

**Reproducibility**:
- Plain text source (version control friendly)
- Programmatic figure generation
- Consistent styling across presentations
- Easy to maintain and update

**Efficiency**:
- Reuse content across presentations
- Template once, use forever
- Automated elements (page numbers, navigation)
- No manual formatting

### Disadvantages

**Learning Curve**:
- Requires LaTeX knowledge
- Compilation time
- Debugging can be challenging
- Less WYSIWYG than PowerPoint

**Flexibility**:
- Complex custom layouts require effort
- Image editing requires external tools
- Some design elements easier in PowerPoint
- Animations more limited

**Collaboration**:
- Not ideal for non-LaTeX users
- Version conflicts possible
- Requires LaTeX installation

## Basic Beamer Document Structure

### Minimal Example

```latex
\documentclass{beamer}

% Theme
\usetheme{Madrid}
\usecolortheme{beaver}

% Title information
\title{Your Presentation Title}
\subtitle{Optional Subtitle}
\author{Your Name}
\institute{Your Institution}
\date{\today}

\begin{document}

% Title slide
\begin{frame}
  \titlepage
\end{frame}

% Content slide
\begin{frame}{Slide Title}
  Content goes here
\end{frame}

\end{document}
```

### Essential Packages

```latex
\documentclass{beamer}

% Encoding and fonts
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% Graphics
\usepackage{graphicx}
\graphicspath{{./figures/}}

% Math
\usepackage{amsmath, amssymb, amsthm}

% Tables
\usepackage{booktabs}
\usepackage{multirow}

% Colors
\usepackage{xcolor}

% Algorithms
\usepackage{algorithm}
\usepackage{algorithmic}

% Code listings
\usepackage{listings}

% Citations
\usepackage[style=authoryear,backend=biber]{biblatex}
\addbibresource{references.bib}
```

### Frame Basics

```latex
% Basic frame
\begin{frame}{Title}
  Content
\end{frame}

% Frame with subtitle
\begin{frame}{Title}{Subtitle}
  Content
\end{frame}

% Frame without title
\begin{frame}
  Content
\end{frame}

% Fragile frame (for verbatim/code)
\begin{frame}[fragile]{Code Example}
  \begin{verbatim}
  def hello():
      print("Hello")
  \end{verbatim}
\end{frame}

% Plain frame (no header/footer)
\begin{frame}[plain]
  Full slide content
\end{frame}
```

## Themes and Appearance

### Presentation Themes

Beamer includes many built-in themes controlling overall layout:

**Classic Themes**:
```latex
\usetheme{Berlin}      % Sections in header
\usetheme{Copenhagen}  % Minimal, clean
\usetheme{Madrid}      % Professional, rounded
\usetheme{Boadilla}    % Simple footer
\usetheme{AnnArbor}    % Vertical navigation
```

**Modern Themes**:
```latex
\usetheme{CambridgeUS}  % Blue theme
\usetheme{Singapore}    % Minimalist
\usetheme{Rochester}    % Very minimal
\usetheme{Antibes}      % Tree navigation
```

**Popular for Science**:
```latex
% Clean and minimal
\usetheme{default}
\usetheme{Copenhagen}

% Professional with navigation
\usetheme{Madrid}
\usetheme{Berlin}

% Traditional academic
\usetheme{Pittsburgh}
\usetheme{Boadilla}
```

### Color Themes

```latex
% Blue themes
\usecolortheme{default}      % Blue
\usecolortheme{dolphin}      % Cyan-blue
\usecolortheme{seagull}      % Grayscale

% Warm themes
\usecolortheme{beaver}       % Red/brown
\usecolortheme{rose}         % Pink/red

% Nature themes
\usecolortheme{orchid}       % Purple
\usecolortheme{crane}        % Orange/yellow

% Professional
\usecolortheme{albatross}    % Gray/blue
```

### Font Themes

```latex
\usefonttheme{default}              % Standard
\usefonttheme{serif}                % Serif fonts
\usefonttheme{structurebold}        % Bold structure
\usefonttheme{structureitalicserif} % Italic serif
\usefonttheme{professionalfonts}    % Professional fonts
```

### Custom Colors

```latex
% Define custom colors
\definecolor{myblue}{RGB}{0,115,178}
\definecolor{myred}{RGB}{214,40,40}

% Apply to theme elements
\setbeamercolor{structure}{fg=myblue}
\setbeamercolor{title}{fg=myred}
\setbeamercolor{frametitle}{fg=myblue,bg=white}
\setbeamercolor{block title}{fg=white,bg=myblue}
```

### Minimal Custom Theme

```latex
% Remove navigation symbols
\setbeamertemplate{navigation symbols}{}

% Page numbers
\setbeamertemplate{footline}[frame number]

% Simple itemize
\setbeamertemplate{itemize items}[circle]

% Clean blocks
\setbeamertemplate{blocks}[rounded][shadow=false]

% Colors
\setbeamercolor{structure}{fg=blue!70!black}
\setbeamercolor{title}{fg=black}
\setbeamercolor{frametitle}{fg=blue!70!black}
```

## Content Elements

### Lists

**Itemize**:
```latex
\begin{frame}{Bullet Points}
  \begin{itemize}
    \item First point
    \item Second point
      \begin{itemize}
        \item Nested point
      \end{itemize}
    \item Third point
  \end{itemize}
\end{frame}
```

**Enumerate**:
```latex
\begin{frame}{Numbered List}
  \begin{enumerate}
    \item First item
    \item Second item
    \item Third item
  \end{enumerate}
\end{frame}
```

**Description**:
```latex
\begin{frame}{Definitions}
  \begin{description}
    \item[Term 1] Definition of term 1
    \item[Term 2] Definition of term 2
  \end{description}
\end{frame}


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

