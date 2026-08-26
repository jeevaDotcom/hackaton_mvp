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
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QCARE_BROWSER_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 1180, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
const checks = {};

page.on("pageerror", error => errors.push(`page: ${error.message}`));
page.on("console", message => {
  if (message.type() === "error") errors.push(`console: ${message.text()}`);
});

async function one(locator, label) {
  const count = await locator.count();
  if (count !== 1) throw new Error(`Expected one ${label}; found ${count}`);
  return locator;
}

async function requireVisible(locator, label) {
  const count = await locator.count();
  if (count < 1) throw new Error(`Missing ${label}`);
  await locator.first().waitFor({ state: "visible", timeout: 20000 });
  checks[label] = true;
}

async function requirePresent(locator, label) {
  const count = await locator.count();
  if (count < 1) throw new Error(`Missing ${label}`);
  checks[label] = true;
}

async function heading(name) {
  const locator = await one(page.getByRole("heading", { name, exact: true }), `heading ${name}`);
  await locator.waitFor({ state: "visible", timeout: 20000 });
  return locator;
}

async function openDisclosure(label, expectedHeading) {
  const summary = await one(page.locator("details summary").filter({ hasText: label }), `disclosure ${label}`);
  await summary.click();
  await heading(expectedHeading);
  checks[label] = true;
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.locator("div.workstation-brand").waitFor({ state: "visible", timeout: 30000 });
await heading("Hybrid Quantum Clinical Research Platform");
await requireVisible(page.getByText("Q-CARE", { exact: true }), "page loads");
await page.getByRole("button", { name: "ANALYSE PROFILE", exact: true }).waitFor({ state: "visible", timeout: 30000 });
await requireVisible(page.getByRole("button", { name: "ANALYSE PROFILE", exact: true }), "patient inputs render");

const analyse = await one(page.getByRole("button", { name: "ANALYSE PROFILE", exact: true }), "Analyse button");
await analyse.click();
await page.getByText("VQC research model score", { exact: true }).waitFor({ state: "visible", timeout: 30000 });
await heading("Live model assessment");
await requirePresent(page.getByText("RBF SVM", { exact: true }), "RBF prediction works");
await requirePresent(page.getByText("QSVC", { exact: true }), "QSVC prediction works");
await requireVisible(page.getByText("VQC research model score", { exact: true }), "VQC prediction works");
await requireVisible(page.getByText("2 OF 3 AGREE", { exact: true }).or(page.getByText("3 OF 3 AGREE", { exact: true })), "agreement works");
await requireVisible(page.getByText("WEAK — DISPLAY WITH CAUTION", { exact: true }), "VQC caution retained");
await heading("Factors influencing this model output");
checks["perturbation factors render"] = true;
await heading("Similar historical benchmark records");
checks["similar records render"] = true;

const uploadMode = await one(page.getByText("Upload biomedical dataset", { exact: true }), "upload entry path");
await uploadMode.click();
const fileInputLocator = page.locator('input[type="file"]');
await fileInputLocator.waitFor({ state: "attached", timeout: 10000 });
const fileInput = await one(fileInputLocator, "CSV file input");
const sourceLines = fs.readFileSync(path.join(root, "artifacts", "live_vqc", "reference_records.csv"), "utf8").trim().split("\n");
const columns = sourceLines[0].split(",");
const targetIndex = columns.indexOf("target");
const reordered = ["target", ...columns.filter(column => column !== "target")];
const temporaryCsv = path.join(os.tmpdir(), `qcare_live_validation_${process.pid}.csv`);
fs.writeFileSync(temporaryCsv, [reordered.join(","), ...sourceLines.slice(1).map(line => {
  const values = line.split(",");
  return [values[targetIndex], ...values.filter((_, index) => index !== targetIndex)].join(",");
})].join("\n") + "\n");
await fileInput.setInputFiles(temporaryCsv);
await page.getByText("Detected 320 rows and 9 columns.", { exact: true }).waitFor({ state: "visible", timeout: 10000 });
await requireVisible(page.getByText("Detected 320 rows and 9 columns.", { exact: true }), "CSV upload works");
await page.getByRole("button", { name: "RUN DATA HEALTH CHECK", exact: true }).waitFor({ state: "visible", timeout: 10000 });
const healthButton = await one(page.getByRole("button", { name: "RUN DATA HEALTH CHECK", exact: true }), "Data Health button");
await healthButton.click();
fs.unlinkSync(temporaryCsv);
await openDisclosure("Data health check", "Data health check");
await requireVisible(page.getByText("READY", { exact: true }), "Data Health Check works");
await requireVisible(page.getByText("8/8", { exact: true }), "required feature coverage");

await openDisclosure("Feature engineering", "Feature reduction");
checks["feature reduction section renders"] = true;
await openDisclosure("Classical / quantum benchmark", "Three-model comparison");
checks["three-model benchmark renders"] = true;
await openDisclosure("Actual quantum circuits", "QSVC circuit");
await heading("VQC circuit");
checks["both quantum circuit visuals render"] = true;
await openDisclosure("Robustness", "Frozen robustness experiments");
checks["robustness section renders"] = true;
await openDisclosure("Dataset compatibility & transportability", "External transportability");
await requireVisible(page.getByText("Target comparability was PARTIAL. External transport failure reflected both target/cohort differences and changed feature–target relationships; therefore the experiment demonstrates transportability risk but cannot isolate pure conditional shift.", { exact: true }), "Phase 3C wording retained");
checks["external transportability section renders"] = true;
await openDisclosure("Q-CARE model evidence report", "Q-CARE model evidence report");
await requireVisible(page.getByText("RESEARCH EVIDENCE ONLY", { exact: true }), "final evidence report renders");

const exceptions = await page.locator('[data-testid="stException"]').count();
if (exceptions) errors.push(`Streamlit exceptions: ${exceptions}`);
checks["Analyse works"] = true;

await browser.close();
if (errors.length) throw new Error(errors.join(" | "));
console.log(JSON.stringify({ url: baseUrl, checks, errors }, null, 2));
