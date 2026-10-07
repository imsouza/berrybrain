import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const source = readFileSync(new URL("../src/components/ask-markdown.tsx", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText.replace(/from "([^"]+)"/g, (_, name) => `from ${JSON.stringify(pathToFileURL(require.resolve(name)).href)}`);
const { AskMarkdown } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const render = (content) => renderToStaticMarkup(React.createElement(AskMarkdown, { content }));

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

test("does not execute HTML, unsafe URLs or load remote images", () => {
  const html = render('<script>alert(1)</script>\n\n<img src="https://tracker.example/pixel">\n\n[unsafe](javascript:alert%281%29)\n\n![pixel](https://tracker.example/pixel)');
  assert.doesNotMatch(html, /<script|<img|javascript:|src="https:/);
  assert.match(html, /Imagem: pixel/);
});

test("links preserve safe destinations and opener protection", () => {
  const html = render("[Fonte](https://example.com/paper)");
  assert.match(html, /href="https:\/\/example.com\/paper"/);
  assert.match(html, /rel="noopener noreferrer"/);
});

test("all assistant answer surfaces use the renderer", () => {
  const screen = readFileSync(new URL("../src/components/graph-screen.tsx", import.meta.url), "utf8");
  assert.equal((screen.match(/<AskMarkdown content=\{inference.answer\}/g) || []).length, 2);
  assert.match(screen, /<AskMarkdown content=\{turn.content\}/);
});
