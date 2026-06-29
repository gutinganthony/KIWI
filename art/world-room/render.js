const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  const fs = require('fs');
  const svg = fs.readFileSync('world_room.svg', 'utf8');
  await page.setContent(`<!doctype html><html><body style="margin:0">${svg}</body></html>`);
  await page.screenshot({ path: 'world_room.png', clip: { x:0, y:0, width:1080, height:1920 } });
  await browser.close();
  console.log('rendered');
})();
