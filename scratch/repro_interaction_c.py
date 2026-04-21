import subprocess
import threading
import time
import os

def stream_reader(pipe):
    while True:
        char = pipe.read(1)
        if not char:
            break
        print(f"DEBUG OUT: '{char}'", flush=True)

code = """
#include <stdio.h>
int main() {
    int x, y;
    printf("Enter first number: ");
    // fflush(stdout); // Most beginners DON'T do this
    scanf("%d", &x);
    printf("Enter second number: ");
    // fflush(stdout);
    scanf("%d", &y);
    printf("Sum: %d\\n", x + y);
    return 0;
}
"""

with open("temp_test.c", "w") as f:
    f.write(code)

# Compile
subprocess.run(["gcc", "temp_test.c", "-o", "temp_test.exe"], capture_output=True)

process = subprocess.Popen(
    ["temp_test.exe"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True
)

threading.Thread(target=stream_reader, args=(process.stdout,), daemon=True).start()

time.sleep(1)
print("Sending '10\\n'...")
process.stdin.write("10\n")
process.stdin.flush()

time.sleep(1)
print("Sending '20\\n'...")
process.stdin.write("20\n")
process.stdin.flush()

process.wait()
os.remove("temp_test.c")
os.remove("temp_test.exe")
