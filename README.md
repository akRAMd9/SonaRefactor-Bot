
# SonaRefactor Bot (Comment-Only MVP)

A **smart CI helper** that runs on every push/PR:

1. Run tests
2. Run **SonarQube** to find code smells/bugs
3. Fetch Sonar findings
4. Post a short summary to the PR (comment/summary)

> Phase 2 (later): Ask an LLM to propose **small, safe fixes**, re-test, and open an **autofix PR**.

## How it works (plain English)

- **GitHub Actions** is the robot that wakes up when you push code.
- **SonarQube** is the code checker that points out issues.
- **Python scripts** fetch the issues and post a simple report to the PR so you can see them quickly.

## Secrets you need (set in GitHub → Settings → Secrets and variables → Actions)

- `SONAR_HOST_URL` (e.g. your SonarCloud or local SonarQube URL)
- `SONAR_TOKEN` (token from Sonar)

## Repo structure

```
.
├─ src/
│  └─ demo.py
├─ tests/
│  └─ test_demo.py
├─ scripts/
│  ├─ fetch_sonar_issues.py
│  └─ pr_commenter.py
├─ .github/workflows/ci.yml
├─ sonar-project.properties
├─ requirements.txt
└─ README.md
```

## Run locally (optional)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Notes
- This MVP only **comments** results (no auto-fix). Start simple, then add auto-fix later.
- Keep commits small. Use PRs so the bot has something to comment on.



Test run for SonarCloud

