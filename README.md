# 🏗️ Beam & Frame Analysis System

**CEG 410 University Project - Complete Structural Analysis Web Application**

A production-ready web application for analyzing 2D beams and frames using the **Direct Stiffness Method**. Built with Python, Streamlit, NumPy, and SciPy.

---

## ✨ Features

### Core Capabilities
- ✅ **Multiple Support Types**: Fixed, Pinned (Hinged), Roller (Simple)
- ✅ **Multi-span Beams & Multi-storey Frames**
- ✅ **Comprehensive Loading**:
  - Point Loads (vertical & horizontal)
  - Uniformly Distributed Loads (UDL)
  - Varying Distributed Loads (VDL/Trapezoidal)
  - Applied Moments
  - Any combination of above
- ✅ **Support Settlement**: Vertical/horizontal displacement at any support
- ✅ **Fixed End Moments (FEM)**: Accurately calculated for all load cases
- ✅ **Complete Output**:
  - Support reactions
  - Member end forces
  - Shear Force Diagrams (SFD)
  - Bending Moment Diagrams (BMD)
  - Deflection diagrams

### Technical Implementation
- **Direct Stiffness Method** (Matrix method)
- Global stiffness matrix assembly
- Transformation matrices (local ↔ global)
- Boundary condition application
- SciPy linear solver for equation systems
- Interactive Plotly visualizations

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step-by-Step Setup

1. **Download/Clone the project**
   ```bash
   # If you have the files in a folder
   cd beam-frame-analysis
   ```

2. **Create virtual environment (recommended)**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

5. **Open in browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, manually navigate to the URL shown in terminal

---

## 📁 Project Structure

```
beam-frame-analysis/
│
├── main.py              # Main Streamlit application (UI & orchestration)
├── utils.py             # Core analysis engine (Direct Stiffness Method)
├── diagrams.py          # Visualization functions (Plotly charts)
├── examples.py          # Pre-defined example structures
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### File Descriptions

**`main.py`** - Streamlit Web Interface
- User input handling (nodes, members, supports, loads)
- Session state management
- Tab-based result display
- Interactive controls

**`utils.py`** - Structural Analysis Core
- `StructuralSystem` class: Main analysis engine
- `Support`, `Load`, `Settlement` dataclasses
- Stiffness matrix assembly (local & global)
- FEM calculations for all load types
- Boundary condition application
- Direct stiffness solver

**`diagrams.py`** - Plotting Functions
- Structure visualization
- Shear force diagrams
- Bending moment diagrams (sagging positive)
- Deflection diagrams with amplification

**`examples.py`** - Example Structures
- Simply supported beam
- 3-span continuous beam
- Portal frame
- Settlement case

---

## 🚀 Quick Start Guide

### Method 1: Using Examples
1. Open the app
2. In sidebar → "Load Example" → Select example
3. Click "Load Example" button
4. Go to "Analysis" tab → Click "🚀 Solve Structure"
5. View results in tabs: Reactions, Member Forces, Diagrams

### Method 2: Building from Scratch
1. **Add Nodes**: Sidebar → Nodes → Enter X, Y coordinates
2. **Create Members**: Connect nodes, specify I and A
3. **Add Supports**: Choose node and support type
4. **Apply Loads**: Select load type and parameters
5. **Solve**: Analysis tab → Solve Structure
6. **View Results**: Navigate through result tabs

---

## 📖 User Guide

### Support Types
- **Fixed**: Restrains translation (X, Y) and rotation
- **Pinned**: Restrains translation (X, Y) only
- **Roller-X**: Restrains X translation only
- **Roller-Y**: Restrains Y translation only

### Load Types

#### Point Load
- **Px**: Horizontal component (kN)
- **Py**: Vertical component (kN)  
- **a**: Distance from start of member (m)

#### UDL (Uniformly Distributed Load)
- **w**: Intensity (kN/m)
- **a**: Start position (use 0 for full span)
- **b**: End position (use 999 for full span)

#### VDL (Varying Distributed Load)
- **w1**: Start intensity (kN/m)
- **w2**: End intensity (kN/m)
- **a, b**: Start and end positions

#### Moment
- **M**: Moment magnitude (kN·m)
- **a**: Distance from start (m)

### Settlement
- **Node**: Support node to displace
- **Δx**: Horizontal displacement (m)
- **Δy**: Vertical displacement (m, negative = sinking)
- **Δθ**: Rotational displacement (rad)

---

## 🎓 Theory & Methodology

### Direct Stiffness Method

The application implements the classic matrix displacement method:

1. **Local Stiffness Matrix** (6×6 for each member)
   ```
   [k_local] with DOFs: [u1, v1, θ1, u2, v2, θ2]
   ```

2. **Transformation to Global Coordinates**
   ```
   [K_global] = [T]ᵀ [k_local] [T]
   ```

3. **Assembly of Global Stiffness Matrix**
   - Superposition of member contributions
   - Properly indexed to node DOFs

4. **Fixed End Actions**
   - Calculated for each load type
   - Transformed to global coordinates
   - Assembled into load vector

5. **Boundary Conditions**
   - Restraint equations applied
   - Reduced system formation

6. **Solution**
   ```
   [K_reduced]{d} = {F_reduced}
   ```
   Solved using SciPy's Gaussian elimination

7. **Post-Processing**
   - Member forces from displacements
   - Support reactions from equilibrium
   - Internal force distributions

### Sign Conventions
- **Bending Moments**: Sagging (tension at bottom) = Positive
- **Shear Forces**: Right face upward = Positive
- **Axial Forces**: Tension = Positive
- **Rotations**: Counter-clockwise = Positive

---

