import { defineConfig, devices } from "@playwright/test";

const BROWSER_WS_ENDPOINT = process.env.PLAYWRIGHT_SERVICE_URL;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html"],
    ["list"],
    ["json", { outputFile: "test-results/results.json" }],
  ],
  use: {
    // When running with a sidecar browser, the browser needs to reach the app container
    baseURL: BROWSER_WS_ENDPOINT
      ? "http://client:3000"
      : "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    connectOptions: BROWSER_WS_ENDPOINT
      ? { wsEndpoint: BROWSER_WS_ENDPOINT }
      : undefined,
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: BROWSER_WS_ENDPOINT
          ? undefined
          : {
              args: ["--no-sandbox", "--disable-setuid-sandbox"],
            },
      },
    },
    {
      name: "firefox",
      use: {
        ...devices["Desktop Firefox"],
      },
    },
    {
      name: "webkit",
      use: {
        ...devices["Desktop Safari"],
      },
    },
  ],
});
