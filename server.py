from fastmcp import FastMCP
import os
import requests
from starlette.requests import Request
from starlette.responses import JSONResponse
from dom_extractor import extract_dom_and_locators


app = FastMCP("jira-mcp")

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
AC_FIELD = os.getenv("AC_FIELD", "description")


def get_jira_issue(issue_id: str):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
    response = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN))

    if response.status_code != 200:
        return {"error": f"Failed: {response.status_code}", "details": response.text}

    return response.json()


@app.tool()
def get_acceptance_criteria(issue_id: str):
    data = get_jira_issue(issue_id)

    if "error" in data:
        return data

    fields = data.get("fields", {})
    ac_value = fields.get(AC_FIELD, None)

    return {"issue": issue_id, "acceptance_criteria": ac_value}


@app.tool()
async def extract_dom(url: str):
    """
    Chunked locator streaming (compatible with older FastMCP).
    """
    chunk = []
    async for locator in extract_dom_and_locators(url):
        chunk.append(locator)

        # Return small chunks to avoid Render timeout
        if len(chunk) >= 30:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


@app.custom_route("/", methods=["GET"])
async def root(request: Request):
    return JSONResponse({
        "status": "MCP server 'jira-mcp' is running!",
        "mcp_endpoint": "/mcp"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, transport="http")
