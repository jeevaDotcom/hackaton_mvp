import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const nodeModules = process.env.QCARE_NODE_MODULES;
if (!nodeModules) {
  throw new Error("QCARE_NODE_MODULES must point to the bundled node_modules directory");
}
const { chromium } = require(path.join(nodeModules, "playwright"));

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const baseUrl = process.env.QCARE_APP_URL || "http://127.0.0.1:8520";
const screenshots = path.join(root, "submission", "screenshots");
const backup = path.join(root, "submission", "demo_backup");

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QCARE_BROWSER_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 956, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));

async function settle(expectedText) {
  await page.getByText(expectedText, { exact: true }).last().waitFor({ state: "visible", timeout: 30000 });
  await page.waitForTimeout(700);
}

async function navigate(label, expectedHeading) {
  const radio = page.getByText(label, { exact: true });
  if ((await radio.count()) !== 1) {
    throw new Error(`Expected one navigation label for ${label}`);
  }
  await radio.click();
  await settle(expectedHeading);
  await page.getByText(expectedHeading, { exact: true }).last().scrollIntoViewIfNeeded();
  await page.waitForTimeout(250);
}

async function capture(file, options = {}) {
  await page.screenshot({ path: file, fullPage: false, ...options });
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
await settle("Q-CARE");
await capture(path.join(screenshots, "01_overview.png"));
await capture(path.join(screenshots, "11_demo_hero.png"));
await capture(path.join(backup, "01_demo_hero.png"));

await navigate("Robustness & Shift", "Robustness & shift");
await capture(path.join(screenshots, "06_external_shift.png"));
await capture(path.join(backup, "04_external_shift.png"));

const featureHeading = page.getByText("Feature transportability", { exact: true });
if ((await featureHeading.count()) !== 1) throw new Error("Feature transportability heading missing");
await featureHeading.scrollIntoViewIfNeeded();
await page.waitForTimeout(500);
await capture(path.join(screenshots, "12_feature_transportability.png"));

const creatinineHeading = page.getByText("Serum-creatinine cohort comparison", { exact: true });
if ((await creatinineHeading.count()) !== 1) throw new Error("Creatinine comparison heading missing");
await creatinineHeading.scrollIntoViewIfNeeded();
await page.waitForTimeout(400);
await capture(path.join(screenshots, "13_creatinine_comparison.png"));

await navigate("Quantum Evidence", "Quantum evidence");
await capture(path.join(screenshots, "08_quantum_evidence.png"));
const finalHeading = page.getByText("Final evidence summary", { exact: true });
if ((await finalHeading.count()) !== 1) throw new Error("Final evidence summary heading missing");
await finalHeading.scrollIntoViewIfNeeded();
await page.waitForTimeout(350);
await capture(path.join(backup, "05_evidence_verdict.png"));

await navigate("Overview", "Q-CARE");
await page.setViewportSize({ width: 480, height: 900 });
await page.waitForTimeout(350);
await capture(path.join(screenshots, "mobile_overview.png"));

await page.setViewportSize({ width: 956, height: 1000 });
await navigate("Robustness & Shift", "Robustness & shift");
await page.setViewportSize({ width: 480, height: 900 });
await page.waitForTimeout(350);
await capture(path.join(screenshots, "mobile_external_shift.png"));

await browser.close();
if (errors.length) {
  throw new Error(`Browser page errors: ${errors.join(" | ")}`);
}
console.log("Phase 3D screenshots captured");
