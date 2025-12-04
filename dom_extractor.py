async def extract_dom_and_locators(url: str):
    await init_browser()

    locator_data = []
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded")

    elements = await page.query_selector_all("*")
    elements = elements[:200]

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

            # Playwright strategies (raw)
            if role and text:
                pw["role"] = f"{role}[name='{text}']"

            if text:
                pw["text"] = text

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

            if text:
                pw["xpath"] = f"//*[text()='{text}']"

            # --- Decide best locator (Playwright priority) ---
            best = (
                pw.get("role") or
                pw.get("text") or
                pw.get("label") or
                pw.get("placeholder") or
                pw.get("alt") or
                pw.get("title") or
                pw.get("testid") or
                pw.get("id") or
                pw.get("css") or
                pw.get("xpath")
            )

            locator_data.append({
                "best_playwright": best,
                "all_playwright": pw,
            })

        except:
            continue

    await page.close()
    return locator_data
