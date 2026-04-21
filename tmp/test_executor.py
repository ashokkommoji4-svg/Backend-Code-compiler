import sys
import os

# Add the project root to sys.path
sys.path.append(r'c:\Users\Useer\Desktop\Code Compiler Baackend')

from apps.compiler.services.executor import CodeExecutorService

def test_c_execution():
    print("Testing C execution (missing gcc)...")
    result = CodeExecutorService.execute("c", "#include <stdio.h>\nint main() { return 0; }")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_c_execution()
