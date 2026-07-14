import { expect, test } from "@playwright/test";

test.describe("Browser AI proxy security", () => {
  test("rejects invalid credentials, private endpoints, and cross-site requests", async ({ request }) => {
    const invalid = await request.post("/api/browser-ai/models", {
      data: { apiKey: "short" },
    });
    expect(invalid.status()).toBe(400);

    const crossSite = await request.post("/api/browser-ai/models", {
      headers: { Origin: "https://evil.example" },
      data: { apiKey: "nvapi-test-key-that-is-long-enough" },
    });
    expect(crossSite.status()).toBe(403);

    const privateProvider = await request.post("/api/browser-ai/models", {
      data: {
        providerUrl: "https://127.0.0.1/v1",
        apiKey: "test-key-that-is-long-enough-for-validation",
      },
    });
    expect(privateProvider.status()).toBe(400);

    const invalidChat = await request.post("/api/browser-ai/chat", {
      data: { apiKey: "short" },
    });
    expect(invalidChat.status()).toBe(400);
  });
});
