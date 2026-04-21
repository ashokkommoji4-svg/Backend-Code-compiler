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
    # Test Python
    test_language("python", "print('Hello from Python')")
    
    # Test JavaScript
    test_language("javascript", "console.log('Hello from Node')")
    
    # C++ test (fixing the string quotes)
    test_language("cpp", "#include <iostream>\nint main() { std::cout << \"Hello from C++\"; return 0; }")

    # Java test
    test_language("java", "class Test { public static void main(String[] args) { System.out.println(\"Hello from Java\"); } }")


    # R test
    test_language("r", "print('Hello from R')")
