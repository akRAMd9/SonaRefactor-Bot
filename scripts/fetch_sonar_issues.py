
import os, re, json, sys, requests

SONAR_HOST_URL = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")
SONAR_TOKEN = os.environ["SONAR_TOKEN"]  # must be set via GitHub Secret
PR_NUMBER = os.environ.get("PR_NUMBER")  # set on pull_request events
OUT = "issues.json"

def read_project_key():
    path = "sonar-project.properties"
    if not os.path.exists(path):
        print("!! sonar-project.properties not found at repo root.")
        return None
    txt = open(path, "r", encoding="utf-8").read()
    m = re.search(r"^sonar\.projectKey\s*=\s*(.+)$", txt, flags=re.M)
    if m:
        return m.group(1).strip()
    print("!! sonar.projectKey not found in sonar-project.properties.")
    return None

def fetch_issues(project_key):
    all_issues, page = [], 1
    while True:
        params = {"componentKeys": project_key, "ps": 200, "p": page}
        if PR_NUMBER:
            params["pullRequest"] = PR_NUMBER
        r = requests.get(f"{SONAR_HOST_URL}/api/issues/search",
                         params=params, auth=(SONAR_TOKEN, ""))
        r.raise_for_status()
        data = r.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)
        paging = data.get("paging", {})
        if page * paging.get("pageSize", len(issues)) >= paging.get("total", 0):
            break
        page += 1
    return all_issues

def main():
    print(f"[fetch] HOST={SONAR_HOST_URL} PR_NUMBER={PR_NUMBER}")
    project_key = read_project_key()
    print(f"[fetch] project_key={project_key!r}")
    issues = []
    if project_key:
        try:
            issues = fetch_issues(project_key)
        except Exception as e:
            print(f"!! Sonar API fetch error: {e}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2)
    print(f"[fetch] wrote {len(issues)} issues to {OUT} (cwd={os.getcwd()})")

if __name__ == "__main__":
    main()
