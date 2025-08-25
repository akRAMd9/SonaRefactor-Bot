
from src.demo import greet
#test ci isnt for the weak

def test_greet():
    assert greet("Akram") == "Hello, Akram!"
