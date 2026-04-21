import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock Django setup if needed, but we can just test the service
from apps.compiler.services.executor import CodeExecutorService

def test_language(language, code):
    print(f"Testing {language}...")
    result = CodeExecutorService.execute(language, code)
    print(f"STDOUT: {result['stdout']}")
    print(f"STDERR: {result['stderr']}")
    print(f"EXIT CODE: {result['exit_code']}")
    print("-" * 20)

if __name__ == "__main__":
    # Test complex C++ that simulation won't catch
    test_language("cpp", "#include <iostream>\nint main() { int a = 5; std::cout << a + 10; return 0; }")
    
    # Test R again with complex code
    test_language("r", "a <- 10; print(a + 5)")
