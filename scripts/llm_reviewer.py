
import os, json, textwrap, requests

API_KEY = os.environ.get("LLM_API_KEY")
MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")  # or any model you prefer
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"  # swap if using another provider

def ask_gemini(prompt: str) -> str:
    if not API_KEY:
        return "(No GEMINI_API_KEY set)"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {"temperature": 0.2}
    }
    r = requests.post(URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def main():
    if not os.path.exists("issues.json"):
        print("No issues.json found; nothing to review.")
        return
    issues = json.load(open("issues.json"))
    if not issues:
        print("No issues from SonarCloud.")
        return

    sample = issues[:5]
    bullets = []
    for it in sample:
        file = it.get("component","").split(":")[-1]
        line = it.get("line","?")
        rule = it.get("rule","")
        msg  = it.get("message","")
        prompt = textwrap.dedent(f"""
        You are a concise senior code reviewer. Explain the SonarCloud issue in 1–2 sentences
        and suggest a minimal, safe fix. If obvious, include a tiny before/after snippet.

        File: {file}
        Line: {line}
        Sonar rule: {rule}
        Message: {msg}
        """).strip()
        try:
            advice = ask_gemini(prompt)
        except Exception as e:
            advice = f"(LLM error: {e})"
        bullets.append(f"- `{file}:{line}` — **{msg}**\n  {advice}")

    out = "### 🤖 AI Review Suggestions (Gemini)\n" + "\n".join(bullets) + "\n"
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a") as f: f.write(out)
    print(out)

if __name__ == "__main__":
    main()
