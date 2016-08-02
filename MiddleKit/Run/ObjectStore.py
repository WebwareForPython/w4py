import sys
import thread
from types import ClassType

from weakref import WeakValueDictionary

from MiscUtils import NoDefault
from MiscUtils.Funcs import safeDescription
from ObjectKey import ObjectKey
from MiddleKit.Core.ModelUser import ModelUser
from MiddleKit.Core.Klass import Klass as BaseKlass
from MiddleKit.Core.ObjRefAttr import ObjRefAttr
from MiddleKit.Core.ListAttr import ListAttr
    # ^^^ for use in _klassForClass() below
    # Can't import as Klass or Core.ModelUser (our superclass)
    # will try to mix it in.
from PerThreadList import PerThreadList, NonThreadedList
from PerThreadDict import PerThreadDict, NonThreadedDict


class UnknownObjectError(LookupError):
    """Unknown object error.

    This is the exception returned by store.fetchObject() if the specified
    object cannot be found (unless you also passed in a default value in
    which case that value is returned).
    """


class DeleteError(Exception):
    """Delete error.

    Base class for all delete exceptions.
    """


class DeleteReferencedError(DeleteError):
    """Delete referenced object error.

    This is raised when you attempt to delete an object that is referenced
    by other objects with onDeleteOther not set to detach or cascade.
    You can call referencingObjectsAndAttrs() to get a list of tuples of
    (object, attr) for the particular attributes that caused the error.
    And you can call object() to get the object that was trying to be deleted.
    This might not be the same as the object originally being deleted if a
    cascading delete was happening.
    """

    def __init__(self, text, obj, referencingObjectsAndAttrs):
        Exception.__init__(self, text)
        self._object = obj
        self._referencingObjectsAndAttrs = referencingObjectsAndAttrs

    def object(self):
        return self._object

    def referencingObjects(self):
        return self._referencingObjectsAndAttrs


class DeleteObjectWithReferencesError(DeleteError):
    """Delete object with references error.

    This is raised when you attempt to delete an object that references other
    objects, with onDeleteSelf=deny.  You can call attrs() to get a list of
    attributes that reference other objects with onDeleteSelf=deny.
    And you can call object() to get the object trying to be deleted that
    contains those attrs.  This might not be the same as the object originally
    being deleted if a cascading delete was happening.
    """

    def __init__(self, text, obj, attrs):
        Exception.__init__(self, text)
        self._object = obj
        self._attrs = attrs

    def object(self):
        return self._object

    def attrs(self):
        return self._attrs


class ObjectStore(ModelUser):
    """The object store.

    NOT IMPLEMENTED:
      * revertChanges()

    FUTURE
      * expanded fetch
    """


    ## Init ##

    def __init__(self):
        self._model = None
        self._newSerialNum = -1
        self._verboseDelete = False

    def modelWasSet(self):
        """Perform additional set up of the store after the model is set."""
        ModelUser.modelWasSet(self)
        self._threaded = self.setting('Threaded')
        if self._threaded:
            self._hasChanges = set()  # keep track on a per-thread basis
            self._newObjects = PerThreadList()
            self._deletedObjects = PerThreadList()
            self._changedObjects = PerThreadDict()
        else:
            self._hasChanges = False
            self._newObjects = NonThreadedList()
            self._deletedObjects = NonThreadedList()
            self._changedObjects = NonThreadedDict()
        self._objects = self.emptyObjectCache()  # dict; keyed by ObjectKeys

    def emptyObjectCache(self):
        if self.setting('CacheObjectsForever', False):
            return {}
        else:
            return WeakValueDictionary()


    ## Manipulating the objects in the store ##

    def hasObject(self, obj):
        """Check if the object is in the store.

        Note: this does not check the persistent store.
        """
        key = obj.key()
        if key is None:
            return False
        else:
            return key in self._objects

    def object(self, a, b=NoDefault, c=NoDefault):
        """Return object described by the given arguments, or default value.

        store.object(anObjectKey) - return the object with the given key,
            or raise a KeyError if it does not reside in memory.
        store.object(anObjectKey, defaultValue) - return the object
            or defaultValue (no exception will be raised)
        store.object(someClass, serialNum) - return the object
            of the given class and serial num, or raise a KeyError
        store.object(someClass, serialNum, defaultValue) - return the object
            or defaultValue (no exception will be raised)

        `someClass` can be a Python class, a string (the name of a class)
            or a MiddleKit.Core.Klass
        """
        if isinstance(a, ObjectKey):
            return self.objectForKey(a, b)
        else:
            return self.objectForClassAndSerial(a, b, c)

    def objectForClassAndSerial(self, klass, serialNum, default=NoDefault):
        if isinstance(klass, BaseKlass):
            klass = klass.name()
        elif isinstance(klass, (type, ClassType)):
            klass = klass.__name__
        else:
            assert isinstance(klass, str)
        key = ObjectKey().initFromClassNameAndSerialNum(klass, serialNum)
        return self.objectForKey(key, default)

    def objectForKey(self, key, default=NoDefault):
        """Return an object from the store by its given key.

        If no default is given and the object is not in the store,
        then an exception is raised.  Note: This method doesn't currently
        fetch objects from the persistent store.
        """
        if default is NoDefault:
            return self._objects[key]
        else:
            return self._objects.get(key, default)

    def add(self, obj, noRecurse=False):
        return self.addObject(obj, noRecurse)

    def addObject(self, obj, noRecurse=False):
        """Add the object and all referenced objects to the store.

        You can insert the same object multiple times, and you can insert
        an object that was loaded from the store.  In those cases, this is
        a no-op.  The noRecurse flag is used internally, and should be avoided
        in regular MiddleKit usage; it causes only this object to be added
        to the store, not any dependent objects.
        """
        if not obj.isInStore():
            assert obj.key() is None
            # Make the store aware of this new object
            self.willChange()
            self._newObjects.append(obj)
            obj.setStore(self)
            if not noRecurse:
                # Recursively add referenced objects to the store
                obj.addReferencedObjectsToStore(self)

            # 2000-10-07 ce: Decided not to allow keys for non-persisted objects
            # Because the serial num, and therefore the key, will change
            # upon saving.
            # key = obj.key()
            # if key is None:
            #     key = ObjectKey(obj, self)
            #     obj.setKey(key)
            # self._objects[key] = obj

    def deleteObject(self, obj):
        """Delete object.

        Restrictions: The object must be contained in the store and obviously
        you cannot remove it more than once.
        """
        # First check if the delete is possible.  Then do the actual delete.
        # This avoids partially deleting objects only to have an exception
        # halt the process in the middle.

        objectsToDel = {}
        detaches = []
        self._deleteObject(obj, objectsToDel, detaches)  # compute objectsToDel and detaches
        self.willChange()

        # detaches
        for obj, attr in detaches:
            if id(obj) not in objectsToDel:
                obj.setValueForAttr(attr, None)

        # process final list of objects
        objectsToDel = objectsToDel.values()
        for obj in objectsToDel:
            obj._mk_isDeleted = True
            self._deletedObjects.append(obj)
            obj.updateReferencingListAttrs()
            del self._objects[obj.key()]

    def _deleteObject(self, obj, objectsToDel, detaches, superobject=None):
        """Compile the list of objects to be deleted.

        This is a recursive method since deleting one object might be
        deleting others.

        obj          - the object to delete
        objectsToDel - a running dictionary of all objects to delete
        detaches     - a running list of all detaches (eg, obj.attr=None)
        superobject  - the object that was the cause of this invocation
        """
        # Some basic assertions
        assert self.hasObject(obj), safeDescription(obj)
        assert obj.key() is not None

        v = self._verboseDelete

        if v:
            if superobject:
                cascadeString = 'cascade-'
                dueTo = ' due to deletion of %s.%i' % (
                    superobject.klass().name(), superobject.serialNum())
            else:
                cascadeString = dueTo = ''
            print 'checking %sdelete of %s.%d%s' % (
                cascadeString, obj.klass().name(), obj.serialNum(), dueTo)

        objectsToDel[id(obj)] = obj

        # Get the objects/attrs that reference this object
        referencingObjectsAndAttrs = obj.referencingObjectsAndAttrs()

        # cascade-delete objects with onDeleteOther=cascade
        for referencingObject, referencingAttr in referencingObjectsAndAttrs:
            onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
            if onDeleteOther == 'cascade':
                self._deleteObject(referencingObject, objectsToDel, detaches, obj)

        # Determine all referenced objects, constructing a list of (attr, referencedObject) tuples.
        referencedAttrsAndObjects = obj.referencedAttrsAndObjects()

        # Check if it's possible to cascade-delete objects with onDeleteSelf=cascade
        for referencedAttr, referencedObject in referencedAttrsAndObjects:
            onDeleteSelf = referencedAttr.get('onDeleteSelf', 'detach')
            if onDeleteSelf == 'cascade':
                self._deleteObject(referencedObject, objectsToDel, detaches, obj)

        # Deal with all other objects that reference or are referenced by this object.
        # By default, you are not allowed to delete an object that has an ObjRef pointing to it.
        # But if the ObjRef has onDeleteOther=detach, then that ObjRef attr will be set to None
        # and the delete will be allowed; and if onDeleteOther=cascade, then that object will
        # itself be deleted and the delete will be allowed.
        #
        # You _are_ by default allowed to delete an object that points to other objects
        # (by List or ObjRef) but if onDeleteSelf=deny it will be disallowed, or if
        # onDeleteSelf=cascade the pointed-to objects will themselves be deleted.

        # Remove from that list anything in the cascaded list
        referencingObjectsAndAttrs = [(o, a)
            for o, a in referencingObjectsAndAttrs if id(o) not in objectsToDel]

        # Remove from that list anything in the cascaded list
        referencedAttrsAndObjects = [(a, o)
            for a, o in referencedAttrsAndObjects if id(o) not in objectsToDel]

        # Check for onDeleteOther=deny
        badObjectsAndAttrs = []
        for referencingObject, referencingAttr in referencingObjectsAndAttrs:
            onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
            assert onDeleteOther in ('deny', 'detach', 'cascade')
            if onDeleteOther == 'deny':
                badObjectsAndAttrs.append((referencingObject, referencingAttr))
        if badObjectsAndAttrs:
            raise DeleteReferencedError(
                'You tried to delete an object (%s.%d) that is referenced'
                ' by other objects with onDeleteOther unspecified or set to deny'
                % (obj.klass().name(), obj.serialNum()), obj, badObjectsAndAttrs)

        # Check for onDeleteSelf=deny
        badAttrs = []
        for referencedAttr, referencedObject in referencedAttrsAndObjects:
            onDeleteSelf = referencedAttr.get('onDeleteSelf', 'detach')
            assert onDeleteSelf in ['deny', 'detach', 'cascade']
            if onDeleteSelf == 'deny':
                badAttrs.append(referencedAttr)
        if badAttrs:
            raise DeleteObjectWithReferencesError(
                'You tried to delete an object (%s.%d) that references'
                ' other objects with onDeleteSelf set to deny'
                % (obj.klass().name(), obj.serialNum()), obj, badAttrs)

        # Detach objects with onDeleteOther=detach
        for referencingObject, referencingAttr in referencingObjectsAndAttrs:
            onDeleteOther = referencingAttr.get('onDeleteOther', 'deny')
            if onDeleteOther == 'detach':
                if v:
                    print 'will set %s.%d.%s to None' % (
                        referencingObject.klass().name(),
                        referencingObject.serialNum(), referencingAttr.name())
                detaches.append((referencingObject, referencingAttr))

        # Detach objects with onDeleteSelf=detach
        # This is actually a no-op. There is nothing that needs to be set to zero.


    ## Changes ##

    def hasChangesForCurrentThread(self):
        """Return whether the current thread has changes to be committed."""
        if self._threaded:
            threadid = thread.get_ident()
            return threadid in self._hasChanges
        else:
            return self._hasChanges

    def hasChanges(self):
        """Return whether any thread has changes to be committed."""
        if self._threaded:
            return bool(self._hasChanges)
        return self._hasChanges

    def willChange(self):
        if self._threaded:
            threadid = thread.get_ident()
            self._hasChanges.add(threadid)
        else:
            self._hasChanges = True

    def saveAllChanges(self):
        """Commit object changes to the object store.

        Done by invoking commitInserts(), commitUpdates() and commitDeletions()
        all of which must by implemented by a concrete subclass.
        """
        self.commitDeletions(allThreads=True)
        self.commitInserts(allThreads=True)
        self.commitUpdates(allThreads=True)
        if self._threaded:
            self._hasChanges = set()
        else:
            self._hasChanges = False

    def saveChanges(self):
        """Commit object changes to the object store.

        Done by invoking commitInserts(), commitUpdates() and commitDeletions()
        all of which must by implemented by a concrete subclass.
        """
        self.commitDeletions()
        self.commitInserts()
        self.commitUpdates()
        if self._threaded:
            self._hasChanges.discard(thread.get_ident())
        else:
            self._hasChanges = False

    def commitInserts(self):
        """Commit inserts.

        Invoked by saveChanges() to insert any news objects add since the
        last save. Subclass responsibility.
        """
        raise AbstractError(self.__class__)

    def commitUpdates(self):
        """Commit updates.

        Invoked by saveChanges() to update the persistent store with any
        changes since the last save.
        """
        raise AbstractError(self.__class__)

    def commitDeletions(self):
        """Commit deletions.

        Invoked by saveChanges() to delete from the persistent store any
        objects deleted since the last save. Subclass responsibility.
        """
        raise AbstractError(self.__class__)

    def revertChanges(self):
        """Revert changes.

        Discards all insertions and deletions, and restores changed objects
        to their original values.
        """
        raise AbstractError(self.__class__)


    ## Fetching ##

    def fetchObject(self, className, serialNum, default=NoDefault):
        """Fetch onkect of a given class.

        Subclasses should raise UnknownObjectError if an object with the
        given className and serialNum does not exist, unless a default value
        was passed in, in which case that value should be returned.
        """
        raise AbstractError(self.__class__)

    def fetchObjectsOfClass(self, className, isDeep=True):
        """Fetch all objects of a given class.

        If isDeep is True, then all subclasses are also returned.
        """
        raise AbstractError(self.__class__)

    def fetch(self, *args, **namedArgs):
        """An alias for fetchObjectsOfClass()."""
        return self.fetchObjectsOfClass(*args, **namedArgs)


    ## Other ##

    def clear(self):
        """Clear all objects from the memory of the store.

        This does not delete the objects in the persistent backing.
        This method can only be invoked if there are no outstanding changes
        to be saved.  You can check for that with hasChanges().
        """
        assert not self.hasChanges()
        assert self._newObjects.isEmpty()
        assert self._deletedObjects.isEmpty()
        assert self._changedObjects.isEmpty()

        self._objects = self.emptyObjectCache()
        self._newSerialNum = -1

    def discardEverything(self):
        """Discard all cached objects.

        This includes any modification tracking.  However, objects in memory
        will not change state as a result of this call.

        This method is a severe form of clear() and is typically used only
        for debugging or production emergencies.
        """
        if self._threaded:
            self._hasChanges = set()
        else:
            self._hasChanges = False
        self._objects = self.emptyObjectCache()
        self._newObjects.clear()
        self._deletedObjects.clear()
        self._changedObjects.clear()
        self._newSerialNum = -1


    ## Notifications ##

    def objectChanged(self, obj):
        """Mark attributes as changed.

        MiddleObjects must send this message when one of their interesting
        attributes change, where an attribute is interesting if it's listed
        in the class model.  This method records the object in a set for
        later processing when the store's changes are saved.
        If you subclass MiddleObject, then you're taken care of.
        """
        self.willChange()
        self._changedObjects[obj] = obj
        # @@ 2000-10-06 ce: Should this be keyed by the obj.key()? Does it matter?


    ## Serial numbers ##

    def newSerialNum(self):
        """Return a new serial number for a newly created object.

        This is a utility methods for objects that have been created, but
        not yet committed to the persistent store. These serial numbers are
        actually temporary and replaced upon committal. Also, they are always
        negative to indicate that they are temporary, whereas serial numbers
        taken from the persistent store are positive.
        """
        self._newSerialNum -= 1
        return self._newSerialNum


    ## Self utility ##

    def _klassForClass(self, aClass):
        """Return a Klass object for the given class.

        This may be:
            - the Klass object already
            - a Python class
            - a class name (e.g., string)
        Users of this method include the various fetchObjectEtc() methods
        which take a "class" parameter.
        """
        assert aClass is not None
        if not isinstance(aClass, BaseKlass):
            if isinstance(aClass, type):  # new Python classes
                aClass = self._model.klass(aClass.__name__)
            elif isinstance(aClass, ClassType):  # old Python classes
                aClass = self._model.klass(aClass.__name__)
            elif isinstance(aClass, basestring):
                aClass = self._model.klass(aClass)
            else:
                raise ValueError('Invalid class parameter. Pass a Klass,'
                    'a name or a Python class. Type of aClass is %s.'
                    ' aClass is %s.' % (type(aClass), aClass))
        return aClass


class Attr(object):

    def shouldRegisterChanges(self):
        """Return whether changes should be registered.

        MiddleObject asks attributes if changes should be registered.
        By default, all attributes respond true, but specific stores may
        choose to override this (a good example being ListAttr for SQLStore).
        """
        return True
