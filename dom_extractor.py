# dom_extractor.py
from playwright.async_api import async_playwright

playwright_instance = None
browser_instance = None


async def init_browser():
    """Start Playwright only once."""
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
    Streams locator data one-by-one instead of returning a huge list.
    Perfect for Render free tier.
    """
    await init_browser()

    page = await browser_instance.new_page()
    await page.goto(url, wait_until="domcontentloaded")

    elements = await page.query_selector_all("*")
    elements = elements[:200]   # safety limit

    for el in elements:
        try:
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            id_attr = await el.get_attribute("id")
            cls = await el.get_attribute("class")
            role = await el.get_attribute("role")
            name_attr = await el.get_attribute("name")
            placeholder = await el.get_attribute("placeholder")
            alt = await el.get_attribute("alt")
            title = await el.get_attribute("title")
            testid = await el.get_attribute("data-testid")
            text = await el.evaluate("e => e.innerText?.trim()?.slice(0, 40)")

            pw = {}

            # Build locators
            if role and text:
                pw["role"] = f"{role}[name='{text}']"

            if text:
                pw["text"] = text
                pw["xpath"] = f"//*[text()='{text}']"

            if placeholder:
                pw["placeholder"] = placeholder

            if title:
                pw["title"] = title

            if alt:
                pw["alt"] = alt

            if testid:
                pw["testid"] = testid

            if name_attr:
                pw["label"] = name_attr

            if id_attr:
                pw["id"] = id_attr

            if cls:
                cls_clean = ".".join(cls.split())
                pw["css"] = f"{tag}.{cls_clean}"

            # Best locator priority
            best = (
                pw.get("role")
                or pw.get("text")
                or pw.get("label")
                or pw.get("placeholder")
                or pw.get("alt")
                or pw.get("title")
                or pw.get("testid")
                or pw.get("id")
                or pw.get("css")
                or pw.get("xpath")
            )

            # 🔥 STREAM IMMEDIATELY
            yield {
                "best_playwright": best,
                "all_playwright": pw,
            }

        except Exception:
            continue

    await page.close()
