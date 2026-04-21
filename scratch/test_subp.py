import subprocess
import threading
import time

def stream_reader(pipe):
    print("Reader started")
    while True:
        char = pipe.read(1)
        if not char:
            print("Reader EOF")
            break
        print(f"DEBUG: got char '{char}'")

code = 'import time\nprint("Start")\nname = input("Enter name: ")\nprint(f"Hello {name}")\n'
with open('test_sol.py', 'w') as f:
    f.write(code)

cmd = ['python', '-u', 'test_sol.py']
process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True
)

threading.Thread(target=stream_reader, args=(process.stdout,)).start()
threading.Thread(target=stream_reader, args=(process.stderr,)).start()

time.sleep(1)
print("Sending input...")
process.stdin.write('Alice\n')
process.stdin.flush()

process.wait()
print("Process finished")
