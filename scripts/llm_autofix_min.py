import os, json, textwrap, requests, subprocess, sys, pathlib, time

API_KEY = os.environ.get("LLM_API_KEY")
MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# Only fix low-risk, non-behavioral issues
SAFE_HINTS = ["unused", "redundant", "docstring", "format", "style", "convention"]

def ask_gemini(prompt: str) -> str:
    if not API_KEY:
        raise RuntimeError("No GEMINI_API_KEY / LLM_API_KEY set")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.15}
    }
    r = requests.post(URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def choose_issue(issues):
    """
    Prefer small, low-risk issues. If none match SAFE_HINTS, abort instead of touching bigger ones.
    """
    for it in issues:
        msg = (it.get("message","") + " " + it.get("rule","")).lower()
        if any(h in msg for h in SAFE_HINTS):
            return it
    return None

def main():
    if not os.path.exists("issues.json"):
        print("No issues.json; nothing to autofix.")
        sys.exit(0)

    issues = json.load(open("issues.json"))
    if not issues:
        print("issues.json empty; nothing to autofix.")
        sys.exit(0)

    issue = choose_issue(issues)
    if not issue:
        print("No safe low-risk issue found; aborting.")
        sys.exit(0)

    file_path = issue.get("component","").split(":")[-1]
    line_num = issue.get("line", 1)
    msg = issue.get("message", "(no message)")
    rule = issue.get("rule", "")

    if not file_path or not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(0)

    lines = pathlib.Path(file_path).read_text(encoding="utf-8").splitlines()
    idx = max(0, (line_num or 1) - 1)
    start, end = max(0, idx - 10), min(len(lines), idx + 11)
    window = "\n".join(lines[start:end])

    prompt = textwrap.dedent(f"""
    You are a highly precise Python code refactoring assistant.

    Fix *only* the specific SonarCloud issue described below with the smallest possible change.
    You may add or remove lines if required to resolve the issue, but do not rewrite unrelated code.
    Do not change behavior or introduce new logic.

    Sonar Issue:
    {msg}
    Rule: {rule}
    Location: {file_path}:{line_num}

    Original Code:
    ```
    {window}
    ```

    Return ONLY the corrected code excerpt, no explanation:
    """).strip()

    try:
        corrected = ask_gemini(prompt)
    except Exception as e:
        print(f"LLM error: {e}")
        sys.exit(0)

    if not corrected or corrected.strip() == window.strip():
        print("No meaningful change — aborting.")
        sys.exit(0)

    corrected_lines = corrected.splitlines()
    lines[start:end] = corrected_lines
    new_full = "\n".join(lines)

    pathlib.Path(file_path).write_text(new_full, encoding="utf-8")
    print(f"✅ Applied safe auto-fix → {file_path}:{line_num}")

    subprocess.run(["git","config","user.name","ci-bot"], check=True)
    subprocess.run(["git","config","user.email","ci-bot@example.com"], check=True)

    branch = f"ci/autofix-{int(time.time())}"
    subprocess.run(["git","checkout","-b", branch], check=True)
    subprocess.run(["git","add", file_path], check=True)

    try:
        subprocess.run(["pytest","-q","--maxfail=1"], check=True)
        test_note = " (tests passed)"
    except Exception:
        test_note = " (tests failed, review recommended)"

    subprocess.run(["git","commit","-m", f"autofix: safe Sonar fix: {msg}{test_note}"], check=True)
    subprocess.run(["git","push","-u","origin", branch], check=True)

    base = os.environ.get("GITHUB_HEAD_REF") or "main"
    try:
        subprocess.run([
            "gh","pr","create",
            "--base", base,
            "--title", f"CI Autofix: {msg}",
            "--body", f"Automated minimal fix for Sonar issue:\n\n- File: `{file_path}`\n- Line: {line_num}\n- Rule: `{rule}`\n- Message: {msg}\n\nThis PR intentionally applies only safe, behavior-preserving cleanup.\n"
        ], check=False)
    except:
        print("Note: gh not available — PR branch created, open manually.")

if __name__ == "__main__":
    main()
