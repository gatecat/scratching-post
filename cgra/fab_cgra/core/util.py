from amaranth import *
from amaranth.hdl.rec import Layout
from typing import TypeAlias

__all__ = ["PortVal", "PortShape", "port_width"]

PortVal: TypeAlias = Value|int
PortShape: TypeAlias = Layout|int

def port_width(lay: PortShape):
    if isinstance(lay, Layout):
        sum(v[0] for v in lay.fields.values())
    else:
        return lay
