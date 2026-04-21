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
    # Test R (complex logic from screenshot)
    r_code = """
a <- 5
b <- 10
sum <- a + b
print(paste("Sum =", sum))
"""
    test_language("r", r_code, "R Logic with Paste")
    
    # Test C (clean output check)
    c_code = """
#include <stdio.h>
int main() {
    int a = 5, b = 10, sum;
    sum = a + b;
    printf("Sum = %d", sum);
    return 0;
}
"""
    test_language("c", c_code, "C Logic check")
