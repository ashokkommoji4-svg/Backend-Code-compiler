
from apps.compiler.services.executor import CodeExecutorService

def test_reverse_number_sim():
    code = """
    #include <iostream>
    using namespace std;
    int main() {
        int num = 1234, reverse = 0, remainder;
        while (num != 0) {
            remainder = num % 10;
            reverse = reverse * 10 + remainder;
            num /= 10;
        }
        cout << "Reversed Number: " << reverse << endl;
        return 0;
    }
    """
    stdout, stderr = CodeExecutorService._try_simulation("cpp", code, "1234")
    print(f"STDOUT: {stdout}")
    print(f"STDERR: {stderr}")
    assert "Reversed Number: 4321" in stdout
    print("Test passed!")

if __name__ == "__main__":
    test_reverse_number_sim()
