from fastmcp import FastMCP
import os
import requests
from starlette.requests import Request
from starlette.responses import JSONResponse
from dom_extractor import extract_dom_and_locators

app = FastMCP("jira-mcp")

# Env vars
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
AC_FIELD = os.getenv("AC_FIELD", "description")


def get_jira_issue(issue_id: str):
    """Fetch a Jira issue using the Jira REST API."""
    
    if not (JIRA_URL and JIRA_EMAIL and JIRA_TOKEN):
        return {"error": "Missing Jira environment variables."}

    url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
    response = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN))

    if response.status_code != 200:
        return {
            "error": f"Failed to fetch issue (HTTP {response.status_code})",
            "details": response.text
        }

    return response.json()


@app.tool()
def get_acceptance_criteria(issue_id: str):
    """
    Retrieve acceptance criteria from a Jira issue.
    Reads the field configured in AC_FIELD (default: description).
    """

    data = get_jira_issue(issue_id)

    if "error" in data:
        return data

    fields = data.get("fields", {})
    ac_value = fields.get(AC_FIELD)

    if not ac_value:
        return {
            "issue": issue_id,
            "acceptance_criteria": None,
            "message": f"No value found for field '{AC_FIELD}'."
        }

    return {
        "issue": issue_id,
        "acceptance_criteria": ac_value
    }


@app.tool()
async def extract_dom(url: str):
    """
    Extract DOM elements from a page and return Playwright locators.
    """
    results = []
    async for item in extract_dom_and_locators(url):
        results.append(item)

    return {"locators": results}


@app.custom_route("/", methods=["GET"])
async def root(request: Request):
    return JSONResponse({
        "status": "MCP server 'jira-mcp' is running!",
        "mcp_endpoint": "/mcp"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        transport="http"
    )
