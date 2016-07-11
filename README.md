Python library interface to EcoPlug wifi outlet.

Until proper documentation...

    >>> from pyecoplug import *
    >>> plugs = {}
    >>> def add(s):
    ...     plugs[s.name] = s
    ... 
    >>> def remove(s):
    ...     del(plugs[s.name])
    ... 
    >>> e = EcoDiscovery(add, remove)
    >>> e.start()
    >>> plug
    {'test': ('## EcoPlug ##', b'test')}
    >>> plug['test'].is_on()
    False
    >>> plug['test'].turn_on()
    >>> plug['test'].is_on()
    True
    >>> plug['test'].turn_off()
    >>> plug['test'].is_on()
    False
    >>> plug['test'].turn_on()
    >>> plug['test'].turn_off()
    >>> e.stop()
