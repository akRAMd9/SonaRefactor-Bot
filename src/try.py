# src/bad_example.py
# Intentionally "bad" code to trigger SonarCloud findings for demo purposes.

import json  # unused import (maintainability)

# 1) Mutable default arg (bug risk)
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket

# 2) Missing docstring (convention)
def multiply(x, y):
    return x * y

# 3) Bare except + ignore (reliability)
def risky_div(x, y):
    try:
        return x / y
    except:
        pass  # swallow exception

# 4) Dangerous eval (security hotspot)
def insecure_eval(user_input):
    return eval(user_input)

# 5) Hardcoded secret (security hotspot)
DB_PASSWORD = "P@ssw0rd123"

# 6) SQL concatenation (SQL injection risk)
def get_user_query(username):
    return "SELECT * FROM users WHERE username = '" + username + "'"

# 7) Duplicate code (copy-paste detector)
def get_user_query_copy(username):
    return "SELECT * FROM users WHERE username = '" + username + "'"

# 8) Unused variable (maintainability)
def greet_bad(name):
    unused = 42
    return f"Hello, {name}"

# 9) Debug print / leftover logging
def debug_something(x):
    print("DEBUG:", x)
    return True

# 10) Too many params (code smell)
def too_many_params(a, b, c, d, e, f, g):
    return a

# Make sure file executes without errors (but tests don't depend on it)
if __name__ == "__main__":
    add_item("x")
    risky_div(1, 0)
    insecure_eval("1+1")
    debug_something("ok")
