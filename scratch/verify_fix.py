from apps.compiler.services.executor import CodeExecutorService

code = """
#include <iostream>
#include <string>

int main() {
    std::string name;
    std::cout << "Enter your name: ";
    std::getline(std::cin, name);
    std::cout << "Hello, " << name << "!" << std::endl;
    return 0;
}
"""

# Test with no input (it should default to empty string, not 0)
print("--- Test 1: No Input ---")
result = CodeExecutorService.execute("cpp", code, "")
print(f"STDOUT: \n{result['stdout']}")
print(f"STDERR: {result['stderr']}")

# Test with input
print("\n--- Test 2: Input 'Antigravity' ---")
result = CodeExecutorService.execute("cpp", code, "Antigravity")
print(f"STDOUT: \n{result['stdout']}")

# Test with std::cin >>
code2 = """
#include <iostream>
int main() {
    int a, b;
    std::cout << "A: ";
    std::cin >> a;
    std::cout << "B: ";
    std::cin >> b;
    std::cout << "Sum: " << (a + b) << std::endl;
    return 0;
}
"""
print("\n--- Test 3: std::cin >> ---")
result = CodeExecutorService.execute("cpp", code2, "10 20")
print(f"STDOUT: \n{result['stdout']}")
