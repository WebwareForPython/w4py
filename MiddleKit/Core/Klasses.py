from ModelObject import ModelObject
from Model import Model, ModelError
from Klass import Klass
from Attr import Attr
from MiscUtils import NoDefault
from MiscUtils.DataTable import DataTable
from MiscUtils.DictForArgs import *


class Klasses(dict, ModelObject):
    """Collection of class specifications.

    A Klasses object can read a list of class specifications that are
    stored in a spreadsheet (.csv).
    """


    ## Init ##

    def __init__(self, model):
        dict.__init__(self)
        assert isinstance(model, Model)
        self._model = model
        self._klasses = []
        self._filename = None
        self._name = None
        self._tableHeadings = None
        self.initTypeMap()

    def classNames(self):
        return ['ModelObject', 'Klasses', 'Klass', 'Attr',
            'BasicTypeAttr', 'ObjRefAttr', 'EnumAttr', 'DateTimeAttr']

    def initTypeMap(self):
        """Initialize the type map.

        Initializes self._typeNamesToAttrClassNames which maps MiddleKit type
        names (like int and enum) to the name of the attribute class that would
        implement them. Mapping to class names rather than actual classes is key,
        because in __init__, a different set of attribute classes can be passed in.
        """
        typemap = {}
        names = 'bool int long float string enum date time list ObjRef decimal'
        names = names.split()
        for name in names:
            typemap[name] = name.capitalize() + 'Attr'
        typemap['datetime'] = 'DateTimeAttr'
        self._typeNamesToAttrClassNames = typemap

    def assignClassIds(self, generator):
        if self.setting('UseHashForClassIds', False):
            # This is better because class ids will likely stay the same even as
            # you change your MiddleKit model. For example, class ids across
            # different sandboxes of your application (development, test and
            # production) would match up even as you add and remove classes.
            # However, renaming classes changes the id!
            allIds = set()
            for klass in self._model._allKlassesInOrder:
                klass.setId(allIds)
        else:
            for i, klass in enumerate(self._model._allKlassesInOrder):
                klass.setId(i+1)


    ## Accessing ##

    def model(self):
        return self._model

    def filename(self):
        return self._filename

    def klassesInOrder(self):
        """Return a list of all the Klasses in the order they were declared.

        Do not modify the list.
        """
        return self._klasses


    ## Reading files ##

    def read(self, filename):
        # @@ 2000-11-24 ce: split into readTable()
        self._filename = filename
        # PickleCache is used at the Model level, so we don't use it here:
        table = DataTable(filename, usePickleCache=False)

        # in case we want to look at these later:
        self._tableHeadings = table.headings()

        try:
            line = 2
            for row in table:
                row = ExpandDictWithExtras(row, dictForArgs=PyDictForArgs)
                for key in ['Class', 'Attribute']:
                    if key not in row:
                        print 'ERROR'
                        print 'Required key %s not found in row:' % key
                        print 'row:', row
                        print 'keys:', row.keys()
                        print row[key]  # throws exception
                if row['Class']:
                    pyClass = self._model.coreClass('Klass')
                    klass = pyClass(self, row)
                    self.addKlass(klass)
                else:
                    name = row['Attribute']
                    if name and name[0] != '#' and name[-1] != ':':
                        pyClassName = self.pyClassNameForAttrDict(row)
                        pyClass = self._model.coreClass(pyClassName)
                        klass.addAttr(pyClass(row))
                line += 1
        except ModelError as e:
            e.setLine(line)
            raise

    def awakeFromRead(self, model):
        """Perform further initialization.

        Expected to be invoked by the model.
        """
        assert self._model is model

        for klass in self._klasses:
            supername = klass.supername()
            if supername != 'MiddleObject':
                klass.setSuperklass(self.model().klass(supername))

        for klass in self._klasses:
            klass.awakeFromRead(self)

    def __getstate__(self):
        """For pickling, remove the back reference to the model that owns self."""
        assert self._model
        attrs = self.__dict__.copy()
        del attrs['_model']
        return attrs


    ## Adding classes ##

    def addKlass(self, klass):
        """Add a class definition.

        Restrictions: Cannot add two classes with the same name.
        """
        name = klass.name()
        assert name not in self, 'Already have %s.' % name
        self._klasses.append(klass)
        self[klass.name()] = klass
        klass.setKlasses(self)


    ## Self utility ##

    def pyClassNameForAttrDict(self, attrDict):
        """Return class for attribute definition.

        Given a raw attribute definition (in the form of a dictionary),
        this method returns the name of the Python class that should be
        instantiated for it. This method relies primarily on dict['Type'].
        """
        typeName = attrDict['Type']
        if not typeName:
            if attrDict['Attribute']:
                raise ModelError("no type specified for attribute '%s'"
                    % attrDict['Attribute'])
            else:
                raise ModelError('type specifier missing')

        # to support "list of <class>":
        if typeName.lower().startswith('list '):
            typeName = 'list'

        try:
            return self._typeNamesToAttrClassNames[typeName]
        except KeyError:
            return 'ObjRefAttr'

    def setting(self, name, default=NoDefault):
        """Return the value of a particular configuration setting taken from the model."""
        return self._model.setting(name, default)


    ## Debugging ##

    def dump(self):
        """Print each class."""
        for klass in self._klasses:
            print klass

    def debugString(self):
        return '<%s 0x%x model=%r>' % (self.__class__.__name__,
            id(self), getattr(self, '_model', '(none)'))
