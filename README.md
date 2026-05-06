# GA_presentation 
> **Geometrical Algorithms:** From Convex Hulls to Optimal Pathfinding.

## 🛠 Project Roadmap & presentation TODO

### Phase 1: Foundations & Input Pipeline
- [ ] **Static Dataset**: Define hardcoded geometric primitives (Square, Circle, Star) for algorithm validation.
- [ ] **Descrive** 3D print + scanner

### Phase 2: Boundary & Topology
- [ ] **Convex Hull**: Implement **Graham Scan / QuickHull** 
- [ ] **animation success/fail**
- [ ] **Winding Number**:
    - [ ] Logic for non-closed segments.
    - [ ] Animation of parity checks (Point-in-Polygon).
- [ ] **Constraint Visualization**: Render the "convex limit" for fabricating not convex shapes.

### Phase 3: Mesh & Structural Optimization (Delaunay)
- [ ] **Delaunay**: 
    - [ ] Generate mesh from points
- [ ] **Mesh Pruning**:
    - [ ] Use Winding Number to filter "exterior" triangles.

### Phase 4: Pathfinding & Demo
- [ ] **Toolpath Optimization**: Sort edges to minimize "travel moves" (head lifting).
- [ ] **Show animation** of travelled pin
- [ ] **RNG Engine**: 
    - [ ] Implement Random Point Cloud generator (Uniform/Gaussian).
    - [ ] Add "Stress Test" mode with high-density noise.
- [ ] **Final Demo Flow**: 
    - [ ] Comparison: `Static Primitive` vs `RNG Cloud` vs `noise`.
