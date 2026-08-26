import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const nodeModules = process.env.QCARE_NODE_MODULES;
if (!nodeModules) throw new Error("QCARE_NODE_MODULES must point to the bundled node_modules directory");
const { chromium } = require(path.join(nodeModules, "playwright"));

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const baseUrl = process.env.QCARE_APP_URL || "http://127.0.0.1:8501";
const output = path.join(root, "submission", "screenshots");
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QCARE_BROWSER_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 1180, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", error => errors.push(error.message));
page.on("console", message => {
  if (message.type() === "error") errors.push(`console: ${message.text()}`);
});

async function unique(locator, label) {
  const count = await locator.count();
  if (count !== 1) throw new Error(`Expected one ${label}; found ${count}`);
  return locator;
}

async function positionAt(locator, top = 80) {
  await locator.scrollIntoViewIfNeeded();
  await locator.evaluate((element, topOffset) => {
    element.scrollIntoView({ block: "start", inline: "nearest", behavior: "instant" });
    const scroller = element.closest('[data-testid="stMain"]');
    if (scroller) {
      scroller.scrollBy({ top: -topOffset, behavior: "instant" });
    } else {
      window.scrollBy({ top: -topOffset, behavior: "instant" });
    }
  }, top);
}

async function capture(locator, filename, top = 80) {
  await positionAt(locator, top);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(output, filename), fullPage: false });
}

async function heading(name) {
  return unique(page.getByRole("heading", { name, exact: true }), `heading ${name}`);
}

async function openDisclosure(label, expectedHeading) {
  const control = await unique(page.locator("details summary").filter({ hasText: label }), `disclosure ${label}`);
  await control.click();
  const target = await heading(expectedHeading);
  await target.waitFor({ state: "visible", timeout: 10000 });
  await page.waitForTimeout(800);
  return target;
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.waitForTimeout(5000);
const brand = await unique(page.locator("div.workstation-brand"), "Q-CARE hero brand");
await brand.waitFor({ state: "visible", timeout: 30000 });
await positionAt(brand, 90);
await page.screenshot({ path: path.join(output, "01_full_page_hero.png"), fullPage: false });

const analyse = await unique(page.getByRole("button", { name: "ANALYSE PROFILE", exact: true }), "Analyse button");
await analyse.click();
const liveHeading = await heading("Live model assessment");
await liveHeading.waitFor({ state: "visible", timeout: 30000 });
await capture(liveHeading, "02_live_patient_assessment.png");
const agreement = await unique(page.locator("div.agreement-line"), "agreement panel");
await capture(agreement, "03_model_agreement.png", 110);
await capture(await heading("VQC performance transparency"), "04_vqc_transparency.png");
await capture(await heading("Similar historical benchmark records"), "05_similar_records.png");

const uploadMode = await unique(page.getByText("Upload biomedical dataset", { exact: true }), "upload entry path");
await uploadMode.click();
const fileInputLocator = page.locator('input[type="file"]');
await fileInputLocator.waitFor({ state: "attached", timeout: 10000 });
const fileInput = await unique(fileInputLocator, "CSV file input");
const sourceCsv = fs.readFileSync(path.join(root, "artifacts", "live_vqc", "reference_records.csv"), "utf8").trim().split("\n");
const columns = sourceCsv[0].split(",");
const targetIndex = columns.indexOf("target");
const reordered = ["target", ...columns.filter(column => column !== "target")];
const captureCsv = path.join(os.tmpdir(), "qcare_capture_health.csv");
fs.writeFileSync(captureCsv, [reordered.join(","), ...sourceCsv.slice(1).map(line => {
  const values = line.split(",");
  return [values[targetIndex], ...values.filter((_, index) => index !== targetIndex)].join(",");
})].join("\n") + "\n");
await fileInput.setInputFiles(captureCsv);
await page.getByText("Detected 320 rows and 9 columns.", { exact: true }).waitFor({ state: "visible", timeout: 10000 });
const healthButtonLocator = page.getByRole("button", { name: "RUN DATA HEALTH CHECK", exact: true });
await healthButtonLocator.waitFor({ state: "visible", timeout: 10000 });
const healthButton = await unique(healthButtonLocator, "data health button");
await healthButton.click();
fs.unlinkSync(captureCsv);
const healthHeading = await openDisclosure("Data health check", "Data health check");
await capture(healthHeading, "06_data_health_check.png");

const featureHeading = await openDisclosure("Feature engineering", "Feature reduction");
await capture(featureHeading, "07_feature_reduction.png");
const benchmarkHeading = await openDisclosure("Classical / quantum benchmark", "Three-model comparison");
await capture(benchmarkHeading, "08_three_model_comparison.png");
const circuitHeading = await openDisclosure("Actual quantum circuits", "QSVC circuit");
await capture(circuitHeading, "09_quantum_circuits.png");
const robustnessHeading = await openDisclosure("Robustness", "Frozen robustness experiments");
await capture(robustnessHeading, "10_robustness.png");
const externalHeading = await openDisclosure("Dataset compatibility & transportability", "External transportability");
await capture(externalHeading, "11_external_transportability.png");
await page.waitForTimeout(1200);
await capture(await heading("Feature transportability"), "12_feature_transportability.png");
const evidenceHeading = await openDisclosure("Q-CARE model evidence report", "Q-CARE model evidence report");
await capture(evidenceHeading, "13_final_evidence_report.png");

await browser.close();
if (errors.length) throw new Error(`Browser errors: ${errors.join(" | ")}`);
console.log("Single-page workstation screenshots captured");
