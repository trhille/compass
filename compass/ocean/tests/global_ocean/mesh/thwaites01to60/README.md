# Thwaites01to60 Mesh

Variable-resolution global ocean mesh with 200m refinement at Thwaites grounding zone.

## Current Status

### ✅ Implemented:
1. **Base mesh generation** (`__init__.py`)
   - `Thwaites01to60BaseMesh` class
   - Currently uses simple Gaussian refinement around Thwaites (~75°S, 106°W)
   - Configurable resolutions: 200m GZ, 1km cavity, 3km shelf, 8km far-field

2. **Configuration** (`thwaites01to60.cfg`)
   - Resolution parameters
   - Optional regional domain settings (currently commented out)
   - Thin film parameters (disabled by default)

3. **Regional culling logic** (`modify_land_mask.py`)
   - Step to modify land mask before culling
   - Supports geojson polygon or lat-lon bounding box
   - **Not yet integrated into workflow** (see below)

4. **Registration**
   - Mesh registered in `compass/ocean/tests/global_ocean/mesh/__init__.py`
   - Can be listed/setup with compass (once compass is installed)

### 🚧 TODO:

#### High Priority:
1. **Integrate regional culling into CullMeshStep**
   - Current challenge: `land_mask.nc` is created inside CullMeshStep
   - Options:
     - Modify CullMeshStep to support pre-processing hooks
     - Create Thwaites-specific CullMeshStep subclass
     - Add regional culling logic directly to base CullMeshStep

2. **Replace Gaussian refinement with grounding-line-based refinement**
   - Extract Thwaites grounding line from BedMachine v4
   - Create `thwaites_grounding_line.geojson`
   - Use `signed_distance_from_geojson` for accurate GZ band

#### Medium Priority:
3. **Add thin film support**
   - Modify land mask to keep cells beneath grounded ice
   - Based on height above flotation from BedMachine
   - Requires integration with `remap_topography` step

4. **Testing**
   - Set up and run basic mesh generation
   - Validate cell widths and resolution
   - Test regional culling with lat-lon bounds
   - Test with/without thin film

#### Low Priority:
5. **Clean up copied FRIS files**
   - Remove unused geojson files (atlantic.geojson, fris_*.geojson, etc.)
   - Remove or adapt FRIS-specific namelists if needed

## Usage

### Basic mesh (no regional culling):
```bash
compass list | grep Thwaites
compass setup -t global_ocean/mesh/Thwaites01to60 -w $WORK
compass run $WORK
```

### With regional domain (when integrated):
Edit `thwaites01to60.cfg`:
```ini
[thwaites01to60]
# Option A: lat-lon bounds
lat_min = -75.5
lat_max = -74.0
lon_min = -115.0
lon_max = -100.0

# Option B: geojson polygon
# regional_domain_geojson = amundsen_domain.geojson
```

## Implementation Notes

### Mesh Refinement:
The current implementation uses an approximate Gaussian refinement:
```python
# Simple distance from Thwaites location
thwaites_lat = -75.0
thwaites_lon = -106.0
# Create smooth transition zones
```

This should be replaced with actual grounding-line-based refinement using
`signed_distance_from_geojson` (see FRIS meshes for examples).

### Regional Culling:
The `modify_land_mask.py` step contains the logic for regional culling:
1. Load base mesh and land mask
2. Determine cells inside/outside regional domain
3. Mark outside cells as "land"
4. Standard `CullMeshStep` then culls these cells

Integration challenge: land mask is created inside CullMeshStep's `run()` method,
so we need a way to modify it before culling happens.

### Thin Film:
Will require:
1. BedMachine topography (from `remap_topography` step)
2. Compute height above flotation for grounded ice
3. Cells with HAF < threshold (e.g., 30m) kept as ocean
4. Add `thinFilmMask` field for diagnostics

## References

- Design document: `/Users/trhille/Documents/Antarctica/thwaites_grounding_zone_intrusion/Grounding_zone_intrusion_simulation_design.pdf`
- Implementation plan: `/Users/trhille/Documents/Antarctica/thwaites_grounding_zone_intrusion/QUICK_START.md`
- FRIS mesh (template): `compass/ocean/tests/global_ocean/mesh/fris01to60/`
