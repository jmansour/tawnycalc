# -*- coding: utf-8 -*-
import os
from collections import OrderedDict

class rows_list(list):
    """
    This is just a dummy class so we can differentiate between
    rows and list type entries in our in our script dictionary
    """
    pass

class Context(object):
    """
    The class records a context for a `thermocalc` computation.
    Multiple concurrent running contexts are allowed.

    The context will leverage the standard `thermocalc` input files
    to define the runtime environment, and by default it will obtain
    these files from script launch directory. The user may also 
    specify the script location via the `tc_prefs` parameter. 

    The `thermocalc` executable must also be available. To use the
    executable, the the script will consider, in order of preference:

    1. User provided `tc_executable` parameter to this class.
    2. User set environment variable `THERMOCALC_EXECUTABLE` defining
       the absolute path to the executable. 
    3. Run directly, with executable therefore available in current
       directory or available via the system `PATH`. 

    Note that the execution is performed in a temporary location such
    that all files in the current context location are not modified or
    written over. This location may be specified as a parameter. 

    Params
    ------
    work_dir: str
        Path to find thermocalc files (in particular `tc-prefs.txt`).
        Defaults to current directory. 
    tc_executable: str
        Thermocalc executable. Check class descriptor for further information.
    temp_dir: str
        Temporary location used for the `thermocalc` execution. If not specified,
        a standard system location is used. 
    """
    def __init__(self, work_dir=os.getcwd(), tc_executable=None, temp_dir=None):
        # lets first check that we have an executable
        # the following is borrowed from https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        def which(program):
            def is_exe(fpath):
                return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

            fpath, fname = os.path.split(program)
            if fpath:
                if is_exe(program):
                    return program
            else:
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_file = os.path.join(path, program)
                    if is_exe(exe_file):
                        return exe_file
            return None

        if tc_executable:
            self.exec = which(tc_executable)
            if self.exec is None:
                raise RuntimeError("Parameter specified executable {} does not appear to be valid".format(tc_executable))
        elif "THERMOCALC_EXECUTABLE" in os.environ:
            self.exec = which(os.environ["THERMOCALC_EXECUTABLE"])
            if self.exec is None:
                raise RuntimeError("Environment specified executable {} does not appear to be valid".format(os.environ["THERMOCALC_EXECUTABLE"]))
        else:
            self.exec = which('thermo')
            if self.exec is None:
                raise RuntimeError("Unable to find `thermo` executable. Ensure it is in your path, or set " \
                                   "the `THERMOCALC_EXECUTABLE` environment variable, or the `tc_executable` parameter.")
        self.work_dir = work_dir
        self.reload()

        if not temp_dir:
            import tempfile
            import random, string
            def randomword():
                letters = string.ascii_lowercase
                randstr = ''.join(random.choice(letters) for i in range(6))
                return 'TC_'+randstr
            temp_dir = os.path.join(tempfile.gettempdir(), randomword())
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.temp_dir = temp_dir

    def reload(self):
        """
        Reloads data from working directory.
        """
        # find tc-prefs.txt
        tc_prefs = os.path.join(self.work_dir,'tc-prefs.txt')
        if not os.path.isfile(tc_prefs):
            raise RuntimeError("Unable to find 'tc-prefs.txt' in '{}'".format(work_dir))
        # read tc-prefs
        self.prefs = OrderedDict()
        with open(tc_prefs,'r') as fp:
            line = fp.readline()
            while line:
                line = line.split("%", 1)[0]
                splitline = line.split()
                # print(splitline)
                if len(splitline)>1:
                    self.prefs[splitline[0]] = splitline[1]
                line = fp.readline()
        if 'scriptfile' not in self.prefs:
            raise RuntimeError("'scriptfile' does not appear to be specified in 'tc-prefs.txt' file.")
        if 'dataset' not in self.prefs:
            raise RuntimeError("'dataset' does not appear to be specified in 'tc-prefs.txt' file.")
        if 'calcmode' not in self.prefs:
            raise RuntimeError("'calcmode' does not appear to be specified in 'tc-prefs.txt' file.")
        if self.prefs['calcmode'] != '1':
            raise RuntimeError("Python wrappers currently only support 'calcmode' 1.")

        # find dataset 
        ds = 'tc-ds' + self.prefs['dataset'] + '.txt'
        tc_ds = os.path.join(self.work_dir,ds)
        if not os.path.isfile(tc_ds):
            raise RuntimeError("Unable to find dataset file '{}' in '{}'".format(ds,self.work_dir))

        # find scriptfile 
        sf = 'tc-' + self.prefs['scriptfile'] + '.txt'
        tc_sf = os.path.join(self.work_dir,sf)
        if not os.path.isfile(tc_sf):
            raise RuntimeError("Unable to find scriptfile '{}' in '{}'".format(sf,self.work_dir))
        # read script file
        # create an ordered dictionary to record key/value pairs
        self.script = OrderedDict()
        # keep track of repeated keys to handle differently
        from collections import defaultdict
        keycount = defaultdict(lambda: 0)
        with open(tc_sf,'r') as fp:
            line = fp.readline()
            while line:
                # get rid of everything after '%'
                line = line.split("%", 1)[0]
                splitline = line.split()
                if len(splitline)>0:
                    if splitline[0] == '*':                # don't read anything past here
                        break
                    key = splitline[0]
                    value = splitline[1:]
                    # first let's decide how to process value(s)
                    val_count = len(value)
                    if   val_count == 0:                   # if no values, just set to None
                        value = None
                    elif val_count == 1:                   # if a single value, create direct key/val pair
                        value = value[0]
                        if value == 'ask':
                            raise RuntimeError("'ask' is not currently a supported setting from Python interface.")
                    else:                                  # otherwise, leave as a list
                        pass
                    # now need to decide how to enter into dictionary.
                    # treat "xyzguess" as dictionary
                    if key=="xyzguess":
                        if "xyzguess" not in self.script.keys():
                            self.script["xyzguess"] = OrderedDict()
                        self.script["xyzguess"][value[0]] = value[1:]
                    else:
                        # first check the number of times this key has been encountered
                        keycount[key]+=1                       # increment key count
                        if   keycount[key] == 1:               # if only encountered once, simply create direct pair
                            self.script[key] = value
                        if keycount[key] == 2:                 # this is the second time we've encountered this key,
                            rows = rows_list()                 # so create a list store the rows,
                            rows.append(self.script[key])      # and append previously encountered value as first item in row list.
                            self.script[key] = rows            # now replace that previous value with the rows list (which contains it). 
                        if keycount[key] > 1:
                            self.script[key].append(value)     # append value to rows list of values 
                line = fp.readline()

    def _longest_key(self, dictguy):
        """
        Get length of longest dictionary key
        """
        longest = 0
        for key in dictguy:
            if len(key)>longest:
                longest = len(key)
        return longest

    def _get_string(self, item, just=0):
        """
        Prints item or list of items
        """
        if   isinstance(item,list):
            return " ".join(str(p).ljust(just) for p in item)
        return item

    def print_script(self):
        """
        Prints the current loaded script configuration.
        """
        longest = self._longest_key(self.script)
        for key, value in self.script.items():
            if   isinstance(value, rows_list):
                print("{} :".format(key))
                for item in value:
                    print("    {}".format(self._get_string(item,10)))
            elif isinstance(value, dict):
                print("{} :".format(key))
                longest_inner = self._longest_key(value)
                for valkey,item in value.items():
                    print("    {} : {}".format(valkey.ljust(longest_inner), self._get_string(item,10)))
            else:
                print("{}: {}".format(key.ljust(longest+1),self._get_string(value)))

    def save_script(self, file):
        """
        Saves the current script configuration to a file.

        Params
        ------
        file: str
            Filename for saved file.
        """
        with open(file,'w') as fp:
            longest = self._longest_key(self.script)
            for key, value in self.script.items():
                if isinstance(value, rows_list):
                    for item in value:
                        fp.write("{} {}\n".format(key,self._get_string(item)))
                elif isinstance(value, dict):
                    longest_inner = self._longest_key(value)
                    for valkey,item in value.items():
                        fp.write("{} {} {}\n".format(key,valkey, self._get_string(item,10)))
                else:
                    fp.write("{} {}\n".format(key.ljust(longest+1),self._get_string(value)))

    def print_prefs(self):
        """
        Prints the current loaded preferences configuration.
        """
        longest = self._longest_key(self.prefs)
        for key, value in self.prefs.items():
            print("{}: {}".format(key.ljust(longest+1),self._get_string(value)))

    def save_prefs(self, file):
        """
        Saves the current preferences configuration to a file.

        Params
        ------
        file: str
            Filename for saved file.
        """
        with open(file,'w') as fp:
            longest = self._longest_key(self.prefs)
            for key, value in self.prefs.items():
                fp.write("{} {}\n".format(key.ljust(longest+1),self._get_string(value)))

    def execute(self, copy_new_files=False):
        """
        Execute thermocalc for the current configuration. 

        Files generated as a result of the execution are as default not copied
        back to the context location 

        Params
        ------
        copy_new_files: bool
            Files which are generated resultant of the `thermocalc` execution are by 
            default not copied back to the context location. Enable this flag to have
            generated files copied. 

        Returns
        -------
        Named tuple including:
            stdout: The full standard output from the `thermocalc` simulation.
            stderr: The full standard error from the `thermocalc` simulation.
            phases: List of phases.
            P     : Pressure (kbar).
            T     : Temperature (íC).
            xyz   : Mineral compositions (as a dictionary).
            modes : Mineral modes (as a dictionary).
        """

        if copy_new_files:
            import warnings
            warnings.warn("'copy_new_files' not yet implemented.\nGenerated files may be found in {}".format(self.temp_dir))

        # write prefs file to temp location
        self.save_prefs(os.path.join(self.temp_dir,"tc-prefs.txt"))

        # write script file
        self.save_script(os.path.join(self.temp_dir,"tc-"+self.prefs['scriptfile']+".txt"))

        # now copy dataset file
        from shutil import copyfile
        dataset = "tc-ds{}.txt".format(self.prefs['dataset'])
        copyfile(os.path.join(self.work_dir,dataset), os.path.join(self.temp_dir,dataset))

        # now copy axfile
        axfile = "tc-{}.txt".format(self.script['axfile'])
        copyfile(os.path.join(self.work_dir,axfile), os.path.join(self.temp_dir,axfile))

        from subprocess import Popen, PIPE, STDOUT
        p = Popen(self.exec,cwd=self.temp_dir, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        std_data = p.communicate(input=b'n\n')

        from collections import namedtuple
        Result = namedtuple("Results", ["stdout","stderr", "phases", "P", "T", "xyz", "modes"])
        stdout = std_data[0].decode("cp437") # record standard output
        stderr = std_data[1].decode("cp437") # record standard error

        phases = None
        P = None
        T = None
        xyz = None
        modes = None

        # now let's try and parse output.  
        # put in a 'try' block so that we can fail usefully.
        try:
            splt1 = "##########################################################"
            splt2 = "more phase diagram calculations"
            strguy = stdout.split(splt1)[1].split(splt2)[0].split('\n')          # split on above blocks, then on new line
            phases = strguy[1].split('phases: ')[1]                              # grab phases

            list1 = strguy[3].split()                                            # process P, T, xyz
            list2 = strguy[4].split()
            P = float(list2[0])
            T = float(list2[1])
            xyz = OrderedDict()
            for key,val in zip(list1[2:],list2[2:]):
                xyz[key] = float(val)
            
            list3 = strguy[6].split()                                            # process modes
            list4 = strguy[7].split()
            modes = OrderedDict()
            for key,val in zip(list3[1:],list4):
                modes[key] = float(val)
        except:
            import warnings
            warnings.warn("Error trying to parse output. Please check standard out/error.")

        return Result(stdout,stderr,phases,P,T,xyz,modes)


