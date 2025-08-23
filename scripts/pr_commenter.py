
import os, json

def main():
    summary_lines = ["### SonaRefactor Bot — Comment-Only MVP"]
    if os.path.exists("issues.json"):
        data = json.load(open("issues.json"))
        count = len(data)
        summary_lines.append(f"- SonarQube reported **{count}** issue(s).")
        # Show up to 5 simple bullets
        for it in data[:5]:
            msg = it.get("message","(no message)")
            comp = it.get("component","") .split(":")[-1]
            line = it.get("line","?")
            summary_lines.append(f"  - `{comp}:{line}` — {msg}")
    else:
        summary_lines.append("- No issues.json found.")

    # Write to GitHub Step Summary if available; fall back to stdout
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    content = "\n".join(summary_lines) + "\n"
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(content)
    print(content)

if __name__ == "__main__":
    main()
