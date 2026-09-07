import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const nodeModules = process.env.QCARE_NODE_MODULES;
if (!nodeModules) throw new Error("QCARE_NODE_MODULES must point to the bundled node_modules directory");
const { chromium } = require(path.join(nodeModules, "playwright"));

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "submission", "screenshots");
const baseUrl = process.env.QCARE_APP_URL || "http://127.0.0.1:8501";
fs.mkdirSync(output, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: chromium.executablePath() });
const page = await browser.newPage({ viewport: { width: 1280, height: 1100 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", error => errors.push(`page: ${error.message}`));
page.on("console", message => {
  if (message.type() === "error") errors.push(`console: ${message.text()}`);
});

async function one(locator, label) {
  const count = await locator.count();
  if (count !== 1) throw new Error(`Expected one ${label}; found ${count}`);
  return locator;
}

async function captureNear(locator, filename, topPadding = 120) {
  await locator.evaluate(element => element.scrollIntoView({ block: "start", behavior: "instant" }));
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(output, filename), fullPage: false });
}

async function choose(label, option) {
  const controlLocator = page.getByLabel(label, { exact: true });
  await controlLocator.waitFor({ state: "visible", timeout: 10000 });
  const control = await one(controlLocator, `select ${label}`);
  await control.click();
  const choiceLocator = page.getByRole("option", { name: option, exact: true });
  await choiceLocator.waitFor({ state: "visible", timeout: 10000 });
  await (await one(choiceLocator, `option ${option}`)).click();
  await page.waitForTimeout(350);
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.locator("div.workstation-brand").waitFor({ state: "visible", timeout: 30000 });
const scanModeLocator = page.getByRole("radio", { name: "Scan report", exact: true });
await scanModeLocator.waitFor({ state: "visible", timeout: 20000 });
await (await one(scanModeLocator, "Scan report mode")).click();
const scanHeadingLocator = page.getByRole("heading", { name: "Scan report", exact: true });
await scanHeadingLocator.waitFor({ state: "visible", timeout: 20000 });
const scanHeading = await one(scanHeadingLocator, "Scan report heading");
await captureNear(scanHeading, "ocr_01_upload.png", 130);

await (await one(page.getByRole("button", { name: "TRY SAMPLE REPORT", exact: true }), "sample report button")).click();
const extractionHeadingLocator = page.getByRole("heading", { name: "AI / OCR extracted values", exact: true });
await extractionHeadingLocator.waitFor({ state: "visible", timeout: 30000 });
const extractionHeading = await one(extractionHeadingLocator, "extraction heading");
await page.getByText("4 of 8 values detected", { exact: true }).waitFor({ state: "visible", timeout: 20000 });
const extractionStatus = await one(page.locator("div.extraction-status"), "extraction status");
await captureNear(extractionStatus, "ocr_02_extraction.png", 300);

const sourceSummary = await one(page.locator("details summary").filter({ hasText: "Show source · Serum creatinine" }), "creatinine source disclosure");
await sourceSummary.click();
await page.getByText("“Serum Creatinine 2.4 mg/dL”", { exact: true }).waitFor({ state: "visible", timeout: 10000 });
await captureNear(sourceSummary, "ocr_03_source_evidence.png", 330);

const reviewHeading = await one(page.getByRole("heading", { name: "Verify extracted profile", exact: true }), "review heading");
await captureNear(reviewHeading, "ocr_04_researcher_review.png", 100);
const manualBanner = await one(page.locator("div.manual-completion"), "manual completion banner");
await captureNear(manualBanner, "ocr_05_manual_completion.png", 120);

await choose("Albumin · dataset ordinal grade", "1");
await choose("Diabetes mellitus", "No");
await choose("Hypertension", "Yes");
await choose("Appetite · dataset category", "Good");
const confirmLocator = page.getByRole("button", { name: "CONFIRM FEATURE PROFILE", exact: true });
await confirmLocator.waitFor({ state: "visible", timeout: 10000 });
await (await one(confirmLocator, "confirm button")).click();
const healthHeadingLocator = page.getByRole("heading", { name: "Confirmed profile data health", exact: true });
await healthHeadingLocator.waitFor({ state: "visible", timeout: 20000 });
const healthHeading = await one(healthHeadingLocator, "profile health heading");
await page.getByText("8 / 8", { exact: true }).waitFor({ state: "visible", timeout: 10000 });
await captureNear(healthHeading, "ocr_06_confirmed_profile.png", 110);

await (await one(page.getByRole("button", { name: "RUN EXPERIMENT", exact: true }), "run experiment button")).click();
const consensusHeading = await one(page.getByRole("heading", { name: "Model consensus", exact: true }), "consensus heading");
await page.locator("div.consensus-row").first().waitFor({ state: "visible", timeout: 30000 });
await captureNear(consensusHeading, "ocr_07_model_results.png", 130);

const exceptionCount = await page.locator('[data-testid="stException"]').count();
if (exceptionCount) errors.push(`Streamlit exceptions: ${exceptionCount}`);
await browser.close();
if (errors.length) throw new Error(errors.join(" | "));
console.log("Seven Q-CARE OCR MVP screenshots captured with the bundled test browser.");
