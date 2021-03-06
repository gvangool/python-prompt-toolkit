from __future__ import unicode_literals
from ..filters import Always, CLIFilter, Never
from ..utils import Callback

from collections import defaultdict

__all__ = (
    'Registry',
)


class _Binding(object):
    """
    (Immutable binding class.)
    """
    def __init__(self, keys, handler, filter=None):
        assert isinstance(keys, tuple)
        assert callable(handler)
        assert isinstance(filter, CLIFilter)

        self.keys = keys
        self._handler = handler
        self.filter = filter

    def call(self, event):
        return self._handler(event)

    def __repr__(self):
        return '%s(keys=%r, callable=%r)' % (
            self.__class__.__name__, self.keys, self._callable)


class Registry(object):
    """
    Key binding registry.

    ::

        r = Registry()

        @r.add_binding(Keys.ControlX, Keys.ControlC, filter=INSERT)
        def handler(event):
            # Handle ControlX-ControlC key sequence.
            pass
    """
    def __init__(self):
        self.key_bindings = []

        #: (tuple of keys) -> [list of bindings handling this sequence].
        self._keys_to_bindings = defaultdict(list)

        #: (tuple of keys) -> [list of bindings handling suffixes of this sequence].
        self._keys_to_bindings_suffixes = defaultdict(list)

        self.on_handler_called = Callback()

    def add_binding(self, *keys, **kwargs):
        """
        Decorator for annotating key bindings.
        """
        filter = kwargs.pop('filter', Always())

        assert not kwargs
        assert keys
        assert isinstance(filter, CLIFilter), 'Expected Filter instance, got %r' % filter

        def decorator(func):
            # When a filter is Never, it will always stay disabled, so in that case
            # don't bother putting it in the registry. It will slow down every key
            # press otherwise. (This happens for instance when a KeyBindingManager
            # is used, but some set of bindings are always disabled.)
            if not isinstance(filter, Never):
                binding = _Binding(keys, func, filter=filter)

                self.key_bindings.append(binding)
                self._keys_to_bindings[keys].append(binding)

                for i in range(1, len(keys)):
                    self._keys_to_bindings_suffixes[keys[:i]].append(binding)

            return func
        return decorator

    def get_bindings_for_keys(self, keys):
        """
        Return a list of key bindings that can handle this key.
        (This return also inactive bindings, so the `filter` still has to be
        called, for checking it.)

        :param keys: tuple of keys.
        """
        return self._keys_to_bindings[keys]

    def get_bindings_starting_with_keys(self, keys):
        """
        Return a list of key bindings that handle a key sequence starting with
        `keys`. (It does only return bindings for which the sequences are
        longer than `keys`. And like `get_bindings_for_keys`, it also includes
        inactive bindings.)

        :param keys: tuple of keys.
        """
        return self._keys_to_bindings_suffixes[keys]
