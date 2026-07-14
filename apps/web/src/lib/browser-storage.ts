import type { NoteDetail, NoteSummary, Stats } from "@/types";

export const BROWSER_STORAGE_MODE =
  process.env.NEXT_PUBLIC_BERRYBRAIN_STORAGE_MODE === "browser";

const DB_NAME = "berrybrain-webapp";
const DB_VERSION = 1;
const BACKUP_FORMAT_VERSION = 1;
const MAX_BACKUP_BYTES = 256 * 1024 * 1024;
const MAX_BACKUP_RECORDS = 100_000;
const SENSITIVE_PREFERENCE = /(api[_-]?key|token|secret|password|session|credential)/i;

const STORE_NAMES = [
  "notes",
  "attachments",
  "graphNodes",
  "graphEdges",
  "insights",
  "jobs",
  "settings",
  "metadata",
] as const;

type StoreName = (typeof STORE_NAMES)[number];

type StoredNote = NoteDetail & {
  createdAt: string;
  updatedAt: string;
};

type StoredAttachment = {
  id: number;
  notePath: string;
  filename: string;
  mimeType: string;
  category: "image" | "video" | "audio" | "other";
  sizeBytes: number;
  blob: Blob;
  createdAt: string;
};

export type BrowserAttachment = Omit<StoredAttachment, "blob" | "notePath"> & {
  downloadUrl: string;
};

export const MAX_BROWSER_ATTACHMENT_BYTES = 50 * 1024 * 1024;

type EncodedValue =
  | null
  | string
  | number
  | boolean
  | EncodedValue[]
  | { [key: string]: EncodedValue };

type BackupPayload = {
  product: "BerryBrain";
  formatVersion: number;
  createdAt: string;
  storageMode: "browser";
  stores: Record<StoreName, EncodedValue[]>;
  preferences: Record<string, string>;
};

type BackupEnvelope = BackupPayload & {
  checksum: { algorithm: "SHA-256"; value: string };
};

function toNoteDetail(record: StoredNote): NoteDetail {
  return {
    title: record.title,
    path: record.path,
    folder: record.folder,
    content: record.content,
    content_hash: record.content_hash,
  };
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("IndexedDB request failed."));
  });
}

function transactionDone(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onabort = () => reject(transaction.error || new Error("IndexedDB transaction aborted."));
    transaction.onerror = () => reject(transaction.error || new Error("IndexedDB transaction failed."));
  });
}

export function openBrowserDatabase(): Promise<IDBDatabase> {
  if (typeof indexedDB === "undefined") {
    return Promise.reject(new Error("This browser does not support IndexedDB."));
  }
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains("notes")) {
        database.createObjectStore("notes", { keyPath: "path" });
      }
      for (const storeName of STORE_NAMES) {
        if (storeName === "notes" || database.objectStoreNames.contains(storeName)) continue;
        database.createObjectStore(storeName, { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("Could not open browser storage."));
    request.onblocked = () => reject(new Error("Browser storage upgrade is blocked by another tab."));
  });
}

async function withStore<T>(
  storeName: StoreName,
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction(storeName, mode);
    const done = transactionDone(transaction);
    const result = await requestResult(operation(transaction.objectStore(storeName)));
    await done;
    return result;
  } finally {
    database.close();
  }
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function titleFromContent(content: string) {
  const firstLine = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);
  return firstLine?.replace(/^#{1,6}\s+/, "").slice(0, 120) || "Untitled note";
}

function slugify(value: string) {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 72) || "untitled-note";
}

export async function initializeBrowserStorage() {
  const database = await openBrowserDatabase();
  database.close();
  let persistent = false;
  if (navigator.storage?.persist) {
    persistent = await navigator.storage.persist().catch(() => false);
  }
  return persistent;
}

export async function browserStorageStatus() {
  const estimate = await navigator.storage?.estimate?.();
  const persisted = navigator.storage?.persisted
    ? await navigator.storage.persisted().catch(() => false)
    : false;
  return {
    persisted,
    usage: estimate?.usage || 0,
    quota: estimate?.quota || 0,
  };
}

export async function listBrowserNotes(): Promise<NoteSummary[]> {
  const records = await withStore<StoredNote[]>("notes", "readonly", (store) => store.getAll());
  return records
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
    .map(({ title, path, folder }) => ({ title, path, folder }));
}

export async function getBrowserNote(path: string): Promise<NoteDetail | null> {
  const record = await withStore<StoredNote | undefined>("notes", "readonly", (store) => store.get(path));
  if (!record) return null;
  return toNoteDetail(record);
}

export async function createBrowserNote(content = ""): Promise<NoteDetail> {
  const title = titleFromContent(content);
  const base = slugify(title);
  const database = await openBrowserDatabase();
  try {
    let path = `inbox/${base}.md`;
    let suffix = 2;
    while (await requestResult(database.transaction("notes", "readonly").objectStore("notes").get(path))) {
      path = `inbox/${base}-${suffix}.md`;
      suffix += 1;
    }
    const now = new Date().toISOString();
    const record: StoredNote = {
      title,
      path,
      folder: "inbox",
      content,
      content_hash: await sha256(content),
      createdAt: now,
      updatedAt: now,
    };
    const transaction = database.transaction("notes", "readwrite");
    const done = transactionDone(transaction);
    transaction.objectStore("notes").add(record);
    await done;
    return toNoteDetail(record);
  } finally {
    database.close();
  }
}

export async function saveBrowserNote(note: NoteDetail, content: string): Promise<NoteDetail> {
  const existing = await withStore<StoredNote | undefined>("notes", "readonly", (store) => store.get(note.path));
  if (!existing) throw new Error("The note no longer exists in browser storage.");
  const updated: StoredNote = {
    ...existing,
    ...note,
    content,
    content_hash: await sha256(content),
    updatedAt: new Date().toISOString(),
  };
  await withStore<IDBValidKey>("notes", "readwrite", (store) => store.put(updated));
  return toNoteDetail(updated);
}

export async function deleteBrowserNote(path: string): Promise<void> {
  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction(["notes", "attachments"], "readwrite");
    const done = transactionDone(transaction);
    transaction.objectStore("notes").delete(path);
    const attachmentStore = transaction.objectStore("attachments");
    const attachments = await requestResult(attachmentStore.getAll()) as StoredAttachment[];
    for (const attachment of attachments) {
      if (attachment.notePath === path) attachmentStore.delete(attachment.id);
    }
    await done;
  } finally {
    database.close();
  }
}

export async function renameBrowserNote(note: NoteDetail, title: string): Promise<NoteDetail> {
  const existing = await withStore<StoredNote | undefined>("notes", "readonly", (store) => store.get(note.path));
  if (!existing) throw new Error("The note no longer exists in browser storage.");
  const folder = note.folder || "inbox";
  const base = slugify(title);
  let nextPath = `${folder}/${base}.md`;
  let suffix = 2;
  while (nextPath !== note.path && (await getBrowserNote(nextPath))) {
    nextPath = `${folder}/${base}-${suffix}.md`;
    suffix += 1;
  }
  const updated: StoredNote = {
    ...existing,
    title: title.trim(),
    path: nextPath,
    updatedAt: new Date().toISOString(),
  };
  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction(["notes", "attachments"], "readwrite");
    const done = transactionDone(transaction);
    const noteStore = transaction.objectStore("notes");
    if (nextPath !== note.path) noteStore.delete(note.path);
    noteStore.put(updated);
    if (nextPath !== note.path) {
      const attachmentStore = transaction.objectStore("attachments");
      const attachments = await requestResult(attachmentStore.getAll()) as StoredAttachment[];
      for (const attachment of attachments) {
        if (attachment.notePath === note.path) attachmentStore.put({ ...attachment, notePath: nextPath });
      }
    }
    await done;
  } finally {
    database.close();
  }
  return toNoteDetail(updated);
}

function attachmentCategory(mimeType: string): StoredAttachment["category"] {
  if (mimeType.startsWith("image/")) return "image";
  if (mimeType.startsWith("video/")) return "video";
  if (mimeType.startsWith("audio/")) return "audio";
  return "other";
}

function toBrowserAttachment(record: StoredAttachment): BrowserAttachment {
  return {
    id: record.id,
    filename: record.filename,
    mimeType: record.mimeType,
    category: record.category,
    sizeBytes: record.sizeBytes,
    createdAt: record.createdAt,
    downloadUrl: URL.createObjectURL(record.blob),
  };
}

export async function listBrowserAttachments(notePath: string): Promise<BrowserAttachment[]> {
  const records = await withStore<StoredAttachment[]>("attachments", "readonly", (store) => store.getAll());
  return records
    .filter((record) => record.notePath === notePath)
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
    .map(toBrowserAttachment);
}

export async function createBrowserAttachment(notePath: string, file: File): Promise<BrowserAttachment> {
  if (file.size > MAX_BROWSER_ATTACHMENT_BYTES) {
    throw new Error("Browser attachments are limited to 50 MB per file.");
  }
  const record: StoredAttachment = {
    id: Date.now() * 1000 + crypto.getRandomValues(new Uint16Array(1))[0] % 1000,
    notePath,
    filename: file.name.slice(0, 255),
    mimeType: file.type || "application/octet-stream",
    category: attachmentCategory(file.type || "application/octet-stream"),
    sizeBytes: file.size,
    blob: file,
    createdAt: new Date().toISOString(),
  };
  await withStore<IDBValidKey>("attachments", "readwrite", (store) => store.add(record));
  return toBrowserAttachment(record);
}

export async function deleteBrowserAttachment(id: number): Promise<void> {
  await withStore<undefined>("attachments", "readwrite", (store) => store.delete(id));
}

export async function browserStats(): Promise<Stats> {
  const notes = await listBrowserNotes();
  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction(["graphEdges", "metadata", "jobs"], "readonly");
    const done = transactionDone(transaction);
    const [connections, metadata, pendingJobs] = await Promise.all([
      requestResult(transaction.objectStore("graphEdges").count()),
      requestResult(transaction.objectStore("metadata").count()),
      requestResult(transaction.objectStore("jobs").getAll()).then((jobs: Array<{ status?: string }>) =>
        jobs.filter((job) => job.status === "pending").length,
      ),
    ]);
    await done;
    return { notes: notes.length, connections, metadata, jobs: { pending: pendingJobs } };
  } finally {
    database.close();
  }
}

function bytesToBase64(bytes: Uint8Array) {
  let output = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    output += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(output);
}

function base64ToBytes(value: string) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

async function encodeValue(value: unknown): Promise<EncodedValue> {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return value;
  }
  if (value instanceof Date) return { __berrybrainType: "Date", value: value.toISOString() };
  if (value instanceof Blob) {
    return {
      __berrybrainType: "Blob",
      mime: value.type,
      data: bytesToBase64(new Uint8Array(await value.arrayBuffer())),
    };
  }
  if (value instanceof ArrayBuffer) {
    return { __berrybrainType: "ArrayBuffer", data: bytesToBase64(new Uint8Array(value)) };
  }
  if (ArrayBuffer.isView(value)) {
    return {
      __berrybrainType: "ArrayBuffer",
      data: bytesToBase64(new Uint8Array(value.buffer, value.byteOffset, value.byteLength)),
    };
  }
  if (Array.isArray(value)) return Promise.all(value.map(encodeValue));
  if (typeof value === "object") {
    const encoded: Record<string, EncodedValue> = {};
    for (const [key, child] of Object.entries(value)) encoded[key] = await encodeValue(child);
    return encoded;
  }
  throw new Error(`Unsupported backup value: ${typeof value}`);
}

function decodeValue(value: EncodedValue): unknown {
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map(decodeValue);
  if (value.__berrybrainType === "Date" && typeof value.value === "string") return new Date(value.value);
  if (value.__berrybrainType === "Blob" && typeof value.data === "string") {
    return new Blob([base64ToBytes(value.data)], { type: typeof value.mime === "string" ? value.mime : "" });
  }
  if (value.__berrybrainType === "ArrayBuffer" && typeof value.data === "string") {
    return base64ToBytes(value.data).buffer;
  }
  return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, decodeValue(child)]));
}

function exportablePreferences() {
  const preferences: Record<string, string> = {};
  for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index);
    if (!key?.startsWith("bb_") || key === "bb_analytics_consent" || SENSITIVE_PREFERENCE.test(key)) continue;
    const value = localStorage.getItem(key);
    if (value !== null) preferences[key] = value;
  }
  return preferences;
}

export async function exportBrowserBackup(): Promise<Blob> {
  const database = await openBrowserDatabase();
  try {
    const stores = {} as Record<StoreName, EncodedValue[]>;
    for (const storeName of STORE_NAMES) {
      const transaction = database.transaction(storeName, "readonly");
      const done = transactionDone(transaction);
      const records = await requestResult(transaction.objectStore(storeName).getAll());
      await done;
      stores[storeName] = (await encodeValue(records)) as EncodedValue[];
    }
    const payload: BackupPayload = {
      product: "BerryBrain",
      formatVersion: BACKUP_FORMAT_VERSION,
      createdAt: new Date().toISOString(),
      storageMode: "browser",
      stores,
      preferences: exportablePreferences(),
    };
    const checksum = await sha256(JSON.stringify(payload));
    const envelope: BackupEnvelope = {
      ...payload,
      checksum: { algorithm: "SHA-256", value: checksum },
    };
    return new Blob([JSON.stringify(envelope)], { type: "application/json" });
  } finally {
    database.close();
  }
}

function assertBackupShape(value: unknown): asserts value is BackupEnvelope {
  if (!value || typeof value !== "object") throw new Error("Backup is not a JSON object.");
  const backup = value as Partial<BackupEnvelope>;
  if (backup.product !== "BerryBrain" || backup.formatVersion !== BACKUP_FORMAT_VERSION) {
    throw new Error("Unsupported BerryBrain backup format.");
  }
  if (!backup.stores || typeof backup.stores !== "object") throw new Error("Backup stores are missing.");
  if (!backup.preferences || typeof backup.preferences !== "object" || Array.isArray(backup.preferences)) {
    throw new Error("Backup preferences are invalid.");
  }
  if (!backup.checksum || backup.checksum.algorithm !== "SHA-256" || typeof backup.checksum.value !== "string") {
    throw new Error("Backup checksum is missing.");
  }
  let records = 0;
  for (const storeName of STORE_NAMES) {
    const store = backup.stores[storeName];
    if (!Array.isArray(store)) throw new Error(`Backup store ${storeName} is invalid.`);
    records += store.length;
  }
  if (records > MAX_BACKUP_RECORDS) throw new Error("Backup contains too many records.");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function validRecordKey(value: unknown): value is IDBValidKey {
  return (typeof value === "string" && value.length > 0 && value.length <= 2_048)
    || (typeof value === "number" && Number.isFinite(value));
}

function validateDecodedStores(stores: Record<StoreName, unknown[]>) {
  for (const storeName of STORE_NAMES) {
    const seenKeys = new Set<string>();
    for (const value of stores[storeName]) {
      if (!isRecord(value)) throw new Error(`Backup store ${storeName} contains a non-object record.`);
      const key = storeName === "notes" ? value.path : value.id;
      if (!validRecordKey(key)) throw new Error(`Backup store ${storeName} contains an invalid key.`);
      const normalizedKey = `${typeof key}:${String(key)}`;
      if (seenKeys.has(normalizedKey)) throw new Error(`Backup store ${storeName} contains duplicate keys.`);
      seenKeys.add(normalizedKey);

      if (storeName === "notes") {
        if (
          typeof value.title !== "string"
          || typeof value.path !== "string"
          || typeof value.content !== "string"
          || typeof value.createdAt !== "string"
          || typeof value.updatedAt !== "string"
        ) {
          throw new Error("Backup contains an invalid note record.");
        }
      }
      if (storeName === "attachments") {
        if (
          typeof value.id !== "number"
          || typeof value.notePath !== "string"
          || typeof value.filename !== "string"
          || typeof value.mimeType !== "string"
          || typeof value.sizeBytes !== "number"
          || !(value.blob instanceof Blob)
          || value.blob.size !== value.sizeBytes
        ) {
          throw new Error("Backup contains an invalid attachment record.");
        }
      }
    }
  }
}

export async function importBrowserBackup(file: File): Promise<void> {
  if (file.size > MAX_BACKUP_BYTES) throw new Error("Backup is larger than 256 MB.");
  const text = await file.text();
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("Backup is not valid JSON.");
  }
  assertBackupShape(parsed);
  const { checksum, ...payload } = parsed;
  const actualChecksum = await sha256(JSON.stringify(payload));
  if (actualChecksum !== checksum.value) throw new Error("Backup checksum does not match. The file may be damaged.");

  const decoded = {} as Record<StoreName, unknown[]>;
  for (const storeName of STORE_NAMES) decoded[storeName] = parsed.stores[storeName].map(decodeValue);
  validateDecodedStores(decoded);

  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction([...STORE_NAMES], "readwrite");
    const done = transactionDone(transaction);
    for (const storeName of STORE_NAMES) {
      const store = transaction.objectStore(storeName);
      store.clear();
      for (const record of decoded[storeName]) store.put(record);
    }
    await done;
  } finally {
    database.close();
  }

  for (let index = localStorage.length - 1; index >= 0; index -= 1) {
    const key = localStorage.key(index);
    if (key?.startsWith("bb_") && key !== "bb_analytics_consent") localStorage.removeItem(key);
  }
  for (const [key, value] of Object.entries(parsed.preferences || {})) {
    if (
      key.startsWith("bb_")
      && key.length <= 128
      && key !== "bb_analytics_consent"
      && !SENSITIVE_PREFERENCE.test(key)
      && typeof value === "string"
    ) {
      localStorage.setItem(key, value.slice(0, 100_000));
    }
  }
}

export async function wipeBrowserStorage(): Promise<void> {
  const database = await openBrowserDatabase();
  try {
    const transaction = database.transaction([...STORE_NAMES], "readwrite");
    const done = transactionDone(transaction);
    for (const storeName of STORE_NAMES) transaction.objectStore(storeName).clear();
    await done;
  } finally {
    database.close();
  }
}
