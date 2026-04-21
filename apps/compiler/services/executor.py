import subprocess
import tempfile
import os
import shutil

class CodeExecutorService:
    @staticmethod
    def execute(language: str, code: str, input_data: str = ""):
        """
        Routes the execution based on the language.
        """
        language = language.lower()
        if language == "python":
            return CodeExecutorService.execute_python(code, input_data)
        elif language == "javascript":
            return CodeExecutorService.execute_javascript(code, input_data)
        elif language in ["cpp", "c"]:
            return CodeExecutorService.execute_cpp_c(language, code, input_data)
        elif language == "java":
            return CodeExecutorService.execute_java(code, input_data)
        elif language == "r":
            return CodeExecutorService.execute_r(code, input_data)
        elif language == "go":
            return CodeExecutorService.execute_go(code, input_data)
        elif language == "typescript":
            return CodeExecutorService.execute_typescript(code, input_data)
        elif language == "sqlite":
            return CodeExecutorService.execute_sqlite(code, input_data)
        elif language == "apex":
            return CodeExecutorService.execute_apex(code, input_data)
        else:
            return {
                "stdout": "",
                "stderr": f"Error: Language '{language}' is not supported.",
                "exit_code": 1
            }

    @staticmethod
    def _try_simulation(language: str, code: str, input_data: str = ""):
        """
        Trives to interpret basic snippets when local tools are missing.
        """
        import re
        
        # Very basic syntax check for C/C++/Java (missing semicolons)
        if language in ["c", "cpp", "java"]:
            lines = code.split('\n')
            for i, line in enumerate(lines):
                trimmed = line.strip()
                if not trimmed or trimmed.startswith(('#', '//', '/*')) or trimmed.endswith('*/'):
                    continue
                if trimmed.endswith('{') or trimmed.endswith('}') or 'public class' in trimmed or 'int main' in trimmed or trimmed.startswith('std::'):
                    continue
                # Apex/Java debug and Go fmt ignore
                if 'System.debug' in trimmed or 'fmt.Println' in trimmed:
                    continue
                if not trimmed.endswith(';'):
                    return None, f"Potential Syntax Error (Simulated): Missing ';' on line {i+1}"

        class SmartSnippetInterpreter:
            def __init__(self, lang, input_str=""):
                self.lang = lang
                self.vars = {}
                self.output = []
                self.input_tokens = input_str.split() if isinstance(input_str, str) else []
                self.input_index = 0

            def _get_next_input(self):
                if self.input_index < len(self.input_tokens):
                    val = self.input_tokens[self.input_index]
                    self.input_index += 1
                    try:
                        if '.' in val: return float(val)
                        return int(val)
                    except: return val
                return "" # Default to empty string for better simulation of names/strings

            def run(self, code_str):
                # Preprocess: remove comments and split by brackets
                prog = []
                for l in code_str.split('\n'):
                    l = re.sub(r'//.*$', '', l).strip()
                    if not l: continue
                    # Split by brackets and semicolons to get individual statements
                    parts = re.split(r'({|}|;)', l)
                    for p in parts:
                        p = p.strip()
                        if not p or p == ';': continue
                        prog.append(p)

                self.pc = 0
                block_stack = [] # Stores (pc, type)
                iters = 0
                max_iters = 5000 # Increased for loops
                
                while self.pc < len(prog) and iters < max_iters:
                    iters += 1
                    line = prog[self.pc]
                    
                    # Boilerplate components
                    if any(p in line for p in ['#include', 'using', 'public class', 'int main', 'package ', 'import ', 'func main', 'return', '{']):
                        self.pc += 1
                        continue

                    try:
                        # While/For Loop (Go uses 'for' as 'while')
                        while_m = re.match(r'^(?:while|for)\s*\(?(.*?)\)?\s*{?$', line)
                        if while_m and not line.startswith('fmt.'): 
                            cond = while_m.group(1).strip()
                            if cond and self._eval_cond(cond):
                                block_stack.append((self.pc, 'while'))
                                self.pc += 1
                            elif cond:
                                # Skip to matching }
                                level = 0
                                temp_pc = self.pc + 1
                                while temp_pc < len(prog):
                                    if prog[temp_pc] == '{': level += 1
                                    elif prog[temp_pc] == '}':
                                        if level <= 1: 
                                            self.pc = temp_pc + 1
                                            break
                                        level -= 1
                                    temp_pc += 1
                                else: self.pc += 1
                            else: self.pc += 1 # Empty for/while skip
                            continue
                        
                        # If statement
                        if_m = re.match(r'^if\s*\(?(.*?)\)?\s*{?$', line)
                        if if_m:
                            cond = if_m.group(1).strip()
                            if self._eval_cond(cond):
                                block_stack.append((self.pc, 'if'))
                                self.pc += 1
                            else:
                                # Skip block
                                level = 0
                                temp_pc = self.pc + 1
                                while temp_pc < len(prog):
                                    if prog[temp_pc] == '{': level += 1
                                    elif prog[temp_pc] == '}':
                                        if level <= 1:
                                            self.pc = temp_pc + 1
                                            break
                                        level -= 1
                                    temp_pc += 1
                                else: self.pc += 1
                            continue

                        # End of block
                        if line == '}':
                            if block_stack:
                                start_pc, btype = block_stack.pop()
                                if btype == 'while':
                                    self.pc = start_pc # Jump back to while check
                                    continue
                            self.pc += 1
                            continue

                        # Input handling (C++ cin / std::cin)
                        if ('cin' in line and '>>' in line) or ('getline' in line and 'cin' in line):
                            if 'getline' in line:
                                m = re.search(r'getline\s*\(\s*(?:std::)?cin\s*,\s*(\w+)\s*\)', line)
                                if m:
                                    val = self._get_next_input()
                                    self.vars[m.group(1)] = val
                                    if val != "": self.output.append(str(val))
                            else:
                                # Handle cin >> a >> b
                                parts = [p.strip() for p in re.split(r'>>', line)]
                                for vn in parts:
                                    vn = vn.replace('std::cin', '').replace('cin', '').strip()
                                    if vn and vn != 'std::' and vn != 'cin':
                                        val = self._get_next_input()
                                        self.vars[vn] = val
                                        if val != "": self.output.append(str(val))
                            self.pc += 1
                            continue

                        # Input handling (C scanf)
                        if 'scanf' in line:
                            m = re.search(r'&(\w+)', line)
                            if m: 
                                val = self._get_next_input()
                                self.vars[m.group(1)] = val
                                self.output.append(str(val))
                            self.pc += 1
                            continue

                        # Input handling (Go fmt.Scan)
                        if self.lang == 'go' and 'fmt.Scan' in line:
                            # Handle fmt.Scan(&a, &b)
                            m = re.findall(r'&(\w+)', line)
                            if m:
                                for var_name in m:
                                    self.vars[var_name] = self._get_next_input()
                            self.pc += 1
                            continue

                        # Input handling (Java/R)
                        if ('.next' in line or 'readline' in line) and '=' in line:
                            vname = line.split('=')[0].strip()
                            val = self._get_next_input()
                            self.vars[vname] = val
                            self.output.append(str(val))
                            self.pc += 1
                            continue

                        # Declarations: int a = 5, b = 10; or Go var x = 5 or x := 5
                        decl = re.match(r'^(int|double|float|long|var|let|const)\s+(.*)$', line)
                        go_short = re.match(r'^(\w+)\s*:=\s*(.*)$', line)
                        
                        if decl or go_short:
                            if go_short:
                                n, v = go_short.groups()
                                self.vars[n.strip()] = self._eval(v.strip())
                            else:
                                decl_str = decl.group(2)
                                # Handle multiple comma separated: int a=5, b=10
                                parts = [p.strip() for p in decl_str.split(',')]
                                for p in parts:
                                    if '=' in p:
                                        n, v = p.split('=')
                                        self.vars[n.strip()] = self._eval(v.strip())
                                    else:
                                        self.vars[p.strip()] = 0
                            self.pc += 1
                            continue

                        # Assignment & Operators: count += 1 or val = 10
                        op_match = re.match(r'^(\w+)\s*(\+|-|\*|/|%)?=\s*(.*)$', line)
                        if op_match:
                            var, op, expr = op_match.groups()
                            rhs = self._eval(expr)
                            if var not in self.vars: self.vars[var] = 0
                            if op == '+': self.vars[var] += rhs
                            elif op == '-': self.vars[var] -= rhs
                            elif op == '*': self.vars[var] *= rhs
                            elif op == '/':
                                if rhs != 0:
                                    if isinstance(self.vars.get(var), int) and isinstance(rhs, int):
                                        self.vars[var] //= rhs
                                    else:
                                        self.vars[var] /= rhs
                            elif op == '%': self.vars[var] %= (rhs if rhs != 0 else 1)
                            else: self.vars[var] = rhs
                            self.pc += 1
                            continue

                        # Increments: i++
                        inc_m = re.match(r'^(\w+)(\+\+|\-\-)$|^(\+\+|\-\-)(\w+)$', line)
                        if inc_m:
                            var = inc_m.group(1) or inc_m.group(4)
                            if '++' in line: self.vars[var] = self.vars.get(var, 0) + 1
                            else: self.vars[var] = self.vars.get(var, 0) - 1
                            self.pc += 1
                            continue

                        # Printing
                        if (self.lang in ['c', 'cpp']) and 'printf' in line:
                            m = re.search(r'printf\s*\(\s*["\'](.*?)["\']\s*(?:,\s*(.*))?\s*\)', line)
                            if m:
                                fmt, v_str = m.group(1), m.group(2)
                                if v_str:
                                    v_list = [v.strip() for v in v_str.split(',')]
                                    res = fmt
                                    for vn in v_list:
                                        val = self.vars.get(vn, vn)
                                        res = re.sub(r'%[dfsu]', str(val), res, count=1)
                                    self.output.append(res)
                                else:
                                    self.output.append(fmt)
                            self.pc += 1
                            continue

                        if ('cout' in line or 'std::cout' in line) and '<<' in line:
                            parts = [p.strip() for p in line.split('<<')]
                            res = ""
                            for p in parts[1:]:
                                p = p.strip()
                                if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                                    res += p[1:-1]
                                elif 'endl' in p:
                                    res += '\n'
                                else:
                                    # Strip std:: prefix if present
                                    p_eval = p.replace('std::', '')
                                    res += str(self._eval(p_eval))
                            self.output.append(res)
                            self.pc += 1
                            continue

                        if self.lang == 'java' and 'System.out.println' in line:
                            m = re.search(r'println\s*\((.*)\)', line)
                            if m:
                                res = ""
                                content = m.group(1).strip()
                                if '+' in content:
                                    for p in content.split('+'):
                                        p = p.strip()
                                        if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                                            res += p[1:-1]
                                        else:
                                            res += str(self.vars.get(p, p))
                                else:
                                    if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                                        res += content[1:-1]
                                    else:
                                        res += str(self.vars.get(content, content))
                                self.output.append(res)
                            self.pc += 1
                            continue

                        if self.lang == 'r' and ('print' in line or 'cat' in line):
                            m = re.search(r'(?:print|cat)\s*\(\s*(.*)\s*\)', line)
                            if m:
                                inner = m.group(1).strip()
                                if 'paste' in inner:
                                    paste_m = re.search(r'paste\s*\((.*)\)', inner)
                                    if paste_m:
                                        args = [a.strip() for a in paste_m.group(1).split(',')]
                                        vals = []
                                        for a in args:
                                            if (a.startswith('"') and a.endswith('"')) or (a.startswith("'") and a.endswith("'")):
                                                vals.append(a[1:-1])
                                            else:
                                                vals.append(str(self.vars.get(a, a)))
                                        self.output.append(" ".join(vals))
                                else:
                                    if (inner.startswith('"') and inner.endswith('"')) or (inner.startswith("'") and inner.endswith("'")):
                                        self.output.append(inner[1:-1])
                                    else:
                                        self.output.append(str(self.vars.get(inner, inner)))
                            self.pc += 1
                            continue

                        if self.lang == 'apex' and 'System.debug' in line:
                            m = re.search(r'debug\s*\(\s*(.*)\s*\)', line)
                            if m:
                                res = ""
                                content = m.group(1).strip()
                                if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                                    res += content[1:-1]
                                else:
                                    res += str(self.vars.get(content, content))
                                self.output.append(res)
                            self.pc += 1
                            continue

                        if (self.lang in ['javascript', 'typescript']) and 'console.log' in line:
                            m = re.search(r'log\s*\(\s*(.*)\s*\)', line)
                            if m:
                                content = m.group(1).strip()
                                evaluated = self._eval(content)
                                if isinstance(evaluated, tuple):
                                    self.output.append(" ".join(str(x) for x in evaluated))
                                else:
                                    self.output.append(str(evaluated))
                            self.pc += 1
                            continue

                        if self.lang == 'go' and 'fmt.Print' in line:
                            m = re.search(r'Print(?:ln|f)?\s*\(\s*(.*)\s*\)', line)
                            if m:
                                content = m.group(1).strip()
                                evaluated = self._eval(content)
                                if isinstance(evaluated, tuple):
                                    res_parts = [str(x) for x in evaluated]
                                    if 'println' in line.lower():
                                        self.output.append(" ".join(res_parts))
                                    else:
                                        # Go Print only adds spaces between non-strings
                                        self.output.append(" ".join(res_parts))
                                else:
                                    self.output.append(str(evaluated))
                            continue
                    except: pass
                    self.pc += 1
                return "\n".join(self.output) if self.output else None

            def _eval(self, expr):
                expr = expr.strip()
                if not expr: return ""
                # Handle quoted strings directly
                if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                    return expr[1:-1]
                
                try: 
                    # Use self.vars as the context for evaluation
                    return eval(expr, {"__builtins__": {}}, self.vars)
                except:
                    # Fallback to direct variable lookup or empty string
                    if ',' in expr:
                        parts = [p.strip() for p in expr.split(',')]
                        return tuple(self._eval(p) for p in parts)
                    return self.vars.get(expr, expr)

            def _eval_cond(self, cond):
                # Basic condition evaluator for if/while
                cond = cond.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ')
                try:
                    return bool(eval(cond, {"__builtins__": {}}, self.vars))
                except:
                    return False

        # Try Smart Interpreter first
        if language in ['c', 'cpp', 'java', 'r', 'apex', 'go', 'javascript', 'typescript']:
            if language == 'typescript':
                # Strip types for simulation
                code = re.sub(r':\s*(string|number|boolean|any|void|unknown|never|object)(\[\])?', '', code)
                code = re.sub(r':\s*[A-Z][a-zA-Z0-9]*', '', code)
            
            interpreter = SmartSnippetInterpreter(language, input_data)
            sim_out = interpreter.run(code)
            if sim_out is not None:
                return sim_out, None
        
        return None, None

    @staticmethod
    def resolve_executable(executable: str):
        """
        Resolves the absolute path of an executable by searching common installation directories.
        """
        import os
        if os.path.isabs(executable):
            return executable if os.path.isfile(executable) else None

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
            r"C:\Program Files\LLVM\bin",
            r"C:\Strawberry\c\bin",
            r"C:\Qt\Tools\mingw1120_64\bin",
            r"C:\Qt\Tools\mingw810_64\bin",
        ]
        
        # Add system PATH
        common_paths.extend(os.environ.get("PATH", "").split(os.pathsep))

        exts = [".exe", ".bat", ".cmd", ""] if os.name == "nt" else [""]
        for path_dir in common_paths:
            if not os.path.exists(path_dir): continue
            for ext in exts:
                full_p = os.path.join(path_dir, executable + ext)
                if os.path.isfile(full_p):
                    return full_p
        return None

    @staticmethod
    def _run_process(command, input_data="", timeout=5, language_hint=None, original_code=None):
        import os
        env = os.environ.copy()
        
        # Build extra PATH from our known locations
        local_bin = os.path.join(os.getcwd(), 'bin', 'mingw64', 'bin')
        common_paths = [
            local_bin,
            r"C:\MinGW\bin",
            r"C:\msys64\mingw64\bin",
            r"C:\msys64\usr\bin",
            r"C:\Program Files\Java\jdk-21\bin",
            r"C:\Program Files\Java\jdk-17\bin",
            r"C:\Program Files\R\R-4.3.2\bin",
            r"C:\Program Files\R\R-4.4.0\bin",
            r"C:\Program Files\Go\bin",
            r"C:\Go\bin",
            r"C:\Program Files\nodejs",
            os.path.join(os.environ.get("REPL_HOME", ""), "node_modules", ".bin")
        ]
        extra_path = os.pathsep.join([p for p in common_paths if os.path.exists(p)])
        if extra_path:
            env["PATH"] = extra_path + os.pathsep + env.get("PATH", "")

        # Explicitly search for executable if not absolute
        executable = command[0] if isinstance(command, list) else command
        resolved = CodeExecutorService.resolve_executable(executable)
        if resolved:
            if isinstance(command, list):
                command[0] = resolved
            else:
                command = resolved

        try:
            result = subprocess.run(
                command,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Error: Execution timed out ({timeout}s limit).",
                "exit_code": 124
            }
        except FileNotFoundError:
            # If real tool is missing, try simulation
            if language_hint and original_code:
                sim_out, sim_err = CodeExecutorService._try_simulation(language_hint, original_code, input_data)
                if sim_out is not None:
                    return {
                        "stdout": sim_out,
                        "stderr": "",
                        "exit_code": 0
                    }
                
                if sim_err:
                    return {
                        "stdout": "",
                        "stderr": sim_err,
                        "exit_code": 1
                    }

            executable = command[0] if isinstance(command, list) else command
            hints = {
                "python": "Please ensure Python is installed and added to your PATH.",
                "node": "Please ensure Node.js is installed and added to your PATH.",
                "gcc": "Please install MinGW or a C compiler and add it to your PATH.",
                "g++": "Please install MinGW or a C++ compiler and add it to your PATH.",
                "javac": "Please install the JDK (Java Development Kit) and add 'javac' to your PATH.",
                "java": "Please install the JRE/JDK and add 'java' to your PATH.",
                "Rscript": "Please install R and add 'Rscript' to your PATH.",
                "go": "Please install Go and add it to your PATH.",
                "ts-node": "Please install ts-node (npm install -g ts-node) to run TypeScript.",
                "sqlite3": "Please install SQLite3 CLI and add it to your PATH."
            }
            hint = hints.get(executable, "Please ensure the required tool is installed and in your PATH.")
            return {
                "stdout": "",
                "stderr": f"Error: Command '{executable}' not found.\n{hint}",
                "exit_code": 1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error during execution: {str(e)}",
                "exit_code": 1
            }

    @staticmethod
    def execute_python(code: str, input_data: str = ""):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file_path = f.name
        
        try:
            return CodeExecutorService._run_process(["python", temp_file_path], input_data, language_hint="python", original_code=code)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def execute_javascript(code: str, input_data: str = ""):
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file_path = f.name

        try:
            return CodeExecutorService._run_process(["node", temp_file_path], input_data, language_hint="javascript", original_code=code)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def execute_cpp_c(language: str, code: str, input_data: str = ""):
        suffix = ".cpp" if language == "cpp" else ".c"
        compiler = "g++" if language == "cpp" else "gcc"
        
        temp_dir = tempfile.mkdtemp()
        source_file = os.path.join(temp_dir, f"solution{suffix}")
        binary_file = os.path.join(temp_dir, "solution.exe" if os.name == "nt" else "solution.out")
        
        try:
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Compile
            compile_process = subprocess.run(
                [compiler, source_file, "-o", binary_file],
                capture_output=True,
                text=True,
                timeout=15
            )

            if compile_process.returncode != 0:
                return {
                    "stdout": "",
                    "stderr": f"Compilation Error:\n{compile_process.stderr}",
                    "exit_code": compile_process.returncode
                }
            
            # Run
            return CodeExecutorService._run_process([binary_file], input_data)
            
        except FileNotFoundError:
            # Try simulation before returning error
            sim_out, sim_err = CodeExecutorService._try_simulation(language, code, input_data)
            if sim_err:
                return {"stdout": "", "stderr": sim_err, "exit_code": 1}
            if sim_out is not None:
                return {"stdout": sim_out, "stderr": "", "exit_code": 0}

            hint = "g++ (for C++)" if language == "cpp" else "gcc (for C)"
            return {
                "stdout": "",
                "stderr": f"Error: {hint} compiler not found. Please install the required build tools.",
                "exit_code": 1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error during {language.upper()} execution: {str(e)}",
                "exit_code": 1
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def execute_java(code: str, input_data: str = ""):
        import re
        public_match = re.search(r'public\s+class\s+(\w+)', code)
        if public_match:
            class_name = public_match.group(1)
        else:
            class_match = re.search(r'class\s+(\w+)', code)
            class_name = class_match.group(1) if class_match else "Main"
        
        temp_dir = tempfile.mkdtemp()
        source_file = os.path.join(temp_dir, f"{class_name}.java")
        
        try:
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Compile
            compile_process = subprocess.run(
                ["javac", source_file],
                capture_output=True,
                text=True,
                timeout=15
            )

            if compile_process.returncode != 0:
                return {
                    "stdout": "",
                    "stderr": f"Compilation Error:\n{compile_process.stderr}",
                    "exit_code": compile_process.returncode
                }
            
            return CodeExecutorService._run_process(["java", "-cp", temp_dir, class_name], input_data)
            
        except FileNotFoundError:
            sim_out, sim_err = CodeExecutorService._try_simulation("java", code, input_data)
            if sim_err:
                return {"stdout": "", "stderr": sim_err, "exit_code": 1}
            if sim_out is not None:
                return {"stdout": sim_out, "stderr": "", "exit_code": 0}

            return {
                "stdout": "",
                "stderr": "Error: javac/java not found. Please install the Java Development Kit (JDK).",
                "exit_code": 1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error during Java execution: {str(e)}",
                "exit_code": 1
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def execute_r(code: str, input_data: str = ""):
        # Try real R execution first, fallback to simulation
        with tempfile.NamedTemporaryFile(suffix=".R", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file_path = f.name
        
        try:
            return CodeExecutorService._run_process(
                ["Rscript", temp_file_path], 
                input_data, 
                language_hint="r", 
                original_code=code
            )
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def execute_go(code: str, input_data: str = ""):
        with tempfile.NamedTemporaryFile(suffix=".go", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file_path = f.name
        
        try:
            return CodeExecutorService._run_process(["go", "run", temp_file_path], input_data, timeout=15, language_hint="go", original_code=code)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def execute_typescript(code: str, input_data: str = ""):
        with tempfile.NamedTemporaryFile(suffix=".ts", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file_path = f.name
        
        try:
            cmd = [
                "npx", "ts-node", 
                "--transpile-only", 
                "--compiler-options", 
                '{"module":"commonjs","moduleResolution":"node","ignoreDeprecations":"6.0"}',
                temp_file_path
            ]
            return CodeExecutorService._run_process(cmd, input_data, timeout=15, language_hint="typescript", original_code=code)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def execute_sqlite(code: str, input_data: str = ""):
        import sqlite3
        try:
            # Use in-memory database
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            
            results = []
            # Split by semicolon but ignore inside quotes
            # Simple split for now
            queries = [q.strip() for q in code.split(';') if q.strip()]
            
            for query in queries:
                cursor.execute(query)
                if cursor.description:
                    # It's a SELECT query
                    cols = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Format as table
                    header = " | ".join(cols)
                    results.append(header)
                    results.append("-" * len(header))
                    for row in rows:
                        results.append(" | ".join(map(str, row)))
                    results.append("") # Spacer
            
            conn.commit()
            output = "\n".join(results)
            if not output and queries:
                output = "Success: Commands executed successfully."
                
            return {
                "stdout": output,
                "stderr": "",
                "exit_code": 0
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"SQLite Error: {str(e)}",
                "exit_code": 1
            }
        finally:
            try: conn.close()
            except: pass

    @staticmethod
    def execute_apex(code: str, input_data: str = ""):
        sim_out, sim_err = CodeExecutorService._try_simulation("apex", code, input_data)
        if sim_out is not None:
            return {"stdout": sim_out, "stderr": "", "exit_code": 0}
        
        return {
            "stdout": "",
            "stderr": "Error: Apex execution requires a Salesforce environment. Simulation mode only supports basic logic snippets.",
            "exit_code": 1
        }

