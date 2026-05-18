const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://dash.aclclouds.com/auth/login', { waitUntil: 'networkidle' });
  const html = await page.content();
  // Find all input elements
  const inputMatches = html.match(/<input[^>]*>/gi) || [];
  inputMatches.forEach(m => console.log(m));
  // Also log all labels
  const labelMatches = html.match(/<label[^>]*>.*?<\/label>/gi) || [];
  labelMatches.forEach(m => console.log(m));
  await browser.close();
})();
