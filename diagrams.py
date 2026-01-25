"""
Diagram plotting functions using Plotly
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_structure(system):
    """Plot the structure with nodes, members, supports, and loads"""
    fig = go.Figure()
    
    # Plot members
    for i, member in enumerate(system.members):
        start = system.nodes[member['start']]
        end = system.nodes[member['end']]
        
        fig.add_trace(go.Scatter(
            x=[start[0], end[0]],
            y=[start[1], end[1]],
            mode='lines+text',
            line=dict(color='blue', width=3),
            text=[f'M{i}', ''],
            textposition='top center',
            name=f'Member {i}',
            showlegend=False
        ))
    
    # Plot nodes
    node_x = [n[0] for n in system.nodes]
    node_y = [n[1] for n in system.nodes]
    node_text = [f'N{i}' for i in range(len(system.nodes))]
    
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(size=12, color='red', symbol='circle'),
        text=node_text,
        textposition='top center',
        name='Nodes',
        showlegend=False
    ))
    
    # Plot supports
    for support in system.supports:
        node = system.nodes[support.node]
        
        if support.support_type == "Fixed":
            symbol = 'square'
            color = 'black'
        elif support.support_type == "Pinned":
            symbol = 'triangle-up'
            color = 'green'
        else:  # Roller
            symbol = 'circle'
            color = 'orange'
        
        fig.add_trace(go.Scatter(
            x=[node[0]],
            y=[node[1]],
            mode='markers',
            marker=dict(size=15, color=color, symbol=symbol, line=dict(width=2, color='black')),
            name=f'{support.support_type}',
            showlegend=False
        ))
    
    # Plot loads (simplified representation)
    for load in system.loads:
        member = system.members[load.member]
        n1 = system.nodes[member['start']]
        n2 = system.nodes[member['end']]
        
        # Midpoint of member
        mid_x = (n1[0] + n2[0]) / 2
        mid_y = (n1[1] + n2[1]) / 2
        
        if load.load_type == "point":
            # Show arrow
            fig.add_annotation(
                x=mid_x, y=mid_y,
                ax=mid_x, ay=mid_y + 0.5,
                xref='x', yref='y',
                axref='x', ayref='y',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='red'
            )
        elif load.load_type in ["udl", "vdl"]:
            # Show distributed load symbol
            fig.add_trace(go.Scatter(
                x=[mid_x],
                y=[mid_y + 0.3],
                mode='markers',
                marker=dict(size=10, color='red', symbol='arrow-down'),
                showlegend=False
            ))
    
    fig.update_layout(
        title="Structure Layout",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        hovermode='closest',
        showlegend=False,
        height=500,
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    
    return fig


def plot_sfd(system, results, member_idx):
    """Plot Shear Force Diagram for a member"""
    member = system.members[member_idx]
    L = system.get_member_length(member_idx)
    forces = results['member_forces'][member_idx]
    
    # Start and end shear forces
    V1 = forces['start']['V']
    V2 = forces['end']['V']
    
    # Get loads on this member
    member_loads = [load for load in system.loads if load.member == member_idx]
    
    # Create detailed shear diagram
    n_points = 100
    x = np.linspace(0, L, n_points)
    V = np.zeros(n_points)
    
    # Start with end shear
    V[0] = V1
    
    # Add effects of loads
    for i, xi in enumerate(x):
        V[i] = V1
        
        for load in member_loads:
            if load.load_type == "point":
                a = min(load.a, L)
                if xi > a:
                    # Get point load in local coordinates
                    theta = system.get_member_angle(member_idx)
                    Py_local = -load.Px * np.sin(theta) + load.Py * np.cos(theta)
                    V[i] -= Py_local
            
            elif load.load_type == "udl":
                w_local = load.w * np.cos(system.get_member_angle(member_idx))
                a = min(load.a, L) if load.a > 0 else 0
                b = min(load.b, L) if load.b < 999 else L
                
                if a <= xi <= b:
                    V[i] -= w_local * (xi - a)
                elif xi > b:
                    V[i] -= w_local * (b - a)
            
            elif load.load_type == "vdl":
                # Simplified VDL shear
                w1_local = load.w1 * np.cos(system.get_member_angle(member_idx))
                w2_local = load.w2 * np.cos(system.get_member_angle(member_idx))
                a = min(load.a, L) if load.a > 0 else 0
                b = min(load.b, L) if load.b < 999 else L
                
                if a <= xi <= b:
                    # Linear variation
                    w_xi = w1_local + (w2_local - w1_local) * (xi - a) / (b - a)
                    V[i] -= (w1_local + w_xi) * (xi - a) / 2
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x,
        y=V,
        mode='lines',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.2)',
        name='Shear Force'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
    
    fig.update_layout(
        title=f"Shear Force Diagram - Member {member_idx}",
        xaxis_title="Distance along member (m)",
        yaxis_title="Shear Force (kN)",
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_bmd(system, results, member_idx):
    """Plot Bending Moment Diagram for a member"""
    member = system.members[member_idx]
    L = system.get_member_length(member_idx)
    forces = results['member_forces'][member_idx]
    
    M1 = forces['start']['M']
    M2 = forces['end']['M']
    V1 = forces['start']['V']
    
    member_loads = [load for load in system.loads if load.member == member_idx]
    
    n_points = 100
    x = np.linspace(0, L, n_points)
    M = np.zeros(n_points)
    
    for i, xi in enumerate(x):
        # Start with end moment + shear effect
        M[i] = M1 + V1 * xi
        
        for load in member_loads:
            if load.load_type == "point":
                a = min(load.a, L)
                if xi > a:
                    theta = system.get_member_angle(member_idx)
                    Py_local = -load.Px * np.sin(theta) + load.Py * np.cos(theta)
                    M[i] -= Py_local * (xi - a)
            
            elif load.load_type == "udl":
                w_local = load.w * np.cos(system.get_member_angle(member_idx))
                a = min(load.a, L) if load.a > 0 else 0
                b = min(load.b, L) if load.b < 999 else L
                
                if a <= xi <= b:
                    M[i] -= w_local * (xi - a)**2 / 2
                elif xi > b:
                    M[i] -= w_local * (b - a) * (xi - (a + b) / 2)
            
            elif load.load_type == "vdl":
                # Simplified VDL moment
                w1_local = load.w1 * np.cos(system.get_member_angle(member_idx))
                w2_local = load.w2 * np.cos(system.get_member_angle(member_idx))
                a = min(load.a, L) if load.a > 0 else 0
                b = min(load.b, L) if load.b < 999 else L
                
                if a <= xi <= b:
                    dist = xi - a
                    M[i] -= (w1_local * dist**2 / 2 + 
                            (w2_local - w1_local) * dist**3 / (6 * (b - a)))
            
            elif load.load_type == "moment":
                a = min(load.a, L)
                if xi > a:
                    M[i] -= load.M
    
    # Sign convention: sagging (tension at bottom) is positive
    M = -M
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x,
        y=M,
        mode='lines',
        line=dict(color='red', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 0, 0, 0.2)',
        name='Bending Moment'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
    
    fig.update_layout(
        title=f"Bending Moment Diagram - Member {member_idx} (Sagging Positive)",
        xaxis_title="Distance along member (m)",
        yaxis_title="Bending Moment (kN·m)",
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_deflection(system, results, member_idx):
    """Plot deflection diagram for a member"""
    member = system.members[member_idx]
    L = system.get_member_length(member_idx)
    
    # Get displacements at nodes
    start_node = member['start']
    end_node = member['end']
    
    d_global = results['displacements']
    
    # Start node displacements (global)
    u1 = d_global[3*start_node]
    v1 = d_global[3*start_node + 1]
    theta1 = d_global[3*start_node + 2]
    
    # End node displacements (global)
    u2 = d_global[3*end_node]
    v2 = d_global[3*end_node + 1]
    theta2 = d_global[3*end_node + 2]
    
    # Transform to local coordinates
    theta_member = system.get_member_angle(member_idx)
    c = np.cos(theta_member)
    s = np.sin(theta_member)
    
    # Local displacements
    v1_local = -u1*s + v1*c
    v2_local = -u2*s + v2*c
    
    # Cubic interpolation for deflection
    n_points = 100
    x = np.linspace(0, L, n_points)
    
    # Hermite cubic interpolation
    v = np.zeros(n_points)
    for i, xi in enumerate(x):
        s = xi / L
        
        # Shape functions
        h1 = 1 - 3*s**2 + 2*s**3
        h2 = s - 2*s**2 + s**3
        h3 = 3*s**2 - 2*s**3
        h4 = -s**2 + s**3
        
        v[i] = h1*v1_local + h2*L*theta1 + h3*v2_local + h4*L*theta2
    
    fig = go.Figure()
    
    # Amplification factor for visualization
    max_deflection = max(abs(v)) if max(abs(v)) > 1e-10 else 1
    scale_factor = L / (20 * max_deflection) if max_deflection > 1e-10 else 1
    
    fig.add_trace(go.Scatter(
        x=x,
        y=v * scale_factor,
        mode='lines',
        line=dict(color='green', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)',
        name=f'Deflection (×{scale_factor:.1f})'
    ))
    
    # Original position
    fig.add_trace(go.Scatter(
        x=[0, L],
        y=[0, 0],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        name='Undeflected'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
    
    fig.update_layout(
        title=f"Deflection Diagram - Member {member_idx} (Amplified)",
        xaxis_title="Distance along member (m)",
        yaxis_title=f"Deflection (m × {scale_factor:.1f})",
        hovermode='x unified',
        height=400
    )
    
    return fig