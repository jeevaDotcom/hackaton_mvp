import { createRequire } from "node:module";
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
const page = await browser.newPage({ viewport: { width: 1280, height: 1200 }, deviceScaleFactor: 1 });
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

async function heading(name) {
  return one(page.getByRole("heading", { name, exact: true }), `heading ${name}`);
}

async function positionAt(locator, top = 64) {
  await locator.scrollIntoViewIfNeeded();
  await locator.evaluate((element, offset) => {
    element.scrollIntoView({ block: "start", inline: "nearest", behavior: "instant" });
    const scroller = element.closest('[data-testid="stMain"]');
    if (scroller) scroller.scrollBy({ top: -offset, behavior: "instant" });
    else window.scrollBy({ top: -offset, behavior: "instant" });
  }, top);
  await page.waitForTimeout(350);
}

async function capture(locator, filename, top = 64) {
  await positionAt(locator, top);
  await page.screenshot({ path: path.join(output, filename), fullPage: false });
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
const brandLocator = page.locator("div.workstation-brand");
await brandLocator.waitFor({ state: "visible", timeout: 30000 });
const brand = await one(brandLocator, "Q-CARE brand");
await heading("Patient input");
await page.waitForTimeout(350);
await page.screenshot({ path: path.join(output, "01_hero_input.png"), fullPage: false });

const analyse = await one(page.getByRole("button", { name: "ANALYSE PROFILE", exact: true }), "Analyse button");
await analyse.click();
const consensus = await heading("Model consensus");
await page.getByText("2 OF 3 AGREE", { exact: true }).or(page.getByText("3 OF 3 AGREE", { exact: true })).waitFor({ state: "visible", timeout: 30000 });
await capture(consensus, "02_model_consensus.png");

await capture(await heading("Classical vs quantum performance"), "03_performance_runtime.png");
await capture(await heading("What influenced this model output?"), "04_feature_influence.png");

const quantumControl = await one(page.locator("details summary").filter({ hasText: "Actual quantum circuits" }), "quantum disclosure");
await quantumControl.click();
const quantum = await heading("Quantum proof");
await page.getByRole("heading", { name: "Quantum similarity matrix", exact: true }).waitFor({ state: "visible", timeout: 20000 });
await capture(quantum, "05_quantum_proof.png");

const evidence = await heading("Q-CARE model evidence report");
await page.getByText("RESEARCH EVIDENCE ONLY", { exact: true }).waitFor({ state: "visible", timeout: 20000 });
await capture(evidence, "06_evidence_report.png");

const exceptions = await page.locator('[data-testid="stException"]').count();
if (exceptions) errors.push(`Streamlit exceptions: ${exceptions}`);
await browser.close();
if (errors.length) throw new Error(errors.join(" | "));
console.log("Six Q-CARE 2.0 judge screenshots captured");
