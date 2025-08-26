```python
    # NOTE: this file is intentionally "bad" to trigger SonarCloud findings.

# 1) Mutable default arg (code smell)
def collect_names(name, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(name)
    return bucket

# 2) Broad 'except' and 3) dangerous eval (security hotspot)
def risky_eval(s):
    try:
        return eval(s)   # Sonar will flag use of eval()
    except:              # Broad exception handler
        return None
```
# 4) Hard-coded secret (security hotspot)
DB_PASSWORD = "P@ssw0rd123"

# 5) SQL string concatenation (SQL injection risk)
def get_user_query(username):
    return "SELECT * FROM users WHERE username = '" + username + "'"

# 6) Duplicate code (copy-paste detector)
def get_user_query_copy(username):
    return "SELECT * FROM users WHERE username = '" + username + "'"

# 7) Debug print / leftover logging
def debug_something(x):
    print("DEBUG:", x)
    return True

# Keep tests passing: don't change greet() import or behavior
if __name__ == "__main__":
    # make sure file runs without error (but tests don't depend on it)
    collect_names("Akram")
    risky_eval("1+1")
    debug_something("ok")