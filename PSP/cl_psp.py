
import os
import sys

from Context import PSPCLContext
from PSPCompiler import Compiler

# Move this to a class like JPS?

def PSPCompile(*args):
    pspfilename = args[0]
    fil, ext = os.path.splitext(os.path.basename(pspfilename))
    classname = fil + '_' + ext
    pythonfilename = classname + '.py'
    context = PSPCLContext(pspfilename)
    context.setClassName(classname)
    context.setPythonFileName(pythonfilename)
    context.setPythonFileEncoding('utf-8')
    clc = Compiler(context)
    clc.compile()


if __name__ == '__main__':
    PSPCompile(sys.argv[1])
