Python library interface to EcoPlug wifi outlet switch.

Until proper documentation...

    >>> from pyecoswitch import *
    >>> switches = {}
    >>> def add(s):
    ...     switches[s.name] = s
    ... 
    >>> def remove(s):
    ...     del(switches[s.name])
    ... 
    >>> e = EcoDiscovery(add, remove)
    >>> e.start()
    >>> switches
    {'test': ('## EcoSwitch ##', b'test')}
    >>> switches['test'].is_on()
    False
    >>> switches['test'].turn_on()
    >>> switches['test'].is_on()
    True
    >>> switches['test'].turn_off()
    >>> switches['test'].is_on()
    False
    >>> switches['test'].turn_on()
    >>> switches['test'].turn_off()
    >>> e.stop()
