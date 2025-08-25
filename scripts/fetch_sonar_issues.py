# scripts/fetch_sonar_issues.py
import os, re, json, sys, time, requests

SONAR_HOST_URL = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")
SONAR_TOKEN = os.environ["SONAR_TOKEN"]
PR_NUMBER = os.environ.get("PR_NUMBER")
OUT = "issues.json"

def read_project_key():
    path = "sonar-project.properties"
    if not os.path.exists(path):
        print("!! sonar-project.properties not found.")
        return None
    txt = open(path, "r", encoding="utf-8").read()
    m = re.search(r"^sonar\.projectKey\s*=\s*(.+)$", txt, flags=re.M)
    return m.group(1).strip() if m else None

def fetch_once(project_key, page, page_size=200):
    params = {"componentKeys": project_key, "ps": page_size, "p": page}
    if PR_NUMBER:
        params["pullRequest"] = PR_NUMBER
    r = requests.get(f"{SONAR_HOST_URL}/api/issues/search",
                     params=params, auth=(SONAR_TOKEN, ""))
    r.raise_for_status()
    return r.json()

def fetch_all(project_key, max_wait_sec=60, interval_sec=5):
    """Poll until issues appear (or timeout) for this PR."""
    waited = 0
    while True:
        page, all_issues = 1, []
        while True:
            data = fetch_once(project_key, page)
            issues = data.get("issues", [])
            all_issues.extend(issues)
            paging = data.get("paging", {})
            if page * paging.get("pageSize", len(issues)) >= paging.get("total", 0):
                break
            page += 1

        if not PR_NUMBER or all_issues or waited >= max_wait_sec:
            if PR_NUMBER and not all_issues:
                print(f"[fetch] still 0 issues after waiting {waited}s (timeout={max_wait_sec}s)")
            return all_issues

        time.sleep(interval_sec)
        waited += interval_sec
        print(f"[fetch] no PR issues yet; retrying in {interval_sec}s… (waited {waited}s)")

def main():
    project_key = read_project_key()
    print(f"[fetch] HOST={SONAR_HOST_URL} PR_NUMBER={PR_NUMBER} project_key={project_key!r}")
    issues = []
    if project_key:
        try:
            issues = fetch_all(project_key)
        except Exception as e:
            print(f"!! Sonar API fetch error: {e}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2)
    print(f"[fetch] wrote {len(issues)} issues to {OUT}")

if __name__ == "__main__":
    main()
