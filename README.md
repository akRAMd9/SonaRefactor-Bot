
#  LLM-Powered Code Quality Bot (SonarCloud + Gemini + CI/CD)

> **An Automated Refactoring Agent for Developer Workflows**

This project is a working proof-of-concept of a **CI/CD bot that detects and auto-fixes code quality issues** flagged by SonarCloud using a Large Language Model (Gemini API). It showcases an **end-to-end AI integration pipeline**, from static analysis to AI-assisted remediation — all triggered by a GitHub pull request.

The goal: **offload repetitive refactoring and minor code smells to AI**, so developers can focus on solving real problems.

---

## 🛠️ What It Does

When a pull request is opened, this bot:
1.  Runs tests via GitHub Actions.
2.  Uses SonarCloud to scan for issues (bugs, smells, security).
3.  Passes those issues to Gemini, which:
   - Explains the problems (posted in the PR summary + comment).
   - Generates a suggested fix.
   - Applies one minimal safe fix (e.g., removing an unused variable).
      Pushes the patch to a new branch and opens a PR.

This demonstrates AI acting as a **hands-on teammate** in your DevOps pipeline — not just a reviewer, but a contributor.

---

##  Project Structure

```bash
.
├── .github
│   └── workflows
│       └── ci.yml             # GitHub Actions workflow definition
├── scripts
│   ├── fetch_sonar_issues.py  # Pulls issues via SonarCloud API
│   ├── llm_reviewer.py        # Gemini suggestions + summary
│   └── llm_autofix_min.py     # Applies one fix and opens PR
├── src
│   ├── demo.py                # Clean code sample
│   └── bad_example.py         # Intentionally flawed file for testing
├── requirements.txt
└── README.md
```

---

##  How to See It in Action

To trigger the full workflow:

1. Fork this repo and push a new branch with an issue (e.g., unused param).  
2. Open a pull request.  
3. Watch the magic:
   - SonarCloud reports issues
   - Gemini posts review suggestions
   - A bot-generated **autofix PR** appears

All Gemini output is visible in:
-  the GitHub Actions **summary tab**
-  a comment in the **PR conversation**
-  an auto-generated PR with the fix

---

## 💡 Why Only One Fix?

This bot intentionally applies **just one fix per PR** to:
- Keep commits reviewable
- Avoid unexpected large diffs from AI
- Make the pipeline deterministic

The logic supports scaling to multiple fixes later — but safety and clarity were prioritized here.

---

##  Tech Stack

- **SonarCloud** → Code quality and static analysis
- **Gemini API** → LLM suggestions and patch generation
- **GitHub Actions** → CI/CD automation pipeline
- **Python** → Scripted integration logic (modular + testable)
- **GitHub CLI (`gh`)** → Branch + pull request creation

---

## 🧩 Skills Demonstrated

This project maps directly to core AI Integration Developer skills:
-  Integrating LLM APIs into real-world pipelines
-  Prompt Engineering to output quality refactored code
-  Static code analysis and rule-based automation
-  CI/CD orchestration using GitHub Actions
-  Writing clean, modular Python for DevOps
-  Automating developer workflow tasks safely
- 

---

##  Who Built This

Hey — I'm Ak, a student at Toronto Metropolitan University and a self-taught systems builder.  
I'm not a 10x engineer (yet), but I build fast, learn deep, and love bringing AI into practical workflows.

This was built as part of my learning journey toward becoming a professional AI Integration Developer — and maybe even a candidate for your team.

I'm passionate about building things that work in the real world — and this project is a small step toward a bigger vision: **making AI part of the team.**
