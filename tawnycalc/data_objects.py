from collections import OrderedDict

class Printable_OrderedDict(OrderedDict):
    """
    This class simply redefines `__repr__` method so that
    objects can be printed nicely. 
    """
    def __repr__(self):
        """
        This should a user friend representation.
        """
        from tabulate import tabulate
        return tabulate(self.items(),tablefmt="plain")
    
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
