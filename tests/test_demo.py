#this is a test for the llm integrated ci 
from src.demo import greet

def test_greet():
    assert greet("Akram") == "Hello, Akram!"
