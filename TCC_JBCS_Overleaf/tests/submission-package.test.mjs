import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manuscriptPath = path.join(packageRoot, "main.tex");

const readText = (relativePath) => readFile(path.join(packageRoot, relativePath), "utf8");
const normalizeName = (value) =>
  value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, " ")
    .trim()
    .toLowerCase();

function extractAuthors(manuscript) {
  const authors = [...manuscript.matchAll(/\\affil\{\\textbf\{([^{}]+)\}/g)].map(
    (match) => match[1],
  );
  assert.equal(authors.length, 2, "The manuscript must contain exactly two authors");
  return authors;
}

function extractIdentity(manuscript) {
  const [authorName] = extractAuthors(manuscript);
  const orcidMatch = manuscript.match(/https:\/\/orcid\.org\/(\d{4}-\d{4}-\d{4}-[\dX]{4})/i);
  assert.ok(orcidMatch, "An ORCID URL must be present in the manuscript author block");
  return { authorName, orcid: orcidMatch[1].toUpperCase() };
}

function isValidOrcid(orcid) {
  const compact = orcid.replaceAll("-", "");
  if (!/^\d{15}[\dX]$/.test(compact)) return false;
  let total = 0;
  for (const digit of compact.slice(0, 15)) total = (total + Number(digit)) * 2;
  const result = (12 - (total % 11)) % 11;
  return (result === 10 ? "X" : String(result)) === compact.at(-1);
}

async function fetchChecked(url, headers = {}) {
  const response = await fetch(url, {
    headers: { "user-agent": "BerryBrain-publication-package-validator/1.0", ...headers },
    signal: AbortSignal.timeout(20_000),
  });
  assert.equal(response.ok, true, `${url} returned HTTP ${response.status}`);
  return response;
}

test("first-author ORCID checksum and official public identity are valid", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  const { authorName, orcid } = extractIdentity(manuscript);
  assert.equal(isValidOrcid(orcid), true, "The ORCID checksum is invalid");

  const response = await fetchChecked(`https://pub.orcid.org/v3.0/${orcid}/person`, {
    accept: "application/json",
  });
  const person = await response.json();
  const registryName =
    person.name?.["credit-name"]?.value ??
    [person.name?.["given-names"]?.value, person.name?.["family-name"]?.value]
      .filter(Boolean)
      .join(" ");
  assert.ok(registryName, "The ORCID public record does not expose a public author name");
  assert.equal(normalizeName(registryName), normalizeName(authorName));
});

test("manuscript contains every JBCS declaration environment", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  for (const environment of ["contributions", "interests", "acknowledgements", "funding", "materials"]) {
    assert.match(manuscript, new RegExp(`\\\\begin\\{${environment}\\}`));
    assert.match(manuscript, new RegExp(`\\\\end\\{${environment}\\}`));
  }
});

test("AI disclosure includes software engineering and automated-test assistance", async () => {
  const manuscript = (await readFile(manuscriptPath, "utf8")).toLowerCase();
  assert.match(manuscript, /generative ai tools assisted software engineering/);
  assert.match(manuscript, /design and\s+addition of automated tests/);
  assert.match(manuscript, /first author executed\s+the\s+test suites/);
  assert.match(manuscript, /both authors retain full responsibility/);
});

test("submission metadata and gate documents match the manuscript", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  const { authorName, orcid } = extractIdentity(manuscript);
  const authors = extractAuthors(manuscript);
  const title = manuscript.match(/\\title\[[^\]]+\]\{([^{}]+)\}/)?.[1];
  assert.ok(title, "The full manuscript title could not be parsed");

  for (const file of ["SUBMISSION_METADATA.md", "COVER_LETTER_DRAFT.md"]) {
    const text = await readText(file);
    for (const author of authors) {
      assert.ok(
        normalizeName(text).includes(normalizeName(author)),
        `${file} does not contain manuscript author ${author}`,
      );
    }
    assert.ok(text.includes(orcid), `${file} does not contain the manuscript ORCID`);
    assert.ok(text.replace(/\s+/g, " ").includes(title), `${file} does not contain the manuscript title`);
  }

  const coauthorConfirmation = await readText("COAUTHOR_REVIEWER_CONFIRMATION.md");
  assert.ok(normalizeName(coauthorConfirmation).includes(normalizeName(authors[1])));
  assert.match(coauthorConfirmation, /ORCID \| Pending author-supplied identifier/);
  assert.match(coauthorConfirmation, /Coauthorship alone does not imply reviewer consent/);

  const metadata = await readText("SUBMISSION_METADATA.md");
  assert.match(metadata, /JBCS category and area: Information Retrieval/);
  assert.match(metadata, /not submitted/i);
  assert.match(metadata, /DOI: not assigned/i);
});

test("two-author identity and CRediT records are explicit and conservative", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  const authors = extractAuthors(manuscript);
  const orcids = [...manuscript.matchAll(/https:\/\/orcid\.org\/(\d{4}-\d{4}-\d{4}-[\dX]{4})/gi)];
  assert.deepEqual(authors, ["Mateus Almeida de Souza", "Leonardo José Silvestre"]);
  assert.equal(orcids.length, 1, "A second ORCID must not be inferred or fabricated");
  assert.match(
    manuscript,
    /Leonardo José Silvestre: Supervision and Writing -- review\s+\\& editing/,
  );

  const metadata = await readText("SUBMISSION_METADATA.md");
  assert.match(metadata, /Leonardo Jose Silvestre/);
  assert.match(metadata, /ORCID: pending author-supplied identifier/i);
  assert.match(metadata, /not satisfied until he\s+explicitly agrees/i);
});

test("manuscript has final declarations without stale submission placeholders", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  assert.match(manuscript, /Writing -- original\s+draft, and Writing -- review \\& editing/);
  assert.doesNotMatch(manuscript, /ORCID remains mandatory/);
  assert.doesNotMatch(manuscript, /was not supplied/);
  assert.doesNotMatch(manuscript, /must be confirmed by the author/);
  assert.doesNotMatch(manuscript, /This statement must be updated/);
  assert.doesNotMatch(manuscript, /2019202064/);
});

test("citation keys and bibliography entries are an exact set", async () => {
  const manuscript = await readFile(manuscriptPath, "utf8");
  const bibliography = await readText("refs.bib");
  const cited = new Set(
    [...manuscript.matchAll(/\\cite\{([^}]+)\}/g)].flatMap((match) =>
      match[1].split(",").map((key) => key.trim()),
    ),
  );
  const defined = new Set([...bibliography.matchAll(/@[a-zA-Z]+\{([^,]+),/g)].map((match) => match[1]));
  assert.deepEqual([...cited].sort(), [...defined].sort());
});

test("compiled artifact exists and package excludes build debris", async () => {
  const pdfPath = path.join(packageRoot, "main.pdf");
  const pdf = await readFile(pdfPath);
  assert.equal(pdf.subarray(0, 5).toString(), "%PDF-");
  assert.ok((await stat(pdfPath)).size > 100_000, "The compiled PDF is unexpectedly small");

  const names = await readdir(packageRoot);
  const prohibited = names.filter((name) =>
    name === "output.pdf" || /\.(aux|bbl|blg|log|out|toc|fdb_latexmk|fls|synctex\.gz)$/.test(name),
  );
  assert.deepEqual(prohibited, []);
});

test("compiled PDF matches the audited SHA-256", async () => {
  const pdf = await readFile(path.join(packageRoot, "main.pdf"));
  const audit = await readText("EVIDENCE_AUDIT.md");
  const recordedHash = audit.match(/Compiled PDF SHA-256: `([a-f0-9]{64})`/)?.[1];
  assert.ok(recordedHash, "EVIDENCE_AUDIT.md does not contain a valid PDF SHA-256");
  assert.equal(createHash("sha256").update(pdf).digest("hex"), recordedHash);
});

test("current JBCS submission page still exposes the validated policy", async () => {
  const compliance = await readText("JBCS_COMPLIANCE.md");
  const submissionsUrl = compliance.match(/https:\/\/journals-sol\.sbc\.org\.br\/index\.php\/jbcs\/about\/submissions/)?.[0];
  assert.ok(submissionsUrl, "The official submissions URL is missing from the compliance report");

  const response = await fetchChecked(submissionsUrl);
  const html = (await response.text())
    .replace(/<[^>]*>/g, " ")
    .replace(/&(?:nbsp|amp);|&#160;/g, " ")
    .replace(/\s+/g, " ")
    .toLowerCase();

  for (const policyMarker of [
    "jbcs template",
    "xelatex",
    "single-blind review",
    "author's contribution",
    "cover letter",
    "commits to serving as a reviewer for up to two papers",
  ]) {
    assert.ok(html.includes(policyMarker), `Current JBCS page is missing policy marker: ${policyMarker}`);
  }
});

test("potential reviewer research resolves to current institutional profiles", async () => {
  const research = await readText("POTENTIAL_REVIEWERS.md");
  const candidates = research
    .split(/^## /m)
    .slice(1)
    .map((section) => {
      const [name, ...bodyLines] = section.split("\n");
      const body = bodyLines.join("\n");
      return {
        name: name.trim(),
        email: body.match(/Institutional email: ([^\s]+)/)?.[1],
        profile: body.match(/Official profile: <(https:[^>]+)>/)?.[1],
        body,
      };
    })
    .filter((candidate) => candidate.profile);

  assert.ok(candidates.length > 0, "No institutional reviewer profile is recorded");
  for (const candidate of candidates) {
    assert.ok(candidate.email, `${candidate.name} has no institutional email`);
    assert.match(candidate.body, /Highest degree reported by the institutional profile: PhD/);
    const response = await fetchChecked(candidate.profile);
    const html = normalizeName(await response.text());
    assert.ok(html.includes(normalizeName(candidate.name)), `${candidate.name} is absent from the profile`);
    assert.ok(html.includes(normalizeName(candidate.email)), `${candidate.email} is absent from the profile`);
    assert.match(html, /\bph d\b|\bphd\b/);
  }
});
