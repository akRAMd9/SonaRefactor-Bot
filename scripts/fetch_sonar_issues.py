import os, sys, json, requests

SONAR_HOST_URL = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")
SONAR_TOKEN = os.environ["SONAR_TOKEN"]
PROJECT_KEY = os.environ.get("akRAMd9_SonaRefactor-Bot")
PR_NUMBER = os.environ.get("PR_NUMBER")           

OUT = "issues.json"

def fetch_page(page, page_size=200):
    params = {"componentKeys": PROJECT_KEY, "ps": page_size, "p": page}
    if PR_NUMBER:
        params["pullRequest"] = PR_NUMBER  # limits to just this PR’s issues
    r = requests.get(
        f"{SONAR_HOST_URL}/api/issues/search",
        params=params,
        auth=(SONAR_TOKEN, "")
    )
    r.raise_for_status()
    return r.json()

def main():
    if not PROJECT_KEY:
        print("Missing SONAR_PROJECT_KEY env var.")
        sys.exit(0)

    all_issues = []
    page = 1
    while True:
        data = fetch_page(page)
        issues = data.get("issues", [])
        all_issues.extend(issues)
        paging = data.get("paging", {})
        if page * paging.get("pageSize", len(issues)) >= paging.get("total", 0):
            break
        page += 1

    with open(OUT, "w") as f:
        json.dump(all_issues, f, indent=2)

    print(f"Saved {len(all_issues)} issues to {OUT} at {os.getcwd()}")

if __name__ == "__main__":
    main()
