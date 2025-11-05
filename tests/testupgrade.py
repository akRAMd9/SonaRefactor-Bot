```python
# This file is intentionally written to trigger a SAFE auto-fix.

import os   # <- used
import sys  # <- UNUSED, Sonar should flag this

def greet(name):
    message = "Hello, " + name   # <- fine
    return message

print(greet("Akram"))
```