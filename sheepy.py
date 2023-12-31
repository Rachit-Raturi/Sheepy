#!/usr/bin/env python3

import sys
import re

def check(line, indent, file):
    line = line.strip()
    line = re.sub(r"^\s+", ' ', line)
    if line.strip():
        if line.startswith("echo "):
            return echo(line)
        elif re.search(r'^\s*\w+=', line):
            return variable(line)
        elif line.startswith("#"):
            if line.startswith("# "):
                return line
            else:
                return "".strip('\n')
        elif line.startswith("cd "):
            return cd(line)
        elif line.startswith("for "):
            return for_command(line, file, indent)
        elif line.startswith("exit "):
            return exit_command(line)
        elif line.startswith("read "):
            return read_command(line)
        elif line.startswith("if "):
            return if_command(line, file, indent)
        elif line.startswith("while "):
            return while_command(line, file, indent)
        else:
            return external(line)
    else:
        return "".strip('\n')

def echo(printString):

    message = printString.split("echo ", 1)[1].strip()
    comments = False
    if re.search(r'\s+ #', message):
        splitter = message.split("#")
        message = splitter[0]
        comment = splitter[1]
        comments = True

    if message.startswith("\'"):
        return "print(f" + message + ")"
    
    if not message.startswith("\""):
        message = re.sub(r"\s+", ' ', message).strip()
    else:
        message = re.sub (r'\"', "", message)

    counter = 0
    string = "print(f\""
    for word in message.split(" "):
        if word.startswith("$", 0, 1):
            word = word.split("$", 1)[1].strip()
            if word in "0123456789":
                string += "{" + "sys.argv[" + word + "]" + "}"
            else:
                string += "{" + word + "}"
        elif re.search(r'\${.*}', word):
            string += re.sub(r'\$(?!\w)(?=\{)', "",  word)
        elif re.search(r'\$\w+', word):
            word = re.sub(r'\$(\w+)', r'{\1}', word)
            string += word
        else:
            string += word
        if counter < (len(message.split(" ")) - 1):
            string += " "
        counter += 1
    string += "\")"

    if comments:
        string += "\n#" + comment
    
    return string 

def variable(declaration):
    variableName = declaration.split("=")[0].strip()
    value = declaration.split("=")[1].strip()

    comments = False
    if re.search(r'\s+ #', value):
        splitter = value.split("#")
        value = splitter[0]
        comment = splitter[1]
        comments = True

    if re.search(r'\${.*}', value):
            value = re.sub(r'\$(?!\w)(?=\{)', "",  value)

    if re.match(r'\$[0-9]', value):
        if comments:
            return variableName + " = " + "sys.argv[" + value[1:] + "] #" + comment
        else:
            return variableName + " = " + "sys.argv[" + value[1:] + "]"
    elif value.startswith("`"):
        if comments:
            return variableName + " = " + external(value[1:]) + " #" + comment
        else:
            return variableName + " = " + external(value[1:])
    elif value.startswith("\'"):
        if comments:
            return variableName + " = " + "\'" + value[1:-1] + "\' #" + comment
        else:
            return variableName + " = " + "\'" + value[1:-1] + "\'"
    elif re.search(r'\$\w+', value):
        value = re.sub(r'\$(\w+)', r'{\1}', value)
        if comments:
            return variableName + " = " + "f\'" + value + "\' #" + comment
        else:
            return variableName + " = " + "f\'" + value + "\'"
    elif value.startswith("\""):
        if comments:
            return variableName + " = " + "f\"" + value[1:-1] + "\" #" + comment
        else:
            return variableName + " = " + "f\"" + value[1:-1] + "\""
    else:
        if comments:
            return variableName + " = " + "\'" + value + "\' #" + comment
        else:
            return variableName + " = " + "\'" + value + "\'"

def imports(file):
    print()

    content = file.read()

    imports = set()

    file.seek(0)
    for line in file:
        line = line.strip()
        line = re.sub(r"\s+", ' ', line)
        if line.strip().startswith("ls"):
            imports.add("import subprocess")
        elif line.strip().startswith("pwd"):
            imports.add("import subprocess")
        elif line.strip().startswith("date"):
            imports.add("import subprocess")
        elif line.strip().startswith("mkdir"):
           imports.add("import subprocess")
        elif line.strip().startswith("cd"):
            imports.add("import os")
        elif re.search(r'if test.* -(r|d|nt|ot|-b|c|e|f|g|h|k|r|s|x|w|L) ', line):
            imports.add("import os")
        elif line.strip().startswith("exit"):
            imports.add("import sys")
        elif re.search(r'\$[0-9]', line):
            imports.add("import sys")
        elif not line.strip().startswith("#"):
            if "*" in line or "?" in line or "[" in line or "]" in line:
                imports.add("import glob")
            
            if line.split(" ")[0] not in ["echo", "exit", "cd", "test", "for", "while", "if", "do", "done", "fi", "then", "elif", "else"] and line:
                if "=" not in line:
                    imports.add("import subprocess")
                else:
                    if re.search(r'`.*`', line):
                        imports.add("import subprocess")

    return imports

def cd(line):
    path = line.split()[1]

    if re.search(r'\$\w+', path):
        path = re.sub(r'\$(\w+)', r'{\1}', path)

    string = "os.chdir(\'" + path + "\')"
    return string

def external(line):
    tokens = line.split()
    string = "subprocess.run([" 
    for token in  tokens:
        if token.endswith("`"):
            token = token[:-1]

        if token.startswith("$"):
            token = re.sub(r'\$', "", token)
            string += token + ", "
        else:
            string += "\'" + token + "\', "
        
    string = string.strip()
    string = string.strip(",")
    string +=  "], capture_output=True, text=True).stdout.strip()"
    return string

def for_command(line, file, indent):
    string = ""
    for arg in line.split(" ")[:3]:
        string += arg + " "
    string += "["
    for arg in line.strip().split(" ")[3:]:
        string += "\"" + arg + "\", "
    
    string = string.strip()
    string = string.strip(",")
    string += "]:\n"

    spaces = " " * (4 * indent)

    for lines in file:
        if lines.strip() == "done":
            return string
        elif lines.strip() == "do":
            continue
        string += spaces + check(lines, indent + 1, file) + "\n"

def exit_command(line):
    status = line.split(" ")[1]
    return "sys.exit(" + status + ")"

def read_command(line):
    name = line.split(" ")[1]
    return name + " = " + "input()"

def test(line):
    string = ""
    beforeOp = False
    quotes = False
    last = False
    for i, arg in enumerate(line):
        if beforeOp:
            beforeOp = False
            continue

        if (i + 1) < len(line):       
            if line[i + 1].startswith("$"):
                value = line[i + 1].replace("$", "").strip()
            else:
                value = "\'" + line[i + 1].strip() + "\'"

        if (i - 1) >= 0:
            if line[i - 1].startswith("$"):
                valuePrev = line[i - 1].replace("$", "").strip()
            else:
                valuePrev = "\'" + line[i - 1].strip() + "\'"

        if arg == "!":
            string += "not "
        elif arg == "-a":
            string += "and "
        elif arg == "-o":
            string += "or "
        elif arg == "-n":
            string += "len(" + value + ") > 0"
            beforeOp = True
        elif arg == "-z":
            string += "len()" + value + ") != 0"
            beforeOp = True
        elif arg == "=" or arg == "-eq":
            string += "== "
        elif arg == "!=" or arg == "-ne":
            string += "!= "
        elif arg == "-ge":
            string += ">= "
        elif arg == "-le":
            string += "<= "
        elif arg == "-gt":
            string += "> "
        elif arg == "-lt":
            string += "< "   
        elif arg == "-nt":
            string = string.split()
            string.pop()
            string = " ".join(string)
            string += "os.path.getmtime(" + valuePrev + ") > os.path.getmtime(" + value + ") "
            beforeOp = True
        elif arg == "-ot":
            string = string.split()
            string.pop()
            string = " ".join(string)
            string += "(os.path.getmtime(" + valuePrev + ") < os.path.getmtime(" + value + ")) "
            beforeOp = True
        elif arg == "-b":
            string += "(os.path.exists(" + value + ") and stat.S_ISBLK(os.stat(" + value + ").st_mode)) "
            beforeOp = True
        elif arg == "-c":
            string += "(os.path.exists(" + value + ") and stat.S_ISCHR(os.stat(" + value + ").st_mode)) "
            beforeOp = True
        elif arg == "-d":
            string += "(os.path.exists(" + value + ") and os.path.isdir(" + value + ")) "
            beforeOp = True
        elif arg == "-e":
            string += "os.path.exists(" + value + ") "
            beforeOp = True
        elif arg == "-f":
            string += "(os.path.exists(" + value + ") and os.path.isfile(" + value + ")) "
            beforeOp = True
        elif arg == "-g":
            string += "(os.path.exists(" + value + ") and bool(stat.S_ISBLK(os.stat(" + value + ").st_mode & stat.S_ISGID))) "
            beforeOp = True
        elif arg == "-h":
            string += "(os.path.exists(" + value + ") and os.path.islink(" + value + ")) "
            beforeOp = True
        elif arg == "-k":
            string += "(os.path.exists(" + value + ") and bool(os.stat(" + value + ").st_mode & stat.S_ISVTX)) "
            beforeOp = True
        elif arg == "-r":
            string += "(os.path.exists(" + value + ") and os.access(" + value + ", os.R_OK)) "
            beforeOp = True
        elif arg == "-s":
            string += "(os.path.exists(" + value + ") and (os.path.getsize(" + value + ") > 0)) "
            beforeOp = True
        elif arg == "-x":
            string += "(os.path.exists(" + value + ") and os.access(" + value + ", os.X_OK)) "
            beforeOp = True
        elif arg == "-w":
            string += "(os.path.exists(" + value + ") and os.access(" + value + ", os.W_OK)) "
            beforeOp = True
        elif arg == "-L":
            string += "(os.path.exists(" + value + ") and os.access(" + value + ", os.R_OK)) "
            beforeOp = True
        elif arg.startswith("$"):
            if (i + 1) < len(line):
                if value in "'-le'-gt'-ge'-lt'":
                    string += "int(" + arg.replace("$", "").strip() + ") "
                else:
                    string += arg.replace("$", "").strip() + " "
            elif (i - 1) >= 0:
                if valuePrev in "'-le'-gt'-ge'-lt'":
                    string += "int(" + arg.replace("$", "").strip() + ") "
                else:
                    string += arg.replace("$", "").strip() + " "
        else:
            if arg.startswith("\'"):
                if not arg.endswith("\'"):
                    quotes = True
                    string += "\'"
                arg = re.sub("\'", "", arg)
            elif arg.startswith("\""):
                if not arg.endswith("\""):
                    string += "\'"
                    quotes = True
                arg = re.sub("\"", "", arg)
                if arg.startswith("$"):
                    arg = arg.replace("$", "").strip()
                    string += arg.strip() + " "
                    continue
            elif arg.endswith("\'"):
                arg = re.sub("\'", "", arg)
                quotes = False
                last = True
            elif arg.endswith("\""):
                arg = re.sub("\"", "", arg)
                quotes = False
                last = True

            if quotes:
                string += arg.strip() + " "
            else:
                if last:
                    string += arg.strip() + "\' "
                    last = False
                else:
                    string += "\'" + arg.strip() + "\' "
    
    return string


def if_command(line, file, indent):
    string = "if "
    string += test(line.split(" ")[2:]).strip() + ":\n"

    spaces = " " * (4 * indent)

    for lines in file:
        if lines.strip() == "fi":
            return string
        elif lines.strip() == "then":
            continue
        elif lines.strip().startswith("elif "):
            string += elif_command(lines, file, indent)
            return string
        elif lines.strip().startswith("else"):
            string += else_command(lines, file, indent)
            return string
        string += spaces + check(lines, indent + 1, file) + "\n"

def elif_command(line, file, indent):
    spaces = " " * (4 * (indent - 1))

    string = spaces + line.strip().split(" ")[0].strip() + " "

    string += test(line.strip().split(" ")[2:]).strip() + ":\n"

    spaces = " " * (4 * indent)

    for lines in file:
        if lines.strip() == "fi":
            return string
        elif lines.strip() == "then":
            continue
        elif lines.strip().startswith("elif "):
            string += elif_command(lines, file, indent)
            return string
        elif lines.strip().startswith("else"):
            string += else_command(lines, file, indent)
            return string
        string += spaces + check(lines, indent + 1, file) + "\n"
    
def else_command(line, file, indent):
    spaces = " " * (4 * (indent - 1))
    string = spaces + "else:\n"

    spaces = " " * (4 * indent)
    for lines in file:
        if lines.strip() == "fi":
            return string
        string += spaces + check(lines, indent + 1, file) + "\n"

def while_command(line, file, indent):
    string = "while "
    string += test(line.split(" ")[2:]).strip() + ":\n"

    spaces = " " * (4 * indent)

    for lines in file:
        if lines.strip() == "done":
            return string
        elif lines.strip() == "do":
            continue
        string += spaces + check(lines, indent + 1, file) + "\n"
        


def main():
    print("#!/usr/bin/python3 -u")

    file = open(sys.argv[1])
    
    importsl = imports(file)

    if importsl:
        for line in importsl:
            print(f"{line}")

    print()
    file.seek(0)
    for line in file:
        print(check(line, 1, file))



if __name__ == '__main__':
    main()