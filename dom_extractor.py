from playwright.async_api import async_playwright

playwright_instance = None
browser_instance = None


async def init_browser():
    """Start Playwright once (very important for Render free tier)."""
    global playwright_instance, browser_instance

    if playwright_instance is None:
        playwright_instance = await async_playwright().start()

    if browser_instance is None:
        browser_instance = await playwright_instance.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )


async def extract_dom_and_locators(url: str):
    """
    Ultra-optimized DOM extractor:
    - Only collect 150 elements max
    - Avoid heavy innerText when not required
    - Build fastest locators
    - Safe for Render free tier
    """
    await init_browser()

    page = await browser_instance.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=15000)

    # Query only interactive / important elements
    selector = "a, button, input, select, textarea, div, span, h1, h2, h3, h4, h5"
    elements = await page.query_selector_all(selector)
    elements = elements[:150]  # Hard limit to keep CPU low

    for el in elements:
        try:
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            id_attr = await el.get_attribute("id")
            cls = await el.get_attribute("class")
            role = await el.get_attribute("role")
            placeholder = await el.get_attribute("placeholder")
            testid = await el.get_attribute("data-testid")
            title = await el.get_attribute("title")
            name_attr = await el.get_attribute("name")

            # Only fetch text if element is small
            text = await el.evaluate(
                "e => (e.innerText?.length < 40 ? e.innerText.trim() : '')"
            )

            # Build optimized locator set
            pw = {}

            if testid:
                pw["testid"] = testid

            if id_attr:
                pw["id"] = id_attr

            if role and text:
                pw["role"] = f"{role}[name='{text}']"

            if placeholder:
                pw["placeholder"] = placeholder

            if name_attr:
                pw["label"] = name_attr

            if title:
                pw["title"] = title

            if text:
                pw["text"] = text

            if cls:
                cls_clean = ".".join(cls.split())
                pw["css"] = f"{tag}.{cls_clean}"

            # Best locator priority (lightweight)
            best = (
                pw.get("testid")
                or pw.get("id")
                or pw.get("role")
                or pw.get("placeholder")
                or pw.get("label")
                or pw.get("title")
                or pw.get("text")
                or pw.get("css")
            )

            yield {
                "best_playwright": best,
                "all_playwright": pw,
                "tag": tag
            }

        except Exception:
            continue

    await page.close()
