import sys
from types import ModuleType

from MiscUtils.MixIn import MixIn
from MiscUtils import NoDefault


class ModelUser(object):


    ## Init ##

    def __init__(self):
        self._model = None


    ## Settings ##

    def setting(self, name, default=NoDefault):
        """Return the given setting which is actually just taken from the model."""
        return self._model.setting(name, default)


    ## Models ##

    def model(self):
        return self._model

    def setModel(self, model):
        assert model
        assert self._model is None, 'Can only set model once.'
        self._model = model
        self.modelWasSet()

    def readModelFileNamed(self, filename, modelClass=None, **keywords):
        assert self._model is None, 'Cannot re-read a model.'
        if modelClass is None:
            from MiddleKit.Core.Model import Model as modelClass
        self._model = modelClass(**keywords)
        self._model.read(filename)
        self.modelWasSet()

    def modelWasSet(self):
        """Perform additional set up of the store after the model is set.

        Invoked by setModel() or readModelFileNamed() as a hook for taking
        action on this event. Invokes installMixIns().
        """
        self.installMixIns()


    ## Mix-ins ##

    def installMixIns(self, verbose=False):
        if verbose:
            print '>> installMixIns()'
            print 'class =', self.__class__

        modules = self.modulesForClass(self.__class__)
        if verbose:
            print 'modules =', ', '.join(modules)

        # reverse order so that mix-ins in subclasses override super
        for module in reversed(modules):
            module = sys.modules[module]
            assert type(module) is ModuleType
            self.installMixInsForModule(module, verbose)

        if verbose:
            print

    def installMixInsForModule(self, module, verbose=False):
        # @@ 2000-10-18 ce: perhaps MixIns should be applied to the actual
        # MiddleKit.Core class and not the custom one that possibly was
        # passed into model. This would help with "invoking super" which
        # may be a non-trivial operation in a mix-in of a generator module.
        coreClassNames = self._model.coreClassNames()
        if verbose:
            print '>>', module
        for name in dir(module):
            generatorThing = getattr(module, name)
            if isinstance(generatorThing, type):
                # See if a class with the same name exists in MiddleKit.Core
                import MiddleKit.Core as Core
                if name in coreClassNames:
                    baseClass = self._model.coreClass(name)
                    if baseClass is not generatorThing:
                        if verbose:
                            print '>> mixing %s into %s' % (generatorThing, baseClass)
                        assert isinstance(baseClass, type)
                        assert isinstance(generatorThing, type)
                        MixIn(baseClass, generatorThing, mixInSuperMethods=True)


    ## Warning ##

    def warning(self, msg):
        """Output a warning.

        Invoked by self for any kind of appropriate warning that doesn't
        warrant an exception being thrown. Preferably, this should be invoked
        from a method that is invoked when the "bad event" occurs. This allows
        subclasses to override that method and potentially customize the
        behavior, including providing more debugging information.

        This implementation writes the msg to stdout.
        """
        print 'WARNING:', msg


    ## Self utility ##

    def modulesForClass(self, pyClass, modules=None):
        """Return the modules for the class.

        Returns a list of modules for pyClass, going up the chain of ancestor
        classes, stopping short before ModelUser. Utility method for installMixIns.
        """
        if modules is None:
            modules = []
        className = pyClass.__name__
        if className != 'ModelUser':
            modules.append(pyClass.__module__)
            for baseClass in pyClass.__bases__:
                self.modulesForClass(baseClass, modules)
        return modules
