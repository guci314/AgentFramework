#!/usr/bin/env python3
"""
Hello World example module
"""

def hello():
    """Print Hello World"""
    print("Hello, World!")

def hello_name(name):
    """Print personalized greeting"""
    print(f"Hello, {name}!")

if __name__ == "__main__":
    hello()
    hello_name("Claude")