import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const nodeModules = process.env.QCARE_NODE_MODULES;
if (!nodeModules) throw new Error("QCARE_NODE_MODULES must point to the bundled node_modules directory");
const { chromium } = require(path.join(nodeModules, "playwright"));

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const baseUrl = process.env.QCARE_APP_URL || "http://127.0.0.1:8521";
const output = path.join(root, "submission", "screenshots");
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QCARE_BROWSER_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const page = await browser.newPage({ viewport: { width: 1100, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", error => errors.push(error.message));
page.on("console", message => {
  if (message.type() === "error") errors.push(`console: ${message.text()}`);
});

async function uniqueText(text) {
  const locator = page.getByText(text, { exact: true });
  const count = await locator.count();
  if (count !== 1) throw new Error(`Expected one exact text match for ${text}; found ${count}`);
  return locator;
}

async function positionAt(locator, top = 80) {
  await locator.evaluate((element, topOffset) => {
    const scroller = document.querySelector('[data-testid="stMain"]');
    if (scroller) {
      const delta = element.getBoundingClientRect().top - scroller.getBoundingClientRect().top - topOffset;
      scroller.scrollTo({ top: scroller.scrollTop + delta, behavior: "instant" });
    } else {
      window.scrollBy({ top: element.getBoundingClientRect().top - topOffset, behavior: "instant" });
    }
  }, top);
}

async function captureAt(text, filename) {
  const locator = await uniqueText(text);
  await positionAt(locator);
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(output, filename), fullPage: false });
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.waitForTimeout(5000);
const overviewHeading = page.getByText("Q-CARE", { exact: true });
const overviewCount = await overviewHeading.count();
if (overviewCount < 1) throw new Error(`Overview heading missing; body=${(await page.locator("body").innerText()).slice(0, 500)}`);
await overviewHeading.last().waitFor({ state: "visible", timeout: 30000 });
const liveNavigation = await uniqueText("Live Research Assessment");
await liveNavigation.click();
await page.waitForTimeout(1500);
const heading = page.getByRole("heading", { name: "Live Research Assessment", exact: true });
await heading.waitFor({ state: "visible", timeout: 30000 });
await heading.scrollIntoViewIfNeeded();
await page.waitForTimeout(350);
await page.screenshot({ path: path.join(output, "live_01_patient_entry.png"), fullPage: false });

const analyse = page.getByRole("button", { name: "Analyse with frozen VQC", exact: true });
if ((await analyse.count()) !== 1) throw new Error("Analyse button missing");
await analyse.click();
await page.locator("div.live-classification").waitFor({ state: "visible", timeout: 30000 });

await captureAt("Experimental classification", "live_02_vqc_result.png");
await captureAt("Factors influencing this model output", "live_03_factor_explanation.png");
await captureAt("Similar benchmark records", "live_04_similar_records.png");
await captureAt("Model comparison", "live_05_model_comparison.png");
await captureAt("Clinician review checklist", "live_06_review_checklist.png");

const explainer = await uniqueText("How the quantum model works");
await explainer.click();
const circuit = page.locator('[data-testid="stCode"]');
if ((await circuit.count()) !== 1) throw new Error("Rendered VQC circuit missing");
await circuit.waitFor({ state: "visible", timeout: 10000 });
await positionAt(circuit, 80);
await page.waitForTimeout(350);
await page.screenshot({ path: path.join(output, "live_07_quantum_circuit.png"), fullPage: false });

await browser.close();
if (errors.length) throw new Error(`Browser errors: ${errors.join(" | ")}`);
console.log("Live VQC screenshots captured");
