import { expect, test } from "@playwright/test";

test.describe("Browser-only persistence", () => {
  test.skip(
    process.env.E2E_BROWSER_STORAGE_MODE !== "browser",
    "Requires a build with NEXT_PUBLIC_BERRYBRAIN_STORAGE_MODE=browser.",
  );
  test.setTimeout(90_000);
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("bb_tour_seen", "1");
      localStorage.setItem("bb_nome", "Browser owner");
    });
  });

  test("persists notes and restores a complete verified backup", async ({ page }) => {
    const unexpectedApiRequests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.includes("/api/v1/")) unexpectedApiRequests.push(request.url());
    });
    await page.goto("/brain");
    await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();

    const quickNote = page.getByRole("textbox", { name: "Quick note draft" });
    await quickNote.fill("# Browser persistence test\n\nThis note survives reload and backup restore.");
    await page.getByRole("button", { name: "Create note" }).click();
    await expect(page.getByRole("textbox", { name: "Editor" })).toHaveValue(
      /This note survives reload and backup restore\./,
    );
    await expect(page.getByText("Saved", { exact: true }).first()).toBeVisible();
    await page.locator('input[type="file"]').first().setInputFiles({
      name: "evidence.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("Browser attachment evidence"),
    });
    await expect(page.getByText("evidence.txt", { exact: true })).toBeVisible();
    await page.reload();

    await page.getByText("Browser persistence test", { exact: true }).first().click();
    await expect(page.getByRole("textbox", { name: "Editor" })).toHaveValue(
      /This note survives reload and backup restore\./,
    );

    await page.getByRole("button", { name: "Settings", exact: true }).click();
    await expect(page.getByText("Data portability", { exact: true })).toBeVisible();
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export all data" }).click();
    const download = await downloadPromise;
    const backupPath = await download.path();
    expect(backupPath).toBeTruthy();

    const backupText = await (await import("node:fs/promises")).readFile(backupPath!, "utf8");
    const backup = JSON.parse(backupText);
    expect(backup.product).toBe("BerryBrain");
    expect(backup.formatVersion).toBe(1);
    expect(backup.checksum?.algorithm).toBe("SHA-256");
    expect(backup.stores.notes).toHaveLength(1);
    expect(backup.stores.attachments).toHaveLength(1);
    expect(backup.stores.attachments[0].blob.__berrybrainType).toBe("Blob");

    const tamperedBackup = structuredClone(backup);
    tamperedBackup.stores.notes[0].title = "Tampered title";
    page.once("dialog", (dialog) => dialog.accept());
    await page.locator('input[type="file"][accept*="berrybrain"]').setInputFiles({
      name: "tampered.berrybrain.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(tamperedBackup)),
    });
    await expect(page.getByText(/Backup checksum does not match/)).toBeVisible();

    await page.evaluate(async () => {
      await new Promise<void>((resolve, reject) => {
        const request = indexedDB.open("berrybrain-webapp", 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const database = request.result;
          const transaction = database.transaction(["notes", "attachments"], "readwrite");
          transaction.objectStore("notes").clear();
          transaction.objectStore("attachments").clear();
          transaction.oncomplete = () => {
            database.close();
            resolve();
          };
          transaction.onerror = () => reject(transaction.error);
        };
      });
    });
    await page.reload();
    await expect(page.getByText("Browser persistence test", { exact: true })).toHaveCount(0);

    await page.getByRole("button", { name: "Settings", exact: true }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.locator('input[type="file"][accept*="berrybrain"]').setInputFiles(backupPath!);
    await expect(page.getByText("Backup restored. Reloading...", { exact: true })).toBeVisible();
    const restoredCounts = await page.evaluate(async () =>
      new Promise<{ notes: number; attachments: number }>((resolve, reject) => {
        const request = indexedDB.open("berrybrain-webapp", 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const database = request.result;
          const transaction = database.transaction(["notes", "attachments"], "readonly");
          const notesRequest = transaction.objectStore("notes").count();
          const attachmentsRequest = transaction.objectStore("attachments").count();
          transaction.oncomplete = () => {
            database.close();
            resolve({ notes: notesRequest.result, attachments: attachmentsRequest.result });
          };
          transaction.onerror = () => reject(transaction.error);
        };
      }),
    );
    expect(restoredCounts).toEqual({ notes: 1, attachments: 1 });
    await expect(page.getByText("Browser persistence test", { exact: true }).first()).toBeVisible({ timeout: 15_000 });
    await page.getByText("Browser persistence test", { exact: true }).first().click();
    await expect(page.getByText("evidence.txt", { exact: true })).toBeVisible();
    expect(unexpectedApiRequests).toEqual([]);
  });
});
