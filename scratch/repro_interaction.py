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
x = input("Enter first number: ")
y = input("Enter second number: ")
print(f"Sum: {int(x) + int(y)}")
"""

with open("temp_test.py", "w") as f:
    f.write(code)

process = subprocess.Popen(
    ["python", "-u", "temp_test.py"],
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
os.remove("temp_test.py")
