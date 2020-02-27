# -*- coding: utf-8 -*-
import os
from collections import OrderedDict

class xyz(OrderedDict):
    """
    Container for mineral composition data. 
    """
    pass

class site_fractions(OrderedDict):
    """
    Container to hold site fraction info.

    """
    def __init__(self):
        self._data_title=None
        pass

    def add_data(self, line):
        """
        Adds data from a provided tokenised line of data. 

        We expect data formatted like the following:

            g          xMgX      xFeX      xCaX      xAlY     xFe3Y
                    0.13698   0.82757   0.03545   0.98451   0.01549
            bi        xMgM3     xFeM3    xFe3M3     xTiM3     xAlM3    xMgM12    xFeM12      xSiT      xAlT      xOHV       xOV
                    0.23132   0.50716   0.05416   0.09110   0.11627   0.47293   0.52707   0.41479   0.58521   0.90890   0.09110
            mu          xKA      xNaA      xCaA    xMgM2A    xFeM2A    xAlM2A    xAlM2B   xFe3M2B     xSiT1     xAlT1
                    0.76707   0.22980   0.00313   0.05172   0.04523   0.90305   0.99381   0.00619   0.54691   0.45309
            pa          xKA      xNaA      xCaA    xMgM2A    xFeM2A    xAlM2A    xAlM2B   xFe3M2B     xSiT1     xAlT1
                    0.06836   0.91840   0.01324   0.00170   0.00149   0.99681   0.99881   0.00119   0.49498   0.50502

        This method should be provided with the above data, one split line per call. The order 
        the provided lines must follow the order of the data to ensure correct parsing. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """

        splitline = line
        if self._data_title == None:
            self._data_title = splitline[0]
            # grab first token for dictionary key
            currentdict = self[self._data_title] = OrderedDict()
            # populate keys for sub-dictionary
            for token in splitline[1:]:
                currentdict[token] = None
        else:
            currentdict = self[self._data_title]
            for key,value in zip(currentdict.keys(),splitline):
                currentdict[key] = value
            self._data_title = None
    
    def _generate_table_rows(self):
        rows = []
        for key,item in self.items():
            row = [key,] + list(item.keys())
            rows.append(row)
            rows.append(["",]+list(item.values()))
        return rows

    def __repr__(self):
        """
        This should a user friend representation.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
    
    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        rows = self._generate_table_rows()
        from tabulate import tabulate
        return tabulate(rows,tablefmt="plain")

class _tabled_data(OrderedDict):
    """
    Container class to hold data derived of table layout.

    Params
    ------
    header: list
        The table header info.

    """
    def __init__(self, header):
        self.header = []
        for item in header:
            self.header.append(item.strip())

    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        raise RuntimeError("Child must define.")
    
    def _generate_table_rows(self):
        rows = [ ["",]+self.header, ]
        for key,item in self.items():
            row = [key,] + list(item.values())
            rows.append(row)
        return rows

    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
 
    def __repr__(self):
        """
        This should a user friend representation.
        """
        return self.__str__()
    

class thermodynamic_properties(_tabled_data):
    """
    Container class for thermodynamic properties parsed
    from tc-ic file. 
    """
    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        if len(line) != len(self.header)+1:
            raise RuntimeError("Error parsing thermodynamic data.\nExpected property count ({}) is different from that encountered ({}) for phase '{}'.".format(len(self.header),len(line)-1,line[0]))
        phase_dict = self[line[0]] = OrderedDict()
        for key,value in zip(self.header,line[1:]):
            phase_dict[key] = value

class rbi(_tabled_data):
    """
    Simple container class to hold rbi info.

    Params
    ------
    oxides: list
        list of oxides. Ie, the rbi columns.

    """
    def __init__(self, oxides):
        if isinstance(oxides, str):
            oxides = oxides.split()
        super().__init__(header=oxides)
        self.oxides = self.header

    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        self.add_phase(phase=line[0],mode=line[1],oxides=line[2:])

    def add_phase(self, phase, mode, oxides):
        """
        Add a phase to the rbi table. 

        Params
        ------
        phase:  str
            Name of phase to add. 
        mode: str, float
            Mode/proportion of phase.
        oxides: list
            Proportion of each oxide for phase. 
        """
        # create a dictionary for phase. 
        phase = phase.strip()
        self[phase] = OrderedDict()
        self[phase]["mode"] = mode
        if isinstance(oxides, str):
            oxides = oxides.split()
        if len(self.oxides) != len(oxides):
            raise RuntimeError("Error parsing 'rbi' data.\nExpected oxide count ({}) is different from that encountered ({}) for phase '{}'.".format(len(self.oxides),len(oxides),phase))
        for item in zip(self.oxides,oxides):
            self[phase][item[0]]=item[1]
    
    def _generate_table_rows(self):
        rows = [ ["",""]+self.oxides, ]
        for key,item in self.items():
            row = [key,] + list(item.values())
            rows.append(row)
        return rows

    def __repr__(self):
        """
        This should a user friend representation.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
    
    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        rows = self._generate_table_rows()
        for row in rows:
            row.insert(0, "rbi")
        from tabulate import tabulate
        return tabulate(rows,tablefmt="plain")

    def copy(self):
        """
        Returns a copy of current rbi object
        """
        cpy = rbi(self.oxides)        
        for key,val in self.items():
            cpy[key]=val.copy()
        return cpy


class Context(object):
    """
    The class records a context for a `thermocalc` computation.
    Multiple concurrent running contexts are allowed.

    The default behaviour is for the context to leverage the standard 
    `thermocalc` input files to for model setup. The user may optionally
    also start with an empty context and construct their model from the 
    ground up.

    The `thermocalc` executable must be available somewhere on the user 
    system. To use the executable, the the script will consider, in order 
    of preference:

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
    scripts_dir: str
        Path to find thermocalc files (in particular `tc-prefs.txt`).
        Defaults to current directory, which is usually the directory where
        Python was launched from. Set to `None` to obtain an empty context. 
    tc_executable: str
        Thermocalc executable. Check class descriptor for further information.
    temp_dir: str
        Temporary location used for the `thermocalc` execution. If not specified,
        a standard system location is used. 
    """
    def __init__(self, scripts_dir=os.getcwd(), tc_executable=None, temp_dir=None):
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
        self.scripts_dir = scripts_dir
        def randomword():
            import random, string
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(6))
        self._id = randomword()
        self.reload()


        if not temp_dir:
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), 'TC_'+self._id)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.temp_dir = temp_dir

    def reload(self):
        """
        Reloads data from working directory.
        """
        # create some defaults
        self.prefs = OrderedDict()
        self.prefs["calcmode"] = 1
        self.prefs["scriptfile"] = self._id
        self.prefs["dataset"] = None
        # create an ordered dictionary to record key/value pairs
        self.script = OrderedDict()
        self.script["axfile"] = None
        self.script["autoexit"] = "yes"

        # load from existing inputs if required
        if self.scripts_dir:
            # find tc-prefs.txt        
            tc_prefs = os.path.join(self.scripts_dir,'tc-prefs.txt')
            if not os.path.isfile(tc_prefs):
                raise RuntimeError("Unable to find 'tc-prefs.txt' in '{}'".format(self.scripts_dir))
            # read tc-prefs
            with open(tc_prefs,'r') as fp:
                while True:
                    line = fp.readline()
                    if not line: break
                    line = line.split("%", 1)[0]
                    splitline = line.split()
                    # print(splitline)
                    if len(splitline)>1:
                        self.prefs[splitline[0]] = splitline[1]
            if 'scriptfile' not in self.prefs:
                raise RuntimeError("'scriptfile' does not appear to be specified in 'tc-prefs.txt' file.")

            # find dataset 
            ds = 'tc-ds' + self.prefs['dataset'] + '.txt'
            tc_ds = os.path.join(self.scripts_dir,ds)
            if not os.path.isfile(tc_ds):
                raise RuntimeError("Unable to find dataset file '{}' in '{}'".format(ds,self.scripts_dir))

            # find scriptfile 
            sf = 'tc-' + self.prefs['scriptfile'] + '.txt'
            tc_sf = os.path.join(self.scripts_dir,sf)
            if not os.path.isfile(tc_sf):
                raise RuntimeError("Unable to find scriptfile '{}' in '{}'".format(sf,self.scripts_dir))
            # read script file
            # keep track of repeated keys to handle differently
            from collections import defaultdict
            keycount = defaultdict(lambda: 0)
            with open(tc_sf,'r') as fp:
                while True:
                    line = fp.readline()
                    if not line: break
                    # get rid of everything after '%'
                    line = line.split("%", 1)[0]
                    splitline = line.split()
                    if len(splitline)>0:
                        if splitline[0] == '*':                # don't read anything past here
                            break
                        key = splitline[0]
                        value = splitline[1:]
                        # now need to decide how to enter into dictionary.
                        # treat "xyzguess" as dictionary
                        if key=="xyzguess":
                            if "xyzguess" not in self.script.keys():
                                self.script["xyzguess"] = xyz()
                            self.script["xyzguess"][value[0]] = value[1:]
                        elif key=="rbi":
                            if "rbi" not in self.script:
                                # create `rbi` object and provide `value` for oxide columns
                                self.script["rbi"] = rbi(value)
                            else:
                                self.script["rbi"].add_data(value)
                        else:
                            val_count = len(value)
                            if val_count == 0:                   # if no values, just set to None
                                value = None
                            else:
                                value = " ".join(value)
                                if value == 'ask':
                                    raise RuntimeError("'ask' is not supported setting from Python interface.")
                            # first check the number of times this key has been encountered
                            keycount[key]+=1                       # increment key count
                            if   keycount[key] == 1:               # if only encountered once, simply create direct pair
                                self.script[key] = value
                            if keycount[key] == 2:                 # this is the second time we've encountered this key,
                                rows = list()                      # so create a list store the rows,
                                rows.append(self.script[key])      # and append previously encountered value as first item in row list.
                                self.script[key] = rows            # now replace that previous value with the rows list (which contains it). 
                                                                   # note that the new value is entered in the following block.
                            if keycount[key] > 1:
                                self.script[key].append(value)     # append value to rows list of values
            self.check_config()


    def check_config(self):
        """
        This method performs sanity checks on your current configuration. 

        It will return nothing if it does not detect any issues, and will 
        raise an exception otherwise.  
        """
        if 'dataset' not in self.prefs:
            raise RuntimeError("'dataset' does not appear to be specified in 'tc-prefs.txt' file.")
        if 'calcmode' not in self.prefs:
            raise RuntimeError("'calcmode' does not appear to be specified in 'tc-prefs.txt' file.")
        if int(self.prefs['calcmode']) != 1:
            raise RuntimeError("Python wrappers currently only support 'calcmode' 1.")

        if "axfile" not in self.script:
            raise RuntimeError("Your script must specify an 'axfile'.")
        if self.script["axfile"] == None:
            raise RuntimeError("Your script must specify a valid 'axfile'.")


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
            if key=="rbi":
                print("\n{} :".format(key))
                print(repr(value),"\n")
            elif isinstance(value, list):
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
                if isinstance(value, list):
                    for item in value:
                        fp.write("{} {}\n".format(key,self._get_string(item)))
                elif isinstance(value,rbi):
                    fp.write(str(value)+"\n")
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

    def execute(self, print_output=False, copy_new_files=False, datasets_dir=None):
        """
        Execute thermocalc for the current configuration, and parse generated
        outputs. Recorded outputs include execution standard output (`stdout`),
        standard error (`stderr`), `tc-log.txt` and `tc-ic.txt`.

        Files generated as a result of the execution are as default not copied
        back to the context location.

        All results are returned as a dictionary. Refer to the list of dictionary 
        keys to get a list of returned data:

        >>> results = mycontext.execute()
        >>> results.print_keys()
        P
        T
        bulk_composition
        modes
        output_stderr
        output_stdout
        output_tc_ic
        output_tc_log
        phases
        rbi
        site_fractions
        thermodynamic_properties
        xyz

        Results objects prepended with `output_` provide the raw text from the 
        corresponding output. Note also that dictionary entries can be accessed 
        directly as attributes or via the usual dictionary methods:

        >>> results.P
        11.0
        >>> results["P"]
        11.0


        Params
        ------
        print_output: bool
            If set to `True`, prints `thermocalc` output to screen. 
        copy_new_files: bool
            Files which are generated resultant of the `thermocalc` execution are by 
            default not copied back to the context location. Enable this flag to have
            generated files copied. 

        datasets_dir: string
            Location of required datasets. It is usually not necessary to specify this
            as the files will be obtained from the `scripts_dir` or from `tawnycalc` 
            itself. 

        Returns
        -------
        results: dict
            Dictionary containing execution results.
        """
        self.check_config()

        if copy_new_files:
            import warnings
            warnings.warn("'copy_new_files' not yet implemented.\nGenerated files may be found in {}".format(self.temp_dir))

        # write prefs file to temp location
        self.save_prefs(os.path.join(self.temp_dir,"tc-prefs.txt"))

        # write script file
        self.save_script(os.path.join(self.temp_dir,"tc-"+self.prefs['scriptfile']+".txt"))

        # if not provided in this call
        if not datasets_dir:
            # set to scripts dir provided when context created.
            datasets_dir = self.scripts_dir
        # if still nothing
        if not datasets_dir:
            # use python module files
            datasets_dir = os.path.join(__file__[:-7],"datasets")
        
        # now copy dataset file
        from shutil import copyfile
        dataset = "tc-ds{}.txt".format(self.prefs['dataset'])
        copyfile(os.path.join(datasets_dir,dataset), os.path.join(self.temp_dir,dataset))

        # now copy axfile
        axfile = "tc-{}.txt".format(self.script['axfile'])
        copyfile(os.path.join(datasets_dir,axfile), os.path.join(self.temp_dir,axfile))

        from subprocess import Popen, PIPE, STDOUT
        p = Popen(self.exec,cwd=self.temp_dir, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        if print_output:
            for line in iter(p.stdout.readline, b''):
                print('{}'.format(line.decode("cp437").rstrip()))
        std_data = p.communicate(input=b'n\n')


        # create a special dictionary which allows keys/vals to be accessed
        # via object attributes
        class ResultsDict(dict):
            def __init__(self, *args, **kwargs):
                super(ResultsDict, self).__init__(*args, **kwargs)
                self.__dict__ = self
            def print_keys(self):
                for key in sorted(self.keys()):
                    print(key)

        results = ResultsDict()
        results["output_stdout"] = std_data[0].decode("cp437") # record standard output
        results["output_stderr"] = std_data[1].decode("cp437") # record standard error

        # try parse `tc-log.txt`
        try:
            with open(os.path.join(self.temp_dir,"tc-log.txt"),'r',encoding="cp437") as fp:
                while True:
                    line = fp.readline()
                    if not line: break
                    splitline = line.split()
                    if len(splitline)>0:
                        key = splitline[0]
                        value = splitline[1:]
                        if   key=="THERMOCALC":
                            # let's check version
                            try:
                                # grab first line
                                version = splitline[1]
                                if version != "3.50":
                                    import warnings
                                    warnings.warn("`tawnycalc` only tested against `thermocalc` version 3.50. Detected version is {}.".format(version))
                            except:
                                import warnings
                                warnings.warn("Unable to detect `thermocalc` version. Note that `tawnycalc` only tested against `thermocalc` version 3.50.")
                        elif key=="rbi":
                            if "rbi" not in results.keys():
                                # # grab copy of existing rbi if available and oxides
                                # if ("rbi" in self.script.keys()) and (self.script["rbi"].oxides == value):
                                #     results["rbi"] = self.script["rbi"].copy()
                                # else:
                                results["rbi"] = rbi(value)
                            else:
                                results["rbi"].add_data(value)
                        elif key=="phases:":
                            results["phases"] = value
                        elif key=="ptguess":
                            results["P"] = value[0]
                            results["T"] = value[1]
                        elif key=="xyzguess":
                            if "xyz" not in results.keys():
                                results["xyz"] = xyz()
                            results["xyz"][value[0]] = float(value[1])
                        elif key=="mode":
                            modes = OrderedDict()
                            mode_keys   = value                  # keys from first line
                            mode_values = fp.readline().split()  # values from next                            
                            for mode_key,mode_value in zip(mode_keys,mode_values):
                                modes[mode_key] = float(mode_value)
                            results["modes"] = modes

        except:
            raise
            import warnings
            warnings.warn("Error trying to parse 'tc-log.txt'.")
        # ok, grab entire output for user's convenience 
        with open(os.path.join(self.temp_dir,"tc-log.txt"),'r',encoding="cp437") as fp:
            results["output_tc_log"] = fp.read()

        # try parse `tc-ic.txt`
        filename = "tc-" + self.prefs["scriptfile"] + "-ic.txt"
        try:
            with open(os.path.join(self.temp_dir,filename),'r',encoding="cp437") as fp:
                while True:
                    line = fp.readline()
                    if not line: break

                    line = line.strip()
                    if line=="site fractions":
                        site_fracs = site_fractions()
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            site_fracs.add_data(line.split())
                        results["site_fractions"] = site_fracs

                    if line=="oxide compositions":
                        bulk_composition = OrderedDict()
                        keys = fp.readline().split()    # keys in first line
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            tokens = line.split()
                            if tokens[0] == 'bulk':
                                for key,value in zip(keys,tokens[1:]):
                                    bulk_composition[key] = float(value)
                        results["bulk_composition"] = bulk_composition

                        # now thermo props. 
                        # we assume here that they appear directly after the "oxide composition" section.
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            tokens = line.split()
                            thermo_props = thermodynamic_properties(tokens)
                            while True:
                                line = fp.readline()
                                if not line or (line == "\n"): break
                                thermo_props.add_data(line.split())
                            results["thermodynamic_properties"] = thermo_props
                            break
        except:
            import warnings
            warnings.warn("Error trying to parse '{}'.".format(filename))
        # ok, grab entire output for user's convenience 
        with open(os.path.join(self.temp_dir,filename),'r',encoding="cp437") as fp:
            results["output_tc_ic"] = fp.read()

        return results

