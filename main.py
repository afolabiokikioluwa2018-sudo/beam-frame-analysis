"""
CEG 410 - Beam and Frame Analysis Web Application
Direct Stiffness Method Implementation
Author: Structural Analysis Tool
"""

import streamlit as st
import numpy as np
import pandas as pd
from utils import StructuralSystem, Support, Load, Settlement
from diagrams import plot_structure, plot_sfd, plot_bmd, plot_deflection
from examples import load_example

# Page configuration
st.set_page_config(
    page_title="Beam & Frame Analysis",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'system' not in st.session_state:
    st.session_state.system = StructuralSystem()
if 'solved' not in st.session_state:
    st.session_state.solved = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Header
st.markdown('<p class="main-header">🏗️ Beam & Frame Analysis System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Direct Stiffness Method | CEG 410 Project</p>', unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("⚙️ System Configuration")
    
    # Example loader
    st.subheader("📋 Load Example")
    example_options = [
        "Start Fresh",
        "Simply Supported Beam",
        "Continuous Beam (3 spans)",
        "Portal Frame",
        "Settlement Case"
    ]
    selected_example = st.selectbox("Choose Example:", example_options)
    
    if st.button("Load Example") and selected_example != "Start Fresh":
        st.session_state.system = load_example(selected_example)
        st.session_state.solved = False
        st.success(f"✅ Loaded: {selected_example}")
    
    if st.button("🔄 Clear All"):
        st.session_state.system = StructuralSystem()
        st.session_state.solved = False
        st.session_state.results = None
        st.rerun()
    
    st.divider()
    
    # Material Properties
    st.subheader("🔧 Material Properties")
    E = st.number_input("Young's Modulus E (kN/m²)", value=200e6, format="%.2e")
    st.session_state.system.E = E
    
    st.divider()
    
    # Node Input
    st.subheader("📍 Nodes")
    with st.expander("Add Node", expanded=False):
        col1, col2 = st.columns(2)
        node_x = col1.number_input("X (m)", value=0.0, key="node_x")
        node_y = col2.number_input("Y (m)", value=0.0, key="node_y")
        if st.button("➕ Add Node"):
            node_id = st.session_state.system.add_node(node_x, node_y)
            st.success(f"Added Node {node_id}")
            st.session_state.solved = False
    
    # Display nodes
    if st.session_state.system.nodes:
        nodes_df = pd.DataFrame([
            {"Node": i, "X": n[0], "Y": n[1]} 
            for i, n in enumerate(st.session_state.system.nodes)
        ])
        st.dataframe(nodes_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Member Input
    st.subheader("📏 Members")
    with st.expander("Add Member", expanded=False):
        if len(st.session_state.system.nodes) >= 2:
            col1, col2 = st.columns(2)
            start_node = col1.selectbox("Start Node", range(len(st.session_state.system.nodes)), key="mem_start")
            end_node = col2.selectbox("End Node", range(len(st.session_state.system.nodes)), key="mem_end")
            I = st.number_input("Moment of Inertia I (m⁴)", value=0.001, format="%.6f")
            A = st.number_input("Cross-sectional Area A (m²)", value=0.1, format="%.4f")
            if st.button("➕ Add Member"):
                if start_node != end_node:
                    member_id = st.session_state.system.add_member(start_node, end_node, I, A)
                    st.success(f"Added Member {member_id}")
                    st.session_state.solved = False
                else:
                    st.error("Start and end nodes must be different!")
        else:
            st.info("Add at least 2 nodes first")
    
    # Display members
    if st.session_state.system.members:
        members_df = pd.DataFrame([
            {"Member": i, "From": m['start'], "To": m['end'], "I": m['I'], "A": m['A']} 
            for i, m in enumerate(st.session_state.system.members)
        ])
        st.dataframe(members_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Support Input
    st.subheader("🔒 Supports")
    with st.expander("Add Support", expanded=False):
        if st.session_state.system.nodes:
            support_node = st.selectbox("Node", range(len(st.session_state.system.nodes)), key="sup_node")
            support_type = st.selectbox("Type", ["Fixed", "Pinned", "Roller-X", "Roller-Y"])
            if st.button("➕ Add Support"):
                st.session_state.system.add_support(support_node, support_type)
                st.success(f"Added {support_type} support at Node {support_node}")
                st.session_state.solved = False
        else:
            st.info("Add nodes first")
    
    # Display supports
    if st.session_state.system.supports:
        supports_df = pd.DataFrame([
            {"Node": s.node, "Type": s.support_type} 
            for s in st.session_state.system.supports
        ])
        st.dataframe(supports_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Load Input
    st.subheader("⚡ Loads")
    with st.expander("Add Load", expanded=False):
        if st.session_state.system.members:
            load_type = st.selectbox("Load Type", ["Point Load", "UDL", "VDL", "Moment"])
            
            if load_type == "Point Load":
                member = st.selectbox("Member", range(len(st.session_state.system.members)), key="pl_mem")
                col1, col2 = st.columns(2)
                Px = col1.number_input("Px (kN)", value=0.0)
                Py = col2.number_input("Py (kN)", value=-10.0)
                a = st.number_input("Distance from start (m)", value=1.0, min_value=0.0)
                if st.button("➕ Add Point Load"):
                    st.session_state.system.add_load(Load("point", member, Px=Px, Py=Py, a=a))
                    st.success("Added Point Load")
                    st.session_state.solved = False
            
            elif load_type == "UDL":
                member = st.selectbox("Member", range(len(st.session_state.system.members)), key="udl_mem")
                w = st.number_input("Intensity w (kN/m)", value=-5.0)
                col1, col2 = st.columns(2)
                a = col1.number_input("Start (m)", value=0.0, min_value=0.0)
                b = col2.number_input("End (m)", value=999.0, min_value=0.0)
                if st.button("➕ Add UDL"):
                    st.session_state.system.add_load(Load("udl", member, w=w, a=a, b=b))
                    st.success("Added UDL")
                    st.session_state.solved = False
            
            elif load_type == "VDL":
                member = st.selectbox("Member", range(len(st.session_state.system.members)), key="vdl_mem")
                col1, col2 = st.columns(2)
                w1 = col1.number_input("w1 (kN/m)", value=-5.0)
                w2 = col2.number_input("w2 (kN/m)", value=-10.0)
                col3, col4 = st.columns(2)
                a = col3.number_input("Start (m)", value=0.0, min_value=0.0, key="vdl_a")
                b = col4.number_input("End (m)", value=999.0, min_value=0.0, key="vdl_b")
                if st.button("➕ Add VDL"):
                    st.session_state.system.add_load(Load("vdl", member, w1=w1, w2=w2, a=a, b=b))
                    st.success("Added VDL")
                    st.session_state.solved = False
            
            elif load_type == "Moment":
                member = st.selectbox("Member", range(len(st.session_state.system.members)), key="mom_mem")
                M = st.number_input("Moment M (kN·m)", value=10.0)
                a = st.number_input("Distance (m)", value=1.0, min_value=0.0, key="mom_a")
                if st.button("➕ Add Moment"):
                    st.session_state.system.add_load(Load("moment", member, M=M, a=a))
                    st.success("Added Moment")
                    st.session_state.solved = False
        else:
            st.info("Add members first")
    
    # Display loads
    if st.session_state.system.loads:
        st.write(f"**Total Loads:** {len(st.session_state.system.loads)}")
        for i, load in enumerate(st.session_state.system.loads):
            st.caption(f"{i+1}. {load.load_type.upper()} on Member {load.member}")
    
    st.divider()
    
    # Settlement Input
    st.subheader("⬇️ Support Settlement")
    with st.expander("Add Settlement", expanded=False):
        if st.session_state.system.supports:
            support_idx = st.selectbox("Support", range(len(st.session_state.system.supports)))
            col1, col2 = st.columns(2)
            delta_x = col1.number_input("Δx (m)", value=0.0, format="%.6f")
            delta_y = col2.number_input("Δy (m)", value=0.0, format="%.6f")
            delta_theta = st.number_input("Δθ (rad)", value=0.0, format="%.6f")
            if st.button("➕ Add Settlement"):
                node = st.session_state.system.supports[support_idx].node
                st.session_state.system.add_settlement(Settlement(node, delta_x, delta_y, delta_theta))
                st.success(f"Added settlement at Node {node}")
                st.session_state.solved = False
        else:
            st.info("Add supports first")
    
    # Display settlements
    if st.session_state.system.settlements:
        settlements_df = pd.DataFrame([
            {"Node": s.node, "Δx": s.delta_x, "Δy": s.delta_y, "Δθ": s.delta_theta} 
            for s in st.session_state.system.settlements
        ])
        st.dataframe(settlements_df, hide_index=True, use_container_width=True)

# Main content area
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📐 Structure", "🔍 Analysis", "📊 Reactions", "📈 Member Forces", "📉 Diagrams", "ℹ️ Help"
])

with tab1:
    st.header("Structure Visualization")
    if st.session_state.system.nodes and st.session_state.system.members:
        fig = plot_structure(st.session_state.system)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👈 Add nodes and members from the sidebar to visualize the structure")

with tab2:
    st.header("Structural Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", len(st.session_state.system.nodes))
    with col2:
        st.metric("Members", len(st.session_state.system.members))
    with col3:
        st.metric("Supports", len(st.session_state.system.supports))
    
    st.divider()
    
    if st.button("🚀 Solve Structure", type="primary", use_container_width=True):
        if not st.session_state.system.members:
            st.error("❌ No members defined!")
        elif not st.session_state.system.supports:
            st.error("❌ No supports defined!")
        else:
            with st.spinner("Solving using Direct Stiffness Method..."):
                try:
                    results = st.session_state.system.solve()
                    st.session_state.results = results
                    st.session_state.solved = True
                    st.success("✅ Analysis Complete!")
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
    
    if st.session_state.solved and st.session_state.results:
        st.success("✅ Structure successfully analyzed!")
        st.info(f"**DOFs Solved:** {st.session_state.results['num_dofs']}")

with tab3:
    st.header("Support Reactions")
    if st.session_state.solved and st.session_state.results:
        reactions = st.session_state.results['reactions']
        reactions_data = []
        for node, react in reactions.items():
            reactions_data.append({
                "Node": node,
                "Rx (kN)": f"{react[0]:.4f}",
                "Ry (kN)": f"{react[1]:.4f}",
                "M (kN·m)": f"{react[2]:.4f}"
            })
        st.dataframe(pd.DataFrame(reactions_data), hide_index=True, use_container_width=True)
    else:
        st.info("Run analysis first to see reactions")

with tab4:
    st.header("Member End Forces")
    if st.session_state.solved and st.session_state.results:
        member_forces = st.session_state.results['member_forces']
        for i, forces in enumerate(member_forces):
            with st.expander(f"Member {i} (Node {st.session_state.system.members[i]['start']} → {st.session_state.system.members[i]['end']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Start End:**")
                    st.write(f"Axial: {forces['start']['N']:.4f} kN")
                    st.write(f"Shear: {forces['start']['V']:.4f} kN")
                    st.write(f"Moment: {forces['start']['M']:.4f} kN·m")
                with col2:
                    st.write("**End End:**")
                    st.write(f"Axial: {forces['end']['N']:.4f} kN")
                    st.write(f"Shear: {forces['end']['V']:.4f} kN")
                    st.write(f"Moment: {forces['end']['M']:.4f} kN·m")
    else:
        st.info("Run analysis first to see member forces")

with tab5:
    st.header("Shear Force & Bending Moment Diagrams")
    if st.session_state.solved and st.session_state.results:
        member_select = st.selectbox("Select Member:", range(len(st.session_state.system.members)))
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Shear Force Diagram")
            fig_sfd = plot_sfd(st.session_state.system, st.session_state.results, member_select)
            st.plotly_chart(fig_sfd, use_container_width=True)
        
        with col2:
            st.subheader("Bending Moment Diagram")
            fig_bmd = plot_bmd(st.session_state.system, st.session_state.results, member_select)
            st.plotly_chart(fig_bmd, use_container_width=True)
        
        st.divider()
        st.subheader("Deflection Diagram")
        fig_def = plot_deflection(st.session_state.system, st.session_state.results, member_select)
        st.plotly_chart(fig_def, use_container_width=True)
    else:
        st.info("Run analysis first to see diagrams")

with tab6:
    st.header("How to Use This Application")
    
    st.markdown("""
    ### 📚 Step-by-Step Guide
    
    1. **Define Nodes** 📍
       - Add nodes at key structural points
       - Input X and Y coordinates in meters
    
    2. **Create Members** 📏
       - Connect nodes to form beams/frames
       - Specify moment of inertia (I) and area (A)
    
    3. **Add Supports** 🔒
       - **Fixed**: Restrains all DOFs (x, y, rotation)
       - **Pinned**: Restrains x and y translation
       - **Roller**: Restrains one translation direction
    
    4. **Apply Loads** ⚡
       - **Point Load**: Concentrated force at distance 'a'
       - **UDL**: Uniform distributed load
       - **VDL**: Varying (trapezoidal) distributed load
       - **Moment**: Concentrated moment
    
    5. **Settlement (Optional)** ⬇️
       - Define support displacements
    
    6. **Solve** 🚀
       - Click "Solve Structure" to run analysis
    
    7. **View Results** 📊
       - Check reactions, member forces, and diagrams
    
    ### 🎓 Theory
    
    This application uses the **Direct Stiffness Method**:
    - Assembles global stiffness matrix [K]
    - Calculates fixed-end forces for all loads
    - Applies boundary conditions
    - Solves [K]{d} = {F} using Gaussian elimination
    - Post-processes for reactions and internal forces
    
    ### 📐 Sign Conventions
    
    - **Moments**: Counter-clockwise positive
    - **Shear**: Right face upward positive
    - **Bending**: Sagging (tension bottom) positive
    - **Axial**: Tension positive
    
    ### ⚠️ Notes
    
    - Units: kN, m, kN/m, kN·m
    - For UDL/VDL: use large 'b' value (999) for full span
    - Structure must be stable (proper supports)
    """)

# Footer
st.divider()
st.caption("CEG 410 Project | Direct Stiffness Method | © 2025")