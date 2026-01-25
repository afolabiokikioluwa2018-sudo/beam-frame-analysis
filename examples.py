"""
Pre-defined example structures for demonstration
"""

from utils import StructuralSystem, Support, Load, Settlement


def load_example(example_name: str) -> StructuralSystem:
    """Load a pre-defined example structure"""
    
    if example_name == "Simply Supported Beam":
        return simply_supported_beam()
    elif example_name == "Continuous Beam (3 spans)":
        return continuous_beam()
    elif example_name == "Portal Frame":
        return portal_frame()
    elif example_name == "Settlement Case":
        return settlement_case()
    else:
        return StructuralSystem()


def simply_supported_beam():
    """Create a simply supported beam with UDL"""
    system = StructuralSystem()
    
    # Material properties
    system.E = 200e6  # kN/m²
    
    # Nodes
    system.add_node(0, 0)    # Node 0
    system.add_node(5, 0)    # Node 1
    
    # Members
    system.add_member(0, 1, I=0.001, A=0.1)  # Member 0
    
    # Supports
    system.add_support(0, "Pinned")     # Left support
    system.add_support(1, "Roller-Y")   # Right support
    
    # Loads
    system.add_load(Load("udl", 0, w=-10.0, a=0, b=999))  # UDL across entire beam
    
    return system


def continuous_beam():
    """Create a 3-span continuous beam"""
    system = StructuralSystem()
    
    # Material properties
    system.E = 200e6
    
    # Nodes - 4 nodes for 3 spans
    system.add_node(0, 0)    # Node 0
    system.add_node(4, 0)    # Node 1
    system.add_node(8, 0)    # Node 2
    system.add_node(12, 0)   # Node 3
    
    # Members - 3 spans
    system.add_member(0, 1, I=0.002, A=0.15)  # Span 1
    system.add_member(1, 2, I=0.002, A=0.15)  # Span 2
    system.add_member(2, 3, I=0.002, A=0.15)  # Span 3
    
    # Supports
    system.add_support(0, "Pinned")     # Left end
    system.add_support(1, "Roller-Y")   # Interior support 1
    system.add_support(2, "Roller-Y")   # Interior support 2
    system.add_support(3, "Roller-Y")   # Right end
    
    # Loads - Different on each span
    system.add_load(Load("udl", 0, w=-15.0, a=0, b=999))           # UDL on span 1
    system.add_load(Load("point", 1, Py=-20.0, a=2.0))            # Point load on span 2
    system.add_load(Load("vdl", 2, w1=-10.0, w2=-20.0, a=0, b=999))  # VDL on span 3
    
    return system


def portal_frame():
    """Create a simple portal frame"""
    system = StructuralSystem()
    
    # Material properties
    system.E = 200e6
    
    # Nodes - rectangular frame
    system.add_node(0, 0)    # Node 0 - Bottom left
    system.add_node(0, 4)    # Node 1 - Top left
    system.add_node(6, 4)    # Node 2 - Top right
    system.add_node(6, 0)    # Node 3 - Bottom right
    
    # Members
    system.add_member(0, 1, I=0.003, A=0.2)   # Left column
    system.add_member(1, 2, I=0.004, A=0.25)  # Beam
    system.add_member(2, 3, I=0.003, A=0.2)   # Right column
    
    # Supports
    system.add_support(0, "Fixed")    # Left base - fixed
    system.add_support(3, "Pinned")   # Right base - pinned
    
    # Loads
    system.add_load(Load("udl", 1, w=-20.0, a=0, b=999))      # UDL on beam (gravity)
    system.add_load(Load("point", 1, Px=15.0, Py=0.0, a=0))  # Horizontal wind at left top
    
    return system


def settlement_case():
    """Create a beam with support settlement"""
    system = StructuralSystem()
    
    # Material properties
    system.E = 200e6
    
    # Nodes - 2 span continuous beam
    system.add_node(0, 0)    # Node 0
    system.add_node(5, 0)    # Node 1
    system.add_node(10, 0)   # Node 2
    
    # Members
    system.add_member(0, 1, I=0.0015, A=0.12)  # Span 1
    system.add_member(1, 2, I=0.0015, A=0.12)  # Span 2
    
    # Supports
    system.add_support(0, "Fixed")     # Left - fixed
    system.add_support(1, "Roller-Y")  # Middle - roller
    system.add_support(2, "Roller-Y")  # Right - roller
    
    # Loads
    system.add_load(Load("udl", 0, w=-12.0, a=0, b=999))
    system.add_load(Load("udl", 1, w=-12.0, a=0, b=999))
    
    # Settlement at middle support (sinking)
    system.add_settlement(Settlement(node=1, delta_x=0.0, delta_y=-0.02, delta_theta=0.0))
    
    return system