import os, json, textwrap, requests, subprocess, sys, pathlib

API_KEY = os.environ.get("LLM_API_KEY")
MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# Safety: only auto-fix very low-risk smells first
SAFE_HINTS = ["unused", "redundant", "docstring", "format", "style", "convention"]

def ask_gemini(prompt: str) -> str:
    if not API_KEY:
        raise RuntimeError("No GEMINI_API_KEY / LLM_API_KEY set")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }
    r = requests.post(URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def choose_issue(issues):
    # Pick the first issue with a "safe" hint (or just the first issue if none match)
    for it in issues:
        msg = (it.get("message","") + " " + it.get("rule","")).lower()
        if any(h in msg for h in SAFE_HINTS):
            return it
    return issues[0] if issues else None

def main():
    # 0) Pre-checks
    if not os.path.exists("issues.json"):
        print("No issues.json; nothing to autofix.")
        sys.exit(0)

    issues = json.load(open("issues.json"))
    if not issues:
        print("issues.json empty; nothing to autofix.")
        sys.exit(0)

    issue = choose_issue(issues)
    if not issue:
        print("No suitable issue found for minimal auto-fix.")
        sys.exit(0)

    file_path = issue.get("component","").split(":")[-1]
    line_num = issue.get("line", 1)
    msg = issue.get("message", "(no message)")
    rule = issue.get("rule", "")

    if not file_path or not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(0)

    # 1) Read file and create a small context window around the line
    lines = pathlib.Path(file_path).read_text(encoding="utf-8").splitlines()
    idx = max(0, (line_num or 1) - 1)
    start = max(0, idx - 10)
    end = min(len(lines), idx + 11)  # 10 lines above + current + 10 below
    window = "\n".join(lines[start:end])

    # 2) Ask Gemini for a corrected window (no diff, just pasteable code)
    prompt = textwrap.dedent(f"""
    You are a careful code refactoring assistant.
    Given a Python source excerpt, return a corrected version of the SAME excerpt that fixes the described SonarCloud issue.
    Keep changes minimal. Do not add or remove unrelated lines. Preserve behavior except to fix the issue.
    Output ONLY the corrected code for the excerpt. No explanations.

    File: {file_path}
    Line: {line_num}
    Sonar issue: {msg}
    Sonar rule: {rule}

    Original excerpt (keep the same number of lines unless strictly required):
    ```
    {window}
    ```
    """).strip()

    try:
        corrected = ask_gemini(prompt)
    except Exception as e:
        print(f"LLM error: {e}")
        sys.exit(0)

    if not corrected or corrected == window:
        print("No meaningful change suggested; aborting.")
        sys.exit(0)

    # 3) Replace the window in the file via simple string replace
    original_full = "\n".join(lines)
    new_full = original_full.replace(window, corrected, 1)
    if new_full == original_full:
        print("Could not apply change (window not found exact).")
        sys.exit(0)

    pathlib.Path(file_path).write_text(new_full, encoding="utf-8")
    print(f"Applied minimal auto-fix to {file_path}:{line_num}")

    # 4) Create branch, commit, push
    subprocess.run(["git","config","user.name","ci-bot"], check=True)
    subprocess.run(["git","config","user.email","ci-bot@example.com"], check=True)

    branch = f"ci/autofix-{os.environ.get('GITHUB_RUN_ID','local')}"
    subprocess.run(["git","checkout","-b", branch], check=True)
    subprocess.run(["git","add", file_path], check=True)

    # Quick test run (optional but nice)
    try:
        subprocess.run(["pytest","-q","--maxfail=1"], check=True)
        test_note = " (tests passed)"
    except Exception:
        test_note = " (tests failed; still opening PR for review)"

    subprocess.run(["git","commit","-m", f"autofix: minimal Gemini patch for Sonar issue: {msg}{test_note}"], check=True)
    subprocess.run(["git","push","-u","origin", branch], check=True)

    # 5) Try to open a PR (ok if 'gh' not present)
    base = os.environ.get("GITHUB_HEAD_REF") or "main"
    try:
        subprocess.run([
            "gh","pr","create",
            "--base", base,
            "--title", "CI Autofix: minimal Gemini patch",
            "--body", f"Automated minimal fix for Sonar issue:\n\n- **File:** `{file_path}`\n- **Line:** {line_num}\n- **Rule/Msg:** {rule} — {msg}\n\nPlease review."
        ], check=False)
    except Exception:
        print("Note: gh CLI not available; open PR manually from the pushed branch.")

if __name__ == "__main__":
    main()
