from playwright.async_api import async_playwright

playwright_instance = None
browser_instance = None


async def init_browser():
    """
    Initialize global Playwright + Chromium once (massive performance gain on Render).
    """
    global playwright_instance, browser_instance

    try:
        if playwright_instance is None:
            playwright_instance = await async_playwright().start()

        if browser_instance is None:
            browser_instance = await playwright_instance.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]  # Required on Render
            )
    except Exception as e:
        raise RuntimeError(f"Browser init failed: {e}")


async def extract_dom_and_locators(url: str):
    """
    Extract optimized locator data with best performance.
    """

    # 1. Reuse browser
    await init_browser()

    page = None

    try:
        # 2. New page for each request
        page = await browser_instance.new_page()

        # 3. Block heavy resources (huge speed improvement)
        await page.route("**/*", lambda route:
            route.abort() if route.request.resource_type in ["image", "media", "font"]
            else route.continue_()
        )

        # 4. Fastest load strategy
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        # 5. Reduced DOM query (no noisy div/span)
        selector = (
            "a, button, input, select, textarea, label, h1, h2, h3, "
            "[role], [data-testid], [placeholder], [name]"
        )

        elements = await page.query_selector_all(selector)

        # Cap elements for Render performance
        elements = elements[:150]

        # 6. Loop through elements
        for el in elements:
            try:
                # Batch extract all attributes in ONE JS call (huge speed gain)
                info = await el.evaluate("""
                e => ({
                    tag: e.tagName.toLowerCase(),
                    id: e.id || null,
                    cls: e.className || null,
                    role: e.getAttribute('role'),
                    placeholder: e.getAttribute('placeholder'),
                    testid: e.dataset?.testid || null,
                    title: e.title || null,
                    name: e.name || null,
                    text: (e.innerText?.length < 40 ? e.innerText.trim() : '')
                })
                """)

                pw = {}

                if info["testid"]:
                    pw["testid"] = info["testid"]
                if info["id"]:
                    pw["id"] = info["id"]
                if info["role"] and info["text"]:
                    pw["role"] = f"{info['role']}[name='{info['text']}']"
                if info["placeholder"]:
                    pw["placeholder"] = info["placeholder"]
                if info["name"]:
                    pw["label"] = info["name"]
                if info["title"]:
                    pw["title"] = info["title"]
                if info["text"]:
                    pw["text"] = info["text"]
                if info["cls"]:
                    cls_clean = ".".join(info["cls"].split())
                    pw["css"] = f"{info['tag']}.{cls_clean}"

                # Best locator priority
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
                    "tag": info["tag"]
                }

            except:
                continue

    except Exception as e:
        yield {"error": f"Navigation or extraction failed: {e}"}

    finally:
        # Always close the page safely
        try:
            if page:
                await page.close()
        except:
            pass
