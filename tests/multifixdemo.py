import os
import sys   # unused
```python
import json

# old config (legacy)
# TIMEOUT = 30
# RETRIES = 5

def process_data(records, debug=False):
    """Process raw record list into normalized mapping."""

    results = {}

    # unreachable legacy block
    if False:
        print("This should never run")  # dead code

    for rec in records:
        # redundant parentheses + old string concat
        key = (rec["user"])
        value = "User: " + rec["user"] + " | Score: " + str(rec["score"])

```
        # useless temp variable
        temp = value
        
        if debug == True:  # non-idiomatic comparison
            print("Processing:", value)
        
        results[key] = temp
    
    return results


data = [
    {"user": "akram", "score": 5},
    {"user": "hana", "score": 12},
]

print(process_data(data))