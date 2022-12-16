"""Core Broadcaster and Listener functionality.

This module provides two classes to use as base classes to create an environment
of Broadcasters and Listeners. Derivative listener classes must declare to
which Broadcasters they will subscribe via the subscribe_to field.

A class may inherit from both Broadcaster and Listener. This may be use to
create filters in which derivative listeners will only receive some of the
lines of a file.

"""
from collections import defaultdict
import glob
import importlib.util
import os


class IllegalListenerError(Exception):
    """Given Listener is programmed illegally.

    Do not try to catch this exception. Its intent is to be a "developer's"
    error, not an expected run time condition to handle gracefully.

    """
    pass


class IllegalBroadcasterError(Exception):
    """Given Broadcaster is programmed illegally.

    Do not try to catch this exception. Its intent to to be a "developer's"
    error, not an expected run time condition to handle gracefully.

    """
    pass


class ReportServer(object):

    def error(*args):
        raise NotImplementedError("Still working on this...")


class GlobalConfig(object):

    def __init__(self):
        self.rs = ReportServer()


class Base(object):

    def __init__(self, *args, **kwargs):
        self.gc = kwargs['gc'] # Instance of GlobalConfig
        self.parent = kwargs['parent']
        # super(Base, self).__init__()


class Broadcaster(Base): # pylint: disable=too-few-public-methods
    """Abstract base class for all broadcasters.

    A Broadcaster will receive information (often as a Listener Mixin) and
    replay that information out to all its subscribed listeners.

    Each Broadcaster calls a unique "update" function in its listeners. This is
    done so that a Listener may subscribe to more than one broadcaster. The
    update function is the name of the class with "Broadcaster" left stripped.

    """
    # The dict of listener classes that subscribe to this Broadcaster
    # Do not directly set this variable, the ListenerMeta type handles the registration
    # key : Broadcaster class
    listener_registry = defaultdict(list)

    @classmethod
    def listener_function_name(cls):
        return "update_{}".format(cls.__name__.lower().replace('broadcaster', ''))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener_instances = []
        if 'created_instances' not in kwargs:
            kwargs['created_instances'] = {}
        self._create_listener_instances(*args, **kwargs)

    def _create_listener_instances(self, *args, **kwargs):
        """Create all the subscribed listeners for this broadcaster."""
        for listener_class in self.__class__.listener_registry[self.__class__]:
            if 'restrictions' in kwargs:
                # For unittesting it simplifies mocking if not all listeners
                # are built (test cases don't have to adhere to all rules)
                if listener_class not in kwargs['restrictions']:
                    continue
            try:
                new_listener = kwargs['created_instances'][listener_class]
            except KeyError:
                kwargs['parent'] = self
                new_listener = listener_class(*args, **kwargs)
                kwargs['created_instances'][listener_class] = new_listener

            self.listener_instances.append(new_listener)

    def _broadcast(self, function_name, *args):
        """Echo args to all subscribed listeners."""
        for listener in self.listener_instances:
            try:
                listener_function = getattr(listener, function_name)
            except AttributeError as exc:
                raise IllegalListenerError("{} subscribed to {} but does not have a {} method.".format(
                    listener.__class__, self.__class__, function_name)) from exc
            if listener_function is not None:
                listener_function(*args)

    def broadcast(self, *args):
        listener_function_name = self.listener_function_name()
        self._broadcast(listener_function_name, *args)

    def get_listener(self, listener_name, broadcaster=None):
        if not broadcaster:
            broadcaster = self
        for listener in broadcaster.listener_instances:
            if listener_name == listener.__class__.__name__:
                return listener
            if isinstance(listener, Broadcaster):
                gl = self.get_listener(listener_name, listener)
                if gl:
                    return gl
        return None


class ListenerMeta(type):
    """Provides automatic registration of Listener classes to desired broadcasters.

    Derivative Listener's only have to set their subscribe_to class variable to
    the appropriate Broadcaster class.

    """

    def __new__(mcs, name, bases, attrs):
        new_class = type.__new__(mcs, name, bases, attrs)
        if Broadcaster in bases:
            mcs._handle_broadcaster(new_class)
        mcs._handle_listener(new_class)
        return new_class

    def _handle_broadcaster(new_class): # pylint: disable=bad-mcs-method-argument
        """Check that new Broadcaster class follows conventions."""
        if not new_class.__name__.endswith("Broadcaster"):
            raise IllegalBroadcasterError("Broadcaster classes must end name with 'Broadcaster': %s" %
                                          new_class.__name__)

    def _handle_listener(new_class): # pylint: disable=bad-mcs-method-argument
        """Check that new Listener class follows conventions.

        Also adds the new Listener class as a subscriber to the necessary
        broadcasters.

        """
        if not isinstance(new_class.subscribe_to, list):
            raise IllegalListenerError("subscribe_to variable must be of type list: %s" % new_class)

        if len(new_class.subscribe_to) == 0 and new_class.__name__ != "Listener":
            raise IllegalListenerError("%s did not subscribe to any broadcasters in subscribe_to class variable" %
                                       new_class.__name__)
        for subscription in new_class.subscribe_to:
            try:
                subscription.listener_registry[subscription].append(new_class)
            except AttributeError:
                raise IllegalListenerError("%s is not a valid Broadcaster to use in subscribe_to field." % subscription)


class Listener(Base, metaclass=ListenerMeta): # pylint: disable=too-few-public-methods
    """Abstract base class for all Listeners.

    Provides automatic registration with desired Broadcasters by setting the
    subscribe_to class member.

    """
    subscribe_to = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignored_broadcasters = {}

    def _ignore(self, broadcaster_class):
        """Stop subscribing to a particular broadcaster.

        This nullifies the corresponding update_* function and squirrels it
        away in another variable. The _pay_attention method is the counterpart to
        this method.

        Parameters
        ----------
        broadcaster_class : class derived from Broadcaster
           The class from which to ignore updates.

        """
        if broadcaster_class not in self.subscribe_to:
            raise IllegalListenerError("Cannot ignore {} because it is not a subscription.".format(broadcaster_class))
        if broadcaster_class in self._ignored_broadcasters:
            raise IllegalListenerError("{} previously ignored by {}".format(broadcaster_class, self))

        update_method = getattr(self, broadcaster_class.listener_function_name())
        setattr(self, broadcaster_class.listener_function_name(), None)
        self._ignored_broadcasters[broadcaster_class] = update_method

    def _pay_attention_to(self, broadcaster_class):
        """Renew a subscription to a broadcaster that was previously ignored.

        Parameters
        ----------
        broadcaster_class : class derived from Broadcaster
           Subscribe to updates from this class.

        """
        if broadcaster_class not in self.subscribe_to:
            raise IllegalListenerError(
                "Cannot pay attention to {} because it is not a subscription.".format(broadcaster_class))
        # FIXME is it possible that a pragma could trigger a user to see this error?
        # I.e. if they double waived an error in a file
        if broadcaster_class not in self._ignored_broadcasters:
            raise IllegalListenerError("{} was not previously ignored by {}".format(broadcaster_class, self))
        setattr(self, broadcaster_class.listener_function_name(), self._ignored_broadcasters[broadcaster_class])
        del self._ignored_broadcasters[broadcaster_class]

    def disable(self):
        for bc in self.subscribe_to:
            self._ignore(bc)

    def enable(self):
        for bc in self.subscribe_to:
            self._pay_attention_to(bc)


def glob_import_rules(filename, ignored_rules=[]):
    abs_filename = os.path.abspath(filename)
    lib_dir = os.path.dirname(abs_filename)
    srcs = glob.glob(os.path.join(lib_dir, "*.py"))
    for src in srcs:
        if os.path.abspath(src) == abs_filename:
            continue
        mod = src.split("/")[-1].replace(".py", "")
        if mod in ["__init__"]:
            continue
        rule = "".join([c.capitalize() for c in mod.split("_")])
        if rule in ignored_rules:
            continue
        spec = importlib.util.spec_from_file_location(src, src)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
