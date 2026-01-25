"""
Structural Analysis Utilities
Direct Stiffness Method Implementation
"""

import numpy as np
from scipy.linalg import solve
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class Support:
    """Support boundary condition"""
    node: int
    support_type: str  # "Fixed", "Pinned", "Roller-X", "Roller-Y"


@dataclass
class Load:
    """Load definition"""
    load_type: str  # "point", "udl", "vdl", "moment"
    member: int
    # Point load
    Px: float = 0.0
    Py: float = 0.0
    a: float = 0.0
    # Distributed loads
    w: float = 0.0   # UDL intensity
    w1: float = 0.0  # VDL start intensity
    w2: float = 0.0  # VDL end intensity
    b: float = 999.0  # End position for distributed loads
    # Moment
    M: float = 0.0


@dataclass
class Settlement:
    """Support settlement"""
    node: int
    delta_x: float = 0.0
    delta_y: float = 0.0
    delta_theta: float = 0.0


class StructuralSystem:
    """Main structural analysis system using Direct Stiffness Method"""
    
    def __init__(self):
        self.nodes = []  # [(x, y), ...]
        self.members = []  # [{'start': i, 'end': j, 'I': I, 'A': A}, ...]
        self.supports = []  # [Support, ...]
        self.loads = []  # [Load, ...]
        self.settlements = []  # [Settlement, ...]
        self.E = 200e6  # Young's modulus (kN/m²)
    
    def add_node(self, x: float, y: float) -> int:
        """Add a node and return its ID"""
        self.nodes.append((x, y))
        return len(self.nodes) - 1
    
    def add_member(self, start: int, end: int, I: float, A: float) -> int:
        """Add a member and return its ID"""
        self.members.append({
            'start': start,
            'end': end,
            'I': I,
            'A': A
        })
        return len(self.members) - 1
    
    def add_support(self, node: int, support_type: str):
        """Add a support"""
        self.supports.append(Support(node, support_type))
    
    def add_load(self, load: Load):
        """Add a load"""
        self.loads.append(load)
    
    def add_settlement(self, settlement: Settlement):
        """Add support settlement"""
        self.settlements.append(settlement)
    
    def get_member_length(self, member_idx: int) -> float:
        """Calculate member length"""
        member = self.members[member_idx]
        n1 = self.nodes[member['start']]
        n2 = self.nodes[member['end']]
        return np.sqrt((n2[0] - n1[0])**2 + (n2[1] - n1[1])**2)
    
    def get_member_angle(self, member_idx: int) -> float:
        """Calculate member angle (radians from horizontal)"""
        member = self.members[member_idx]
        n1 = self.nodes[member['start']]
        n2 = self.nodes[member['end']]
        return np.arctan2(n2[1] - n1[1], n2[0] - n1[0])
    
    def local_stiffness_matrix(self, member_idx: int) -> np.ndarray:
        """Generate 6x6 local stiffness matrix for a member"""
        member = self.members[member_idx]
        L = self.get_member_length(member_idx)
        E = self.E
        I = member['I']
        A = member['A']
        
        # Local stiffness matrix (6x6)
        # DOFs: [u1, v1, θ1, u2, v2, θ2]
        k = np.zeros((6, 6))
        
        # Axial terms
        EA_L = E * A / L
        k[0, 0] = EA_L
        k[0, 3] = -EA_L
        k[3, 0] = -EA_L
        k[3, 3] = EA_L
        
        # Bending terms
        EI_L = E * I / L
        EI_L2 = E * I / L**2
        EI_L3 = E * I / L**3
        
        k[1, 1] = 12 * EI_L3
        k[1, 2] = 6 * EI_L2
        k[1, 4] = -12 * EI_L3
        k[1, 5] = 6 * EI_L2
        
        k[2, 1] = 6 * EI_L2
        k[2, 2] = 4 * EI_L
        k[2, 4] = -6 * EI_L2
        k[2, 5] = 2 * EI_L
        
        k[4, 1] = -12 * EI_L3
        k[4, 2] = -6 * EI_L2
        k[4, 4] = 12 * EI_L3
        k[4, 5] = -6 * EI_L2
        
        k[5, 1] = 6 * EI_L2
        k[5, 2] = 2 * EI_L
        k[5, 4] = -6 * EI_L2
        k[5, 5] = 4 * EI_L
        
        return k
    
    def transformation_matrix(self, member_idx: int) -> np.ndarray:
        """Generate transformation matrix from local to global coordinates"""
        theta = self.get_member_angle(member_idx)
        c = np.cos(theta)
        s = np.sin(theta)
        
        # Transformation matrix (6x6)
        T = np.zeros((6, 6))
        
        # Rotation submatrix
        R = np.array([
            [c, s, 0],
            [-s, c, 0],
            [0, 0, 1]
        ])
        
        T[0:3, 0:3] = R
        T[3:6, 3:6] = R
        
        return T
    
    def global_stiffness_matrix(self, member_idx: int) -> np.ndarray:
        """Transform local stiffness to global coordinates"""
        k_local = self.local_stiffness_matrix(member_idx)
        T = self.transformation_matrix(member_idx)
        
        # K_global = T^T * k_local * T
        return T.T @ k_local @ T
    
    def calculate_fem(self, load: Load) -> Dict[str, float]:
        """Calculate Fixed End Moments and Forces for a load
        
        Returns: {'V1': V1, 'M1': M1, 'V2': V2, 'M2': M2, 'N1': N1, 'N2': N2}
        All in local coordinates
        """
        L = self.get_member_length(load.member)
        theta = self.get_member_angle(load.member)
        
        fem = {'V1': 0, 'M1': 0, 'V2': 0, 'M2': 0, 'N1': 0, 'N2': 0}
        
        if load.load_type == "point":
            # Transform to local coordinates
            Px_local = load.Px * np.cos(theta) + load.Py * np.sin(theta)
            Py_local = -load.Px * np.sin(theta) + load.Py * np.cos(theta)
            
            a = min(load.a, L)
            b = L - a
            
            # Transverse load (Py)
            if abs(Py_local) > 1e-10:
                fem['V1'] += Py_local * b**2 * (3*a + b) / L**3
                fem['M1'] += Py_local * a * b**2 / L**2
                fem['V2'] += Py_local * a**2 * (a + 3*b) / L**3
                fem['M2'] += -Py_local * a**2 * b / L**2
            
            # Axial load (Px)
            fem['N1'] += -Px_local
            fem['N2'] += Px_local
        
        elif load.load_type == "udl":
            w_local = load.w * np.cos(theta)  # Perpendicular to member
            
            a = min(load.a, L) if load.a > 0 else 0
            b = min(load.b, L) if load.b < 999 else L
            length = b - a
            
            if abs(w_local) > 1e-10 and length > 0:
                # UDL formulas for partial span
                c = a  # Distance from left to start of load
                
                fem['V1'] += w_local * length / 2
                fem['V2'] += w_local * length / 2
                fem['M1'] += w_local * length * (2*c + length) / 2
                fem['M2'] += -w_local * length * (2*(L-b) + length) / 2
        
        elif load.load_type == "vdl":
            # Trapezoidal load
            w1_local = load.w1 * np.cos(theta)
            w2_local = load.w2 * np.cos(theta)
            
            a = min(load.a, L) if load.a > 0 else 0
            b = min(load.b, L) if load.b < 999 else L
            length = b - a
            
            if length > 0:
                # Decompose into uniform + triangular
                w_uniform = min(abs(w1_local), abs(w2_local)) * np.sign(w1_local)
                w_triangular = abs(w2_local - w1_local) * np.sign(w2_local - w1_local)
                
                # Uniform part
                fem['V1'] += w_uniform * length / 2
                fem['V2'] += w_uniform * length / 2
                fem['M1'] += w_uniform * length**2 / 12
                fem['M2'] += -w_uniform * length**2 / 12
                
                # Triangular part (simplified)
                fem['V1'] += w_triangular * length / 3
                fem['V2'] += w_triangular * length * 2 / 3
                fem['M1'] += w_triangular * length**2 / 20
                fem['M2'] += -w_triangular * length**2 / 30
        
        elif load.load_type == "moment":
            a = min(load.a, L)
            b = L - a
            
            fem['M1'] += load.M * b * (2*a - b) / L**2
            fem['M2'] += load.M * a * (2*b - a) / L**2
        
        return fem
    
    def assemble_global_stiffness(self) -> Tuple[np.ndarray, np.ndarray]:
        """Assemble global stiffness matrix and load vector"""
        n_nodes = len(self.nodes)
        n_dofs = 3 * n_nodes  # 3 DOFs per node (u, v, θ)
        
        K_global = np.zeros((n_dofs, n_dofs))
        F_global = np.zeros(n_dofs)
        
        # Assemble stiffness from members
        for i, member in enumerate(self.members):
            K_member = self.global_stiffness_matrix(i)
            
            # DOF indices for start and end nodes
            start_node = member['start']
            end_node = member['end']
            
            dofs = [
                3*start_node, 3*start_node+1, 3*start_node+2,
                3*end_node, 3*end_node+1, 3*end_node+2
            ]
            
            # Add to global stiffness
            for local_i, global_i in enumerate(dofs):
                for local_j, global_j in enumerate(dofs):
                    K_global[global_i, global_j] += K_member[local_i, local_j]
        
        # Add fixed end forces from loads
        for load in self.loads:
            fem = self.calculate_fem(load)
            member = self.members[load.member]
            theta = self.get_member_angle(load.member)
            
            start_node = member['start']
            end_node = member['end']
            
            # Transform to global coordinates
            c = np.cos(theta)
            s = np.sin(theta)
            
            # Start node forces
            F_global[3*start_node] += -(fem['N1']*c - fem['V1']*s)
            F_global[3*start_node+1] += -(fem['N1']*s + fem['V1']*c)
            F_global[3*start_node+2] += -fem['M1']
            
            # End node forces
            F_global[3*end_node] += -(fem['N2']*c - fem['V2']*s)
            F_global[3*end_node+1] += -(fem['N2']*s + fem['V2']*c)
            F_global[3*end_node+2] += -fem['M2']
        
        return K_global, F_global
    
    def apply_boundary_conditions(self, K: np.ndarray, F: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """Apply support boundary conditions and settlements"""
        restrained_dofs = []
        
        # Identify restrained DOFs
        for support in self.supports:
            node = support.node
            if support.support_type == "Fixed":
                restrained_dofs.extend([3*node, 3*node+1, 3*node+2])
            elif support.support_type == "Pinned":
                restrained_dofs.extend([3*node, 3*node+1])
            elif support.support_type == "Roller-X":
                restrained_dofs.append(3*node)
            elif support.support_type == "Roller-Y":
                restrained_dofs.append(3*node+1)
        
        restrained_dofs = sorted(list(set(restrained_dofs)))
        
        # Handle settlements
        for settlement in self.settlements:
            node = settlement.node
            
            # Add settlement forces to right-hand side
            # F = F - K * d_known
            d_settlement = np.zeros(K.shape[0])
            d_settlement[3*node] = settlement.delta_x
            d_settlement[3*node+1] = settlement.delta_y
            d_settlement[3*node+2] = settlement.delta_theta
            
            F -= K @ d_settlement
        
        # Free DOFs (not restrained)
        all_dofs = set(range(K.shape[0]))
        free_dofs = sorted(list(all_dofs - set(restrained_dofs)))
        
        # Reduced system
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]
        
        return K_reduced, F_reduced, free_dofs
    
    def solve(self) -> Dict:
        """Solve the structural system and return results"""
        # Assemble global system
        K_global, F_global = self.assemble_global_stiffness()
        
        # Apply boundary conditions
        K_reduced, F_reduced, free_dofs = self.apply_boundary_conditions(K_global, F_global)
        
        # Solve for displacements
        d_reduced = solve(K_reduced, F_reduced)
        
        # Reconstruct full displacement vector
        n_dofs = K_global.shape[0]
        d_global = np.zeros(n_dofs)
        
        for i, dof in enumerate(free_dofs):
            d_global[dof] = d_reduced[i]
        
        # Add settlement displacements
        for settlement in self.settlements:
            node = settlement.node
            d_global[3*node] = settlement.delta_x
            d_global[3*node+1] = settlement.delta_y
            d_global[3*node+2] = settlement.delta_theta
        
        # Calculate reactions
        reactions = self.calculate_reactions(K_global, d_global, F_global)
        
        # Calculate member forces
        member_forces = self.calculate_member_forces(d_global)
        
        return {
            'displacements': d_global,
            'reactions': reactions,
            'member_forces': member_forces,
            'num_dofs': len(free_dofs)
        }
    
    def calculate_reactions(self, K: np.ndarray, d: np.ndarray, F: np.ndarray) -> Dict:
        """Calculate support reactions"""
        reactions = {}
        
        # Total forces = K*d
        F_total = K @ d
        
        for support in self.supports:
            node = support.node
            
            # Reaction = Total force - Applied force
            Rx = F_total[3*node] + F[3*node]
            Ry = F_total[3*node+1] + F[3*node+1]
            M = F_total[3*node+2] + F[3*node+2]
            
            reactions[node] = (Rx, Ry, M)
        
        return reactions
    
    def calculate_member_forces(self, d_global: np.ndarray) -> List[Dict]:
        """Calculate internal forces at member ends"""
        member_forces = []
        
        for i, member in enumerate(self.members):
            start_node = member['start']
            end_node = member['end']
            
            # Extract member displacements in global coordinates
            d_member_global = np.array([
                d_global[3*start_node],
                d_global[3*start_node+1],
                d_global[3*start_node+2],
                d_global[3*end_node],
                d_global[3*end_node+1],
                d_global[3*end_node+2]
            ])
            
            # Transform to local coordinates
            T = self.transformation_matrix(i)
            d_member_local = T @ d_member_global
            
            # Local forces = k_local * d_local
            k_local = self.local_stiffness_matrix(i)
            f_local = k_local @ d_member_local
            
            # Add fixed end forces from loads
            for load in self.loads:
                if load.member == i:
                    fem = self.calculate_fem(load)
                    f_local[0] += -fem['N1']
                    f_local[1] += -fem['V1']
                    f_local[2] += -fem['M1']
                    f_local[3] += -fem['N2']
                    f_local[4] += -fem['V2']
                    f_local[5] += -fem['M2']
            
            forces = {
                'start': {
                    'N': f_local[0],
                    'V': f_local[1],
                    'M': f_local[2]
                },
                'end': {
                    'N': f_local[3],
                    'V': f_local[4],
                    'M': f_local[5]
                }
            }
            
            member_forces.append(forces)
        
        return member_forces