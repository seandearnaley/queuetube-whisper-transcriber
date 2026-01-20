import { test, expect } from "@playwright/test";

test("loads the queue dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /QueueTube Whisper/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Add to queue/i })).toBeVisible();
});
