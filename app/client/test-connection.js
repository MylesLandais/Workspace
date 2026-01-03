const { chromium } = require('playwright');

(async () => {
  console.log('Connecting to browserless (CDP)...');
  const browser = await chromium.connectOverCDP(
    process.env.PLAYWRIGHT_SERVICE_URL || 'ws://172.24.0.2:3000'
  );
  console.log('Connected!');
  const context = browser.contexts()[0];
  const page = await context.newPage();
  console.log('Going to http://client:3000...');
  await page.goto('http://client:3000');
  console.log('Title:', await page.title());
  await browser.close();
  console.log('Done!');
})();
