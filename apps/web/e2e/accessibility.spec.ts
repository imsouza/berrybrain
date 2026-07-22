import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const WCAG_TAGS = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
  "wcag22aa",
];

async function expectNoWcagViolations(page: Page) {
  const result = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();
  const violations = result.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    targets: violation.nodes.map((node) => node.target),
  }));
  expect(violations, JSON.stringify(violations, null, 2)).toEqual([]);
}

test.describe("WCAG 2.2 AA automated gate", () => {
  test("landing page has no detectable WCAG A/AA violations", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expectNoWcagViolations(page);
  });

  test("login page has no detectable WCAG A/AA violations", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in to this local instance." })).toBeVisible();
    await expectNoWcagViolations(page);
  });

  test("keyboard focus is visible and reduced motion disables long animation", async ({
    page,
  }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus-visible");
    await expect(focused).toBeVisible();
    const outline = await focused.evaluate((element) =>
      getComputedStyle(element).outlineStyle,
    );
    expect(outline).not.toBe("none");
    const longAnimations = await page.evaluate(() =>
      document
        .getAnimations()
        .filter((animation) => Number(animation.effect?.getTiming().duration || 0) > 100)
        .length,
    );
    expect(longAnimations).toBe(0);
  });
});
