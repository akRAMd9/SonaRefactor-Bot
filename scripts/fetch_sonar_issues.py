
import os, json, sys, requests

def main():
    host = os.environ.get("SONAR_HOST_URL", "").rstrip("/")
    token = os.environ.get("SONAR_TOKEN", "")
    project = "sonarefactor-demo"

    if not host or not token:
        print("Missing SONAR_HOST_URL or SONAR_TOKEN")
        sys.exit(0)

    try:
        resp = requests.get(
            f"{host}/api/issues/search",
            params={"componentKeys": project, "ps": 200},
            auth=(token, "")
        )
        resp.raise_for_status()
        issues = resp.json().get("issues", [])
    except Exception as e:
        print("Could not fetch Sonar issues:", e)
        issues = []

    with open("issues.json","w") as f:
        json.dump(issues, f, indent=2)
    print(f"Saved {len(issues)} issues to issues.json")

if __name__ == "__main__":
    main()
