from cffi import FFI
import os
import subprocess
import re
import ast
import pycparserext
import pycparser

HERE = os.path.dirname(os.path.realpath(__file__))
BUILDDIR='v4l2_cache'

if not os.path.exists(os.path.join(HERE, BUILDDIR)):
    os.mkdir(os.path.join(HERE, BUILDDIR))
else:
    if not os.path.isdir(os.path.join(HERE, BUILDDIR)):
        print('Can not create directory', os.path.join(HERE, BUILDDIR), ': File exists')
        exit(1)
    print('Clearing build cache directory', os.path.join(HERE, BUILDDIR))
    for p in os.scandir(os.path.join(HERE, BUILDDIR)):
        print('removing ', os.path.join(HERE, BUILDDIR, p.name))
        os.remove(os.path.join(HERE, BUILDDIR, p.name))

def generate_cdef():
    """Generate the cdef output file"""
    include_v4l2_path='/usr/include/linux'
    #include_v4l2_path='.'
    #out_file = path.join(HERE, 'v4l2', 'videodev2.cdef.h')
    #out_packed_file = path.join(HERE, 'v4l2', 'videodev2.cdef_packed.h')
    #header = path.join(include_v4l2_path, 'videodev2.h')
    #header_parsed = path.join(HERE, 'v4l2', 'videodev2.h')
    #enum_file = path.join(HERE, 'v4l2', 'v4l2_enums.py')
    out_file = os.path.join(HERE, BUILDDIR, 'videodev2.cdef.h')
    out_packed_file = os.path.join(HERE, BUILDDIR,  'videodev2.cdef_packed.h')
    header = os.path.join(include_v4l2_path, 'videodev2.h')
    header_parsed = os.path.join(HERE, BUILDDIR, 'videodev2.h')
    enum_file = os.path.join(HERE, 'v4l2enums.py')

    out=open(header_parsed, 'w+')
    cpp_process = subprocess.Popen(
        ['cpp',
         '-P',
         #'-nostdinc',
         '-I', 'fake-include',
         header
        ],
        stdout=out
        )
    cpp_process.wait()
    out.close()

    headerin = open(header_parsed, 'r')
    headersrc = headerin.read()
    from pycparserext.ext_c_parser import GnuCParser
    p = GnuCParser()
    ast=p.parse(headersrc, filename=header_parsed)
    # ast.show()
    headerin.close()
    out=open(out_file, 'w+')
    out_packed=open(out_packed_file, 'w+')
    enums=open(enum_file, 'w+')
    enums.write('import enum\nimport v4l2\n')
    from pycparserext.ext_c_generator import GnuCGenerator
    g=GnuCGenerator()
    i = 0
    for nname, astnode in ast.children():
        outthis = out
        if type(astnode) == pycparser.c_ast.Decl:
            #print('node', i)
            #print(g.visit(astnode)+'\n')
            for spec in astnode.funcspec:
                if type(spec) == pycparserext.ext_c_parser.AttributeSpecifier:
                    for att in spec.exprlist.exprs:
                        if att.name == 'packed':
                            outthis = out_packed
            if type(astnode.type) == pycparser.c_ast.Enum:
                enumnode = astnode.type
                enums.write('class ' + enumnode.name +'(enum.IntEnum):\n')
                for el in enumnode.values.enumerators:
                    enums.write('    ' + el.name + ' = v4l2.' + el.name + '\n')
                enums.write('\n')
            if type(astnode.type) != pycparserext.ext_c_parser.FuncDeclExt:
                #print(i, type(astnode.type))
                outthis.write(g.generic_visit(astnode)+';\n')
            else:
                # for parsing ioctl(...) decalaration
                outthis.write(g.visit(astnode)+';\n')
        else:
            outthis.write(g.visit(astnode)+';\n')
        #print('node', i)
        #print(g.generic_visit(astnode)+'\n')
        i+=1
    out.flush()
    out.close()
    out_packed.flush()
    out_packed.close()
    enums.flush()
    enums.close()

    print('generate_cdef: generated\n      ', out_file, ',\n      ', out_packed_file, '\n  and', enum_file, 'from', header)
    return out_file, out_packed_file

def pythonize_expr(expr, exprs):
    res = expr.replace('||', 'or').replace('&&', 'and')
    res = res.replace('dir', 'dir_').replace('type', 'type_')
    res = res.replace('sizeof', 'ffi.sizeof')
    for e,r in exprs:
        res = e.sub(r, res)

    return res

def generate_py():
    """Generate the python output file"""
    from _v4l2 import ffi
    include_v4l2_path='/usr/include/linux'
    #include_v4l2_path='.'
    #out_def_file = path.join(HERE, 'v4l2', 'videodev2.defines.h')
    #header = path.join(include_v4l2_path, 'videodev2.h')
    #out_file = path.join(HERE, 'v4l2.py')
    out_def_file = os.path.join(HERE, BUILDDIR, 'videodev2.defines.h')
    header = os.path.join(include_v4l2_path, 'videodev2.h')
    out_file = os.path.join(HERE, 'v4l2.py')

    outdef=open(out_def_file, 'w+')
    cpp_process = subprocess.Popen(
        ['cpp',
         '-dD',
         header
        ],
        stdout=subprocess.PIPE
        )
    grep_process = subprocess.Popen(
        ['grep',
         '-E', '^#define (V4L2|VIDIOC|v4l2|VIDEO|_IO)'
         ],
        stdin=cpp_process.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines = True
        )
    stdout, stderr = grep_process.communicate()
    if (stderr):
        for line in stderr.split('\n'):
            print(line)
    outdef.write(stdout)
    outdef.flush()
    outdef.close()
    print('generated', out_def_file, 'from', header)
    out=open(out_file, 'w+')
    out.write('from _v4l2 import ffi\nfrom _v4l2.lib import *\n')
    notparsed = []
    casts = re.compile(r"(\(\w+\))(\(\w+\)|\w+)")
    macro = re.compile(r"^(.*)\((.*)\)$")
    exprs=[]
    # should try using \b
    exprs.append((re.compile(r"\b([0-9A-Fa-f][0-9A-Fa-f]*)(?:UL|LL|U|L)(\W|\Z)"), r"\1\2"))
    #exprs.append((re.compile(r"(struct\s\w+)"), r"'\1'"))
    exprs.append((re.compile(r"(_IOWR|_IOW|_IOR)\((.*),(.*),(.*)\)"), r"\1(ord(\2), \3, '\4')"))
    exprs.append((re.compile(r"_IO\((.*),(.*)\)"), r"_IO(ord(\1), \2)"))
    for define in stdout.split('\n'):
        try:
            _, name, value = define.split(' ', maxsplit=2)
        except ValueError:
            print('Error:', define)
            continue
        # casts
        match = casts.finditer(value)
        castvalue=''
        current=0
        for c in match:
            castvalue+=value[current:c.start()]
            t = c.groups()[0][1:-1]
            if (t in ffi.list_types()[0] or t in ffi.list_types()[1] or t in ffi.list_types()[2]):
                ctype = ffi.getctype(t)
                if 'int' in ctype or 'long' in ctype or 'short' in ctype:
                    castvalue+='int(ffi.cast(\''+t+'\','+c.groups()[1]+'))'
                elif 'float' in ctype or 'double' in ctype:
                    castvalue+='float(ffi.cast(\''+t+'\','+c.groups()[1]+'))'
                else:
                    castvalue+='ffi.cast(\''+t+'\','+c.groups()[1]+')'
            else:
                castvalue+=value[c.start():c.end()]
            current = c.end()
        if castvalue:
            castvalue+=value[current:len(value)]
            #print(castvalue)
            value=castvalue
        match = macro.match(name)
        if match:
            #print('Macro', match.group(), match.groups())
            macrodef = pythonize_expr(value, exprs)
            try:
                ast.parse(macrodef)
                out.write('def '+ match.group().replace('dir', 'dir_').replace('type', 'type_') +':\n    return '+ macrodef + '\n')
                continue
            except:
                notparsed.append((name, value))
                continue
        expression = pythonize_expr(value, exprs)
        try:
            ast.parse(expression)
            out.write(name + ' = ' + expression + '\n')
            continue
        except:
            notparsed.append((name, value))
            continue
        notparsed.append((name, value))

    print('not parsed ', len(notparsed))
    if notparsed != []:
        for d in notparsed:
            print(d[0], '-->', d[1])
    cffiwrapstruct = """
def _cstr(x):
    if not isinstance(x, ffi.CData):
        return x

    t = ffi.typeof(x)
    if 'item' not in dir(t) or (t.item.cname != 'char' and t.item.cname != 'unsigned char'):
        return x

    return ffi.string(x).decode('ascii')

class CStructType(object):
    ''' Provides introspection to CFFI ``StructType``s and ``UnionType``s.

    Instances have the following attributes:

    * ``ffi``: The FFI object this struct is pulled from.
    * ``cname``: The C name of the struct.
    * ``ptrname``: The C pointer type signature for this struct.
    * ``fldnames``: A list of fields this struct has.

    Instances of this class are essentially struct/union generators.
    Calling an instance of ``CStructType`` will produce a newly allocated
    struct or union.

    Struct fields can be passed in as positional arguments or keyword
    arguments. ``TypeError`` is raised if positional arguments overlap with
    given keyword arguments.

    Arrays of structs can be created with the ``array`` method.

    The module convenience function ``wrapall`` creates ``CStructType``\ s
    for each struct and union imported from the FFI.

    '''

    def __init__(self, ffi, structtype):
        '''

        * ``ffi``: The FFI object.
        * ``structtype``: a CFFI StructType or a string for the type name
          (wihtout any trailing '*' or '[]').

        '''

        if isinstance(structtype, str):
            structtype = ffi.typeof(structtype)

        self._struct_type = structtype
        self.ffi = ffi

        # Sometimes structtype.name starts with a '$'...?
        self.cname = structtype.cname
        self.ptrname = ffi.getctype(self.cname, '*')
        self.fldnames = structtype.fields

    def __call__(self, *args, **kwargs):
        if self.fldnames is None:
            if args or kwargs:
                raise TypeError('CStructType call with arguments on opaque '
                                'CFFI struct {0}.'.format(self.cname))
            return self.ffi.new(self.ptrname)
        else:
            if len(args) > len(self.fldnames):
                raise TypeError('CStructType got more arguments than struct '
                                'has fields. {0} > {1}'
                                .format(len(args), len(self.fldnames)))
            retval = self.ffi.new(self.ptrname)
            for fld, val in zip(self.fldnames, args):
                if fld in kwargs:
                    raise TypeError('CStructType call got multiple values for '
                                    'field name {0}'.format(fld))
                setattr(retval, fld, val)
            for fld, val in kwargs.items():
                setattr(retval, fld, val)

            return retval
"""
    out.write(cffiwrapstruct)
    for s in ffi.list_types()[1]:
        out.write(s + ' = CStructType(ffi, ffi.typeof(\'struct '+ s + '\'))\n')

    out.flush()
    out.close()
    return out_file

ffibuilder = FFI()

ffibuilder.set_source("_v4l2",
                      """
#include <linux/videodev2.h>
#include <sys/ioctl.h>
                      """,
                      libraries=[])


# read file
cdef_file, cdef_packed_file=generate_cdef()
with open(cdef_file, 'r') as f:
    cdef = f.read()

ffibuilder.cdef(cdef)

with open(cdef_packed_file, 'r') as f:
    cdef_packed = f.read()

ffibuilder.cdef(cdef_packed, packed=True)

def maker():
    ffibuilder.compile(verbose=True)
    #from _v4l2 import ffi
    py_file=generate_py()
    return ffibuilder

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
    from _v4l2 import ffi
    py_file=generate_py()
