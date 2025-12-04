from fastmcp import FastMCP
import os
import requests
from starlette.requests import Request
from starlette.responses import JSONResponse
from dom_extractor import extract_dom_and_locators


# Create MCP app
app = FastMCP("jira-mcp")

# Load environment variables
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
AC_FIELD = os.getenv("AC_FIELD", "description")


def get_jira_issue(issue_id: str):
    """Internal helper to fetch Jira issue details."""
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
    response = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN))

    if response.status_code != 200:
        return {
            "error": f"Failed: {response.status_code}",
            "details": response.text
        }

    return response.json()


@app.tool()
def get_acceptance_criteria(issue_id: str):
    """Fetch acceptance criteria from Jira."""
    data = get_jira_issue(issue_id)

    if "error" in data:
        return data

    fields = data.get("fields", {})
    ac_value = fields.get(AC_FIELD, None)

    return {
        "issue": issue_id,
        "acceptance_criteria": ac_value
    }


# --------------------------------------------------------
# 🚀 STREAMING MCP TOOL (locators returned one-by-one)
# --------------------------------------------------------
@app.tool(streaming=True)
async def extract_dom(url: str):
    """
    Streams locator data as it's extracted.
    Works fast on Render free tier.
    """
    async for locator in extract_dom_and_locators(url):
        yield locator


# --- Health-check route using custom_route ---
@app.custom_route("/", methods=["GET"])
async def root(request: Request):
    return JSONResponse({
        "status": "MCP server 'jira-mcp' is running!",
        "mcp_endpoint": "/mcp"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, transport="http")
