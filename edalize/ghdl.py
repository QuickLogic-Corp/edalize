import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Ghdl(Edatool):

    tool_options = {'lists' : {'analyze_options' : 'String',
                               'run_options'     : 'String'}}
    argtypes = ['vlogparam']

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files()
        # ghdl does not support mixing incompatible versions
        # specifying 93c as std should allow 87 syntax
        # 2008 can't be combined so try to parse everthing with 08 std
        has87 = has93 = has08 = False
        for f in src_files:
            if f.file_type == "vhdlSource-87":
                has87 = True
            elif f.file_type == "vhdlSource-93":
                has93 = True
            elif f.file_type == "vhdlSource-2008":
                has08 = True
        stdarg = []
        if has08:
            if has87 or has93:
                logger.warning("ghdl can't mix vhdlSource-2008 with other standard version\n"+
                               "Trying with treating all as vhdlSource-2008"
                )
            stdarg = ['--std=08']
        elif has87 and has93:
            stdarg = ['--std=93c']
        elif has87:
            stdarg = ['--std=87']
        elif has93:
            stdarg = ['--std=93']

        analyze_options = self.tool_options.get('analyze_options', '')

        run_options = self.tool_options.get('run_options', [])

        makefile = open(os.path.join(self.work_root, 'Makefile'), 'w')
        makefile.write("""#Auto generated by Edalize
STD = {std}
TOPLEVEL = {toplevel}
ANALYZE_OPTIONS = {analyze_options}
RUN_OPTIONS = {run_options}

all: analyze

run:
	ghdl --elab-run $(ANALYZE_OPTIONS) $(STD) $(TOPLEVEL) $(RUN_OPTIONS) $(EXTRA_OPTIONS)
analyze:
""".format(std=' '.join(stdarg),
           toplevel=self.toplevel,
           analyze_options=' '.join(analyze_options),
           run_options=' '.join(run_options)))

        _vhdltypes = ("vhdlSource", "vhdlSource-87", "vhdlSource-93", "vhdlSource-2008")
        for f in src_files:
            if f.file_type in _vhdltypes:
                lib = ""
                if f.logical_name:
                    lib = ' --work='+f.logical_name
                makefile.write("\tghdl -a $(STD) $(ANALYZE_OPTIONS){lib} {file}\n".format(lib=lib, file=f.name))
            elif f.file_type in ["user"]:
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(f.name, f.file_type))
        makefile.close()

    def run_main(self):
        cmd = 'make'
        args = ['run']

        if self.vlogparam:
            extra_options='EXTRA_OPTIONS='
            for k,v in self.vlogparam.items():
                extra_options += ' -g{}={}'.format(k,self._param_value_str(v,'"'))
            args.append(extra_options)
        self._run_tool(cmd, args)
