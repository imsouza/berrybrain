import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const source = readFileSync(new URL("../src/components/ask-markdown.tsx", import.meta.url), "utf8")
  .replace('import "katex/dist/katex.min.css";', "");
const workspaceStub = `data:text/javascript;base64,${Buffer.from('export const appPath = (path) => `/berrybrain${path}`;').toString("base64")}`;
const mermaidStub = `data:text/javascript;base64,${Buffer.from('export const MermaidDiagram = ({ source }) => `Mermaid diagram:${source}`;').toString("base64")}`;
const compiled = ts.transpileModule(source, {
  compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText.replace(/from "([^"]+)"/g, (_, name) => `from ${JSON.stringify(name === "@/contexts/workspace-context" ? workspaceStub : name === "./editor/mermaid-diagram" ? mermaidStub : pathToFileURL(require.resolve(name)).href)}`);
const { AskMarkdown } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const render = (content, references = []) => renderToStaticMarkup(React.createElement(AskMarkdown, { content, references }));

test("renders headings, emphasis, ordered and unordered lists", () => {
  const html = render("# Guia\n\n**Conceito** e *exemplo*.\n\n1. Estudar\n2. Revisar\n\n- Praticar");
  for (const tag of ["h2", "strong", "em", "ol", "ul", "li"]) assert.match(html, new RegExp(`<${tag}[ >]`));
  assert.doesNotMatch(html, /# Guia|\*\*Conceito\*\*/);
});

test("renders GFM tables, code blocks and blockquotes", () => {
  const html = render("| Tema | Valor |\n| --- | --- |\n| Algoritmos | 10 |\n\n```python\nprint(10)\n```\n\n> Fonte");
  for (const tag of ["table", "th", "td", "pre", "code", "blockquote"]) assert.match(html, new RegExp(`<${tag}[ >]`));
  assert.match(html, /overflow-x-auto/);
});

test("renders formulas and Mermaid through strict, bounded renderers", () => {
  const html = render("$a^2+b^2=c^2$\n\n```mermaid\ngraph TD\n  A --> B\n```");
  assert.match(html, /class="katex"/);
  assert.match(html, /Mermaid diagram:graph TD/);
});

test("does not execute HTML, unsafe URLs or load remote images", () => {
  const html = render('<script>alert(1)</script>\n\n<img src="https://tracker.example/pixel">\n\n[unsafe](javascript:alert%281%29)\n\n![pixel](https://tracker.example/pixel)');
  assert.doesNotMatch(html, /<script|<img|javascript:|src="https:/);
  assert.match(html, /Imagem: pixel/);
});

test("only verified typed BerryBrain references become links", () => {
  const references = [
    { kind: "note", id: 7, stableId: "note-stable", title: "Feira", path: "study/feira.md", current: true, evidenceIds: ["source-note"] },
    { kind: "graph_node", id: 7, stableId: "node-stable", title: "Grafos", current: true, evidenceIds: ["source-node"] },
  ];
  const html = render("[Fonte externa](https://example.com) [Nota](bbref:resolved:note:7) [Nó](bbref:resolved:graph_node:7) [Fonte](bbref:source-note) [Tipo falso](bbref:resolved:attachment:7) [Inexistente](bbref:resolved:note:8)", references);
  assert.match(html, /href="\/berrybrain\/brain\?note=study%2Ffeira.md"/);
  assert.match(html, /href="\/berrybrain\/graph\/nodes\/7"/);
  assert.equal((html.match(/href="\/berrybrain\/brain\?note=study%2Ffeira.md"/g) || []).length, 2);
  assert.doesNotMatch(html, /href="https:\/\/example.com"|bbref:missing|href="\/berrybrain\/brain\?note=undefined/);
  assert.match(html, /<span[^>]*>Tipo falso<\/span>/);
  assert.match(html, /Inexistente/);
});

test("all assistant answer surfaces use the renderer", () => {
  const screen = readFileSync(new URL("../src/components/graph-screen.tsx", import.meta.url), "utf8");
  assert.equal((screen.match(/<AskMarkdown content=\{inference.answer\}/g) || []).length, 2);
  assert.match(screen, /<AskMarkdown content=\{turn.content\}/);
});
