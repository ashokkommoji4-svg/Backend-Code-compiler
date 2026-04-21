import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from apps.compiler.services.executor import CodeExecutorService

def test_language(language, code, description):
    print(f"--- {description} ({language}) ---")
    result = CodeExecutorService.execute(language, code)
    print(f"STDOUT: {result['stdout']!r}")
    print(f"STDERR: {result['stderr']!r}")
    print(f"EXIT CODE: {result['exit_code']}")
    print("-" * 30)

if __name__ == "__main__":
    # Test C (clean output)
    test_language("c", '#include <stdio.h>\nint main() {\n    printf("Hello, C!");\n    return 0;\n}', "C Clean Output")
    
    # Test R (clean output)
    test_language("r", 'print("Hello, R!")', "R Clean Output")
    
    # Test Java (clean output)
    test_language("java", 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Java!");\n    }\n}', "Java Clean Output")
    
    # Test HTML (clean output)
    test_language("html", "<h1>Hello</h1>", "HTML Clean Output")
    
    # Test CSS (clean output)
    test_language("css", "body { color: red; }", "CSS Clean Output")
    
    # Test Error (Syntax)
    test_language("c", "int main() { printf(\"Missing semicolon\") }", "C Syntax Error")
