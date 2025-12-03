# dom_extractor.py
from playwright.async_api import async_playwright

playwright = None
browser = None

async def init_browser():
    global playwright, browser
    if not playwright:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])

async def extract_dom_and_locators(url: str):

    await init_browser()

    locator_data = []

    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded")

    # Limit element types for speed
    elements = await page.query_selector_all("button, input, a, div, span")
    elements = elements[:200]

    for el in elements:
        try:
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            id_attr = await el.get_attribute("id")
            cls = await el.get_attribute("class")
            role = await el.get_attribute("role")

            # Faster than inner_text
            text = await el.evaluate("e => e.innerText?.trim()?.slice(0, 40)")

            playwright_locators = []
            selenium_locators = []

            if id_attr:
                playwright_locators.append(f"page.locator('#{id_attr}')")
                selenium_locators.append(f"driver.find_element(By.ID, '{id_attr}')")

            if cls:
                cls_clean = ".".join(cls.split())
                playwright_locators.append(f"page.locator('css={tag}.{cls_clean}')")
                selenium_locators.append(f"driver.find_element(By.CSS_SELECTOR, '{tag}.{cls_clean}')")

            if text:
                playwright_locators.append(f"page.get_by_text('{text}')")
                selenium_locators.append(f"driver.find_element(By.XPATH, \"//*[text()='{text}']\")")

            locator_data.append({
                "tag": tag,
                "text": text,
                "id": id_attr,
                "class": cls,
                "role": role,
                "playwright": playwright_locators,
                "selenium": selenium_locators,
            })

        except Exception:
            continue

    await page.close()
    return locator_data
