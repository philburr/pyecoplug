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
    >>> plugs
    {'test': ('## EcoPlug ##', b'test')}
    >>> plugs['test'].is_on()
    False
    >>> plugs['test'].turn_on()
    >>> plugs['test'].is_on()
    True
    >>> plugs['test'].turn_off()
    >>> plugs['test'].is_on()
    False
    >>> plugs['test'].turn_on()
    >>> plugs['test'].turn_off()
    >>> e.stop()
