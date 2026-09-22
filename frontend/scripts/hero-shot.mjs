import { chromium } from "playwright";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
await page.screenshot({
  path: "public/_hero_check.png",
  clip: { x: 250, y: 50, width: 1190, height: 280 },
});
await browser.close();
console.log("saved");
