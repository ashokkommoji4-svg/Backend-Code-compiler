import subprocess
import threading
import time
import os

def stream_reader(pipe):
    print("Reader started")
    while True:
        char = pipe.read(1)
        if not char:
            print("Reader EOF")
            break
        print(f"DEBUG: got char '{char}'", end='', flush=True)

code = '#include <stdio.h>\nint main() { printf("Hello, World!"); return 0; }\n'
with open('test_c.c', 'w') as f:
    f.write(code)

# Compile
print("Compiling...")
gcc_path = os.path.join(os.getcwd(), 'bin', 'mingw64', 'bin', 'gcc.exe')
subprocess.run([gcc_path, 'test_c.c', '-o', 'test_c.exe'], capture_output=True)

print("Running...")
process = subprocess.Popen(
    ['test_c.exe'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True
)

t = threading.Thread(target=stream_reader, args=(process.stdout,))
t.start()

exit_code = process.wait()
print(f"\nProcess finished with {exit_code}")
t.join(timeout=2)
print("Reader thread joined")
