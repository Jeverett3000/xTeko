import sys
import traceback

from browser import document as doc
from browser import window, alert, console

_credits = """    Thanks to CWI, CNRI, BeOpen.com, Zope Corporation and a cast of thousands
    for supporting Python development.  See www.python.org for more information."""

_copyright = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All Rights Reserved.

Copyright (c) 2001-2013 Python Software Foundation.
All Rights Reserved.

Copyright (c) 2000 BeOpen.com.
All Rights Reserved.

Copyright (c) 1995-2001 Corporation for National Research Initiatives.
All Rights Reserved.

Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam.
All Rights Reserved."""

_license = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. Redistributions in binary
form must reproduce the above copyright notice, this list of conditions and
the following disclaimer in the documentation and/or other materials provided
with the distribution.
Neither the name of the <ORGANIZATION> nor the names of its contributors may
be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

CODE_ELT = doc['code']

def credits():
    print(_credits)
credits.__repr__ = lambda:_credits

def copyright():
    print(_copyright)
copyright.__repr__ = lambda:_copyright

def license():
    print(_license)
license.__repr__ = lambda:_license

class Trace:
    def __init__(self):
        self.buf = ""

    def write(self, data):
        self.buf += str(data)

    def format(self):
        """Remove calls to function in this script from the traceback."""
        lines = self.buf.split("\n")
        stripped = [lines[0]]
        for i in range(1, len(lines), 2):
            if __file__ in lines[i]:
                continue
            stripped += lines[i: i+2]
        return "\n".join(stripped)

def print_tb():
    trace = Trace()
    traceback.print_exc(file=trace)
    CODE_ELT.value += trace.format()

OUT_BUFFER = ''

def write(data):
    global OUT_BUFFER
    OUT_BUFFER += str(data)

def flush():
    global CODE_ELT, OUT_BUFFER
    CODE_ELT.value += OUT_BUFFER
    OUT_BUFFER = ''

sys.stdout.write = sys.stderr.write = write
sys.stdout.__len__ = sys.stderr.__len__ = lambda: len(OUT_BUFFER)

history = []
current = 0
_status = "main"  # or "block" if typing inside a block

# execution namespace
editor_ns = {
    'credits': credits,
    'copyright': copyright,
    'license': license,
    '__name__': '__main__'
}

def get_col(area):
    # returns the column num of cursor
    sel = doc['code'].selectionStart
    lines = doc['code'].value.split('\n')
    for line in lines[:-1]:
        sel -= len(line) + 1
    return sel

def run_code():
    global _status, current
    src = doc['code'].value

    if _status == "main":
        currentLine = src[src.rfind('>>>') + 4:]
    elif _status == "3string":
        currentLine = src[src.rfind('>>>') + 4:]
        currentLine = currentLine.replace('\n... ', '\n')
    else:
        currentLine = src[src.rfind('...') + 4:]

    if _status == 'main' and not currentLine.strip():
        doc['code'].value += '\n>>> '
        return doc['code'].value

    doc['code'].value += '\n'
    history.append(currentLine)
    current = len(history)

    if _status in ["main", "3string"]:
        try:
            _ = editor_ns['_'] = eval(currentLine, editor_ns)
            flush()
            if _ is not None:
                write(repr(_)+'\n')
            flush()
            doc['code'].value += '>>> '
            _status = "main"
        except IndentationError:
            doc['code'].value += '... '
            _status = "block"
        except SyntaxError as msg:
            if str(msg) == 'invalid syntax : triple string end not found' or \
                str(msg).startswith('Unbalanced bracket'):
                doc['code'].value += '... '
                _status = "3string"
            elif str(msg) == 'eval() argument must be an expression':
                try:
                    exec(currentLine, editor_ns)
                except:
                    print_tb()
                flush()
                doc['code'].value += '>>> '
                _status = "main"
            elif str(msg) == 'decorator expects function':
                doc['code'].value += '... '
                _status = "block"
            else:
                info, filename, lineno, offset, line = msg.args
                print(f"  File <stdin>, line {lineno}")
                print(f"    {line}")
                print("    " + offset * " " + "^")
                print("SyntaxError:", info)
                flush()
                doc['code'].value += '>>> '
                _status = "main"
        except:
            # the full traceback includes the call to eval(); to
            # remove it, it is stored in a buffer and the 2nd and 3rd
            # lines are removed
            print_tb()
            doc['code'].value += '>>> '
            _status = "main"
    elif currentLine == "":  # end of block
        block = src[src.rfind('>>>') + 4:].splitlines()
        block = [block[0]] + [b[4:] for b in block[1:]]
        block_src = '\n'.join(block)
        # status must be set before executing code in globals()
        _status = "main"
        try:
            _ = exec(block_src, editor_ns)
            if _ is not None:
                print(repr(_))
        except:
            print_tb()
        flush()
        doc['code'].value += '>>> '
    else:
        doc['code'].value += '... '

    return doc['code'].value

window.run_code = run_code

v = sys.implementation.version
doc['code'].value = "Brython %s.%s.%s on %s %s\n>>> " % (
    v[0], v[1], v[2], window.navigator.appName, window.navigator.appVersion)

window.notify('pythonDidInit')