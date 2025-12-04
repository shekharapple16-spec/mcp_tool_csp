from playwright.async_api import async_playwright

playwright_instance = None
browser_instance = None


async def init_browser():
    """
    Initialize global Playwright + Chromium only once.
    Render free tier optimization.
    """
    global playwright_instance, browser_instance

    try:
        if playwright_instance is None:
            playwright_instance = await async_playwright().start()

        if browser_instance is None:
            browser_instance = await playwright_instance.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
    except Exception as e:
        raise RuntimeError(f"Browser init failed: {e}")


async def extract_dom_and_locators(url: str):
    """
    Async generator that yields optimized locator results.
    Auto-handles Playwright failures + network issues.
    """

    await init_browser()

    page = None

    try:
        page = await browser_instance.new_page()

        # FIX HTTP2 PROTOCOL ERRORS
        await page.route("**/*", lambda route: route.continue_())

        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=20000
        )

        selector = (
            "a, button, input, select, textarea, "
            "div, span, h1, h2, h3, label, i, li"
        )

        elements = await page.query_selector_all(selector)

        # Render-friendly limit
        elements = elements[:150]

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

                # Safely fetch text
                text = await el.evaluate(
                    "e => (e.innerText?.length < 40 ? e.innerText.trim() : '')"
                )

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

    except Exception as e:
        yield {"error": f"Navigation or extraction failed: {e}"}

    finally:
        try:
            if page:
                await page.close()
        except:
            pass
