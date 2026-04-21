import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from apps.compiler.services.executor import CodeExecutorService

def test_language(language, code, description):
    print(f"--- {description} ({language}) ---")
    result = CodeExecutorService.execute(language, code)
    print(f"STDOUT: {result['stdout']!r}")
    print(f"STDERR: {result['stderr']}")
    print(f"EXIT CODE: {result['exit_code']}")
    print("-" * 30)

if __name__ == "__main__":
    # The code from the user's screenshot
    c_code = """
#include <stdio.h>
int main() {
    int a = 5, b = 10, sum;
    sum = a + b;
    printf("Sum = %d", sum);
    return 0;
}
"""
    test_language("c", c_code, "User Screenshot Code (C)")

    # Java example
    java_code = """
public class Main {
    public static void main(String[] args) {
        int x = 20;
        int y = 30;
        int result = x * y;
        System.out.println("Result is " + result);
    }
}
"""
    test_language("java", java_code, "Java Logic Snippet")

    # C++ cout example
    cpp_code = """
#include <iostream>
int main() {
    double price = 19.99;
    double tax = 0.05;
    double total = price * (1 + tax);
    std::cout << "Total Price: " << total << endl;
    return 0;
}
"""
    test_language("cpp", cpp_code, "C++ Cout Logic")
