"""
pstat_debug.py

This pstat function decorator will track a function within the pstat tool.
This is the easiest way to profile slow code for Panda3d.
"""

def pstat(func):
    from pandac.PandaModules import PStatCollector
    collectorName = "Debug:%s" % func.__name__
    if hasattr(base, 'custom_collectors'):
        if collectorName in base.custom_collectors.keys():
            pstat = base.custom_collectors[collectorName]
        else:
            base.custom_collectors[collectorName] = PStatCollector(collectorName)
            pstat = base.custom_collectors[collectorName]
    else:
        base.custom_collectors = {}
        base.custom_collectors[collectorName] = PStatCollector(collectorName)
        pstat = base.custom_collectors[collectorName]
    def doPstat(*args, **kargs):
        pstat.start()
        returned = func(*args, **kargs)
        pstat.stop()
        return returned
    doPstat.__name__ = func.__name__
    doPstat.__dict__ = func.__dict__
    doPstat.__doc__ = func.__doc__
    return doPstat