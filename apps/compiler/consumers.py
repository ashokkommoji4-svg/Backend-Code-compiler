import json
import subprocess
import threading
import os
import time
import queue
import tempfile
import shutil
from .services.executor import CodeExecutorService
from channels.generic.websocket import WebsocketConsumer

class CompilerConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.process = None
        self.output_thread = None
        self.error_thread = None

    def disconnect(self, close_code):
        self.terminate_process()

    def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'run':
            language = data.get('language')
            code = data.get('code')
            self.run_code(language, code)
        elif action == 'input':
            input_text = data.get('data')
            if self.process and self.process.poll() is None:
                try:
                    # 1. Echo the input back to the terminal (xterm.js)
                    # Use \r\n for the terminal display to move to the next line correctly
                    display_text = input_text.replace('\r', '\r\n')
                    self.send(text_data=json.dumps({
                        'type': 'output',
                        'data': display_text
                    }))

                    # 2. Send the input to the process stdin
                    # Use \n for the process itself
                    process_input = input_text.replace('\r', '\n')
                    self.process.stdin.write(process_input)
                    self.process.stdin.flush()
                except Exception as e:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'data': f'Error writing to stdin: {str(e)}'
                    }))

    def run_code(self, language, code):
        self.terminate_process()
        
        # Prepare command based on language
        cmd = []
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = temp_dir
        
        try:
            if language == 'python':
                file_path = os.path.join(temp_dir, 'solution.py')
                with open(file_path, 'w', encoding='utf-8') as f: f.write(code)
                cmd = ['python', '-u', file_path]
            elif language == 'javascript':
                file_path = os.path.join(temp_dir, 'solution.js')
                with open(file_path, 'w', encoding='utf-8') as f: f.write(code)
                cmd = ['node', file_path]
            elif language == 'typescript':
                file_path = os.path.join(temp_dir, 'solution.ts')
                with open(file_path, 'w', encoding='utf-8') as f: f.write(code)
                cmd = [
                    'npx', 'ts-node', 
                    '--transpile-only', 
                    '--compiler-options', 
                    '{"module":"commonjs","moduleResolution":"node","ignoreDeprecations":"6.0"}',
                    file_path
                ]
            elif language == 'go':
                file_path = os.path.join(temp_dir, 'solution.go')
                with open(file_path, 'w', encoding='utf-8') as f: f.write(code)
                cmd = ['go', 'run', file_path]
            elif language == 'r':
                file_path = os.path.join(temp_dir, 'solution.R')
                with open(file_path, 'w', encoding='utf-8') as f: f.write(code)
                cmd = ['Rscript', file_path]
            elif language in ['c', 'cpp', 'c++']:
                suffix = '.c' if language == 'c' else '.cpp'
                compiler = 'gcc' if language == 'c' else 'g++'
                source_file = os.path.join(temp_dir, f'solution{suffix}')
                binary_file = os.path.join(temp_dir, 'solution.exe' if os.name == 'nt' else 'solution.out')
                with open(source_file, 'w', encoding='utf-8') as f: f.write(code)
                cmd = [compiler, source_file, '-o', binary_file]
            elif language == 'java':
                import re
                match = re.search(r'public\s+class\s+(\w+)', code)
                class_name = match.group(1) if match else 'Main'
                source_file = os.path.join(temp_dir, f'{class_name}.java')
                with open(source_file, 'w', encoding='utf-8') as f: f.write(code)
                cmd = ['javac', source_file] 
            elif language == 'sqlite':
                result = CodeExecutorService.execute_sqlite(code)
                self._send_batch_result(result)
                return
            elif language == 'apex':
                result = CodeExecutorService.execute_apex(code)
                self._send_batch_result(result)
                return
            else:
                self.send(text_data=json.dumps({'type': 'error', 'data': f'Unsupported language: {language}'}))
                return

            # --- Unified Compilation Step for Compiled Languages ---
            if language in ['c', 'cpp', 'c++', 'java']:
                compiler_cmd = cmd[0]
                resolved_compiler = CodeExecutorService.resolve_executable(compiler_cmd)
                if not resolved_compiler:
                    raise FileNotFoundError(f"Compiler '{compiler_cmd}' not found")
                
                self.send(text_data=json.dumps({'type': 'output', 'data': f'\x1b[36mCompiling {language} code...\x1b[0m\r\n'}))
                
                compile_proc = subprocess.run(
                    [resolved_compiler] + cmd[1:],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    env=self._get_env()
                )
                
                if compile_proc.returncode != 0:
                    error_msg = compile_proc.stderr or compile_proc.stdout
                    self.send(text_data=json.dumps({
                        'type': 'output',
                        'data': f'\x1b[31mCompilation Error:\x1b[0m\r\n{error_msg}\r\n'
                    }))
                    self.send(text_data=json.dumps({'type': 'exit', 'data': compile_proc.returncode}))
                    return
                
                # --- After success, set the actual execution command ---
                if language in ['c', 'cpp', 'c++']:
                    cmd = [binary_file]
                elif language == 'java':
                    cmd = ['java', '-cp', temp_dir, class_name]

            # --- Final Path Resolution and Process Start ---
            if cmd:
                # Resolve absolute executable path if not absolute
                if not os.path.isabs(cmd[0]):
                    resolved_exe = CodeExecutorService.resolve_executable(cmd[0])
                    if resolved_exe:
                        cmd[0] = resolved_exe
                    else:
                        raise FileNotFoundError(f"Command '{cmd[0]}' not found")
                elif not os.path.exists(cmd[0]):
                    if not cmd[0].strip().startswith('.'): # Allow relative on some platforms
                        raise FileNotFoundError(f"Executable '{cmd[0]}' not found")

            # Start the interactive process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1, 
                universal_newlines=True,
                env=self._get_env(),
                cwd=temp_dir
            )

            # Start reader threads
            self.output_thread = threading.Thread(target=self.stream_reader, args=(self.process.stdout, 'output'))
            self.error_thread = threading.Thread(target=self.stream_reader, args=(self.process.stderr, 'output'))
            self.output_thread.daemon = True
            self.error_thread.daemon = True
            self.output_thread.start()
            self.error_thread.start()
            
            threading.Thread(target=self.wait_for_exit).start()

        except FileNotFoundError:
            # Fallback to Simulation Mode if real compiler is missing
            msg = f"\x1b[33mCompiler not found for {language}. Switched to Compatibility Mode.\x1b[0m\r\n"
            msg += "\x1b[33mNote: Compatibility Mode is a basic simulation and DOES NOT support interactive typing.\x1b[0m\r\n"
            self.send(text_data=json.dumps({'type': 'output', 'data': msg}))
            
            result = CodeExecutorService.execute(language, code)
            self._send_batch_result(result)
            return

        except Exception as e:
            self.send(text_data=json.dumps({'type': 'error', 'data': str(e)}))

    def _get_env(self):
        env = os.environ.copy()
        # Add common tool paths to environment
        # Local portable compiler (installed in project folder)
        local_bin = os.path.join(os.getcwd(), 'bin', 'mingw64', 'bin')
        local_java = os.path.join(os.getcwd(), 'bin', 'java', 'bin')
        local_go = os.path.join(os.getcwd(), 'bin', 'go', 'bin')
        
        common_paths = [
            local_bin,
            local_java,
            local_go,
            r"C:\msys64\mingw64\bin",
            r"C:\msys64\ucrt64\bin",
            r"C:\msys64\clang64\bin",
            r"C:\msys64\usr\bin",
            r"C:\MinGW\bin",
            r"C:\Program Files\Java\jdk-21\bin",
            r"C:\Program Files\Java\jdk-17\bin",
            r"C:\Program Files\R\R-4.3.2\bin",
            r"C:\Program Files\R\R-4.4.0\bin",
            r"C:\Program Files\Go\bin",
            r"C:\Go\bin",
            r"C:\Program Files\nodejs",
            os.path.join(os.environ.get("REPL_HOME", ""), "node_modules", ".bin"),
            r"C:\Program Files\Python312",
            r"C:\Program Files\Python311",
            r"C:\Program Files\Python310",
        ]
        extra_path = os.pathsep.join([p for p in common_paths if os.path.exists(p)])
        if extra_path:
            env["PATH"] = extra_path + os.pathsep + env.get("PATH", "")
        
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "UTF-8"
        return env

    def _send_batch_result(self, result):
        if result.get('stdout'):
            self.send(text_data=json.dumps({
                'type': 'output',
                'data': result['stdout'].replace('\n', '\r\n')
            }))
        
        if result.get('stderr'):
            self.send(text_data=json.dumps({
                'type': 'output',
                'data': f"\x1b[31m{result['stderr'].replace('\n', '\r\n')}\x1b[0m\r\n"
            }))
            
        self.send(text_data=json.dumps({
            'type': 'exit',
            'data': result.get('exit_code', 0)
        }))

    def stream_reader(self, pipe, stream_type):
        try:
            while True:
                char = pipe.read(1)
                if not char:
                    break
                self.send(text_data=json.dumps({
                    'type': stream_type,
                    'data': char
                }))
        except Exception:
            pass
        finally:
            pipe.close()

    def wait_for_exit(self):
        if self.process:
            exit_code = self.process.wait()
            
            # Small delay to allow OS to flush pipe buffers after process exit
            time.sleep(0.1)
            
            # Ensure reader threads have finished sending all data
            if hasattr(self, 'output_thread') and self.output_thread:
                self.output_thread.join(timeout=5)
            if hasattr(self, 'error_thread') and self.error_thread:
                self.error_thread.join(timeout=5)
            
            self.send(text_data=json.dumps({
                'type': 'exit',
                'data': exit_code
            }))
            self.terminate_process()

    def terminate_process(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                try: self.process.kill()
                except: pass
            self.process = None
        
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
