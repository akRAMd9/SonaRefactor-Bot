# This file is intentionally written to trigger a SAFE auto-fix.

import os   # <- used
import sys  # <- UNUSED, Sonar should flag this

def greet(name):
    message = "Hello, " + name   # <- fine
    unused_var = 42              # <- UNUSED variable, also safe fix
    return message

print(greet("Akram"))
