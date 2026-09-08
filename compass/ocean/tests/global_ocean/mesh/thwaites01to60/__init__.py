import mpas_tools.mesh.creation.mesh_definition_tools as mdt
import numpy as np
from geometric_features import read_feature_collection
from mpas_tools.cime.constants import constants
from mpas_tools.mesh.creation.signed_distance import (
    signed_distance_from_geojson,
)

from compass.mesh import QuasiUniformSphericalMeshStep


class Thwaites01to60BaseMesh(QuasiUniformSphericalMeshStep):
    """
    A step for creating Thwaites 200m-to-60km variable resolution mesh

    Attributes
    ----------
    cell_width : numpy.ndarray
        m x n array of cell width in km

    x, y, z : numpy.ndarray
        m x n arrays defining the sphere
    """

    def setup(self):
        """
        Add geojson files as inputs
        """
        # TODO: Add thwaites_grounding_line.geojson when available
        # self.add_input_file(
        #     filename='thwaites_grounding_line.geojson',
        #     package=self.__module__)

        super().setup()

    def build_cell_width_lat_lon(self):
        """
        Create cell width array for this mesh on a regular latitude-longitude grid

        Returns
        -------
        cellWidth : numpy.array
            m x n array of cell width in km

        lon : numpy.array
            longitude in degrees (length n and between -180 and 180)

        lat : numpy.array
            latitude in degrees (length m and between -90 and 90)
        """
        km = 1.0e3

        # Get config parameters
        config = self.config
        section = config['thwaites01to60']

        res_gz = section.getfloat('res_gz')
        res_cavity = section.getfloat('res_cavity')
        res_shelf = section.getfloat('res_shelf')
        res_far = section.getfloat('res_far')
        gz_band_halfwidth = section.getfloat('gz_band_halfwidth')

        print('\nCreating Thwaites01to60 mesh with:')
        print(f'  GZ resolution: {res_gz} km')
        print(f'  Cavity resolution: {res_cavity} km')
        print(f'  Shelf resolution: {res_shelf} km')
        print(f'  Far-field resolution: {res_far} km')
        print(f'  GZ band halfwidth: {gz_band_halfwidth} km')

        # Create lat-lon grid for cellWidth
        dlon = 0.1
        dlat = dlon
        earth_radius = constants['SHR_CONST_REARTH']
        nlon = int(360. / dlon) + 1
        nlat = int(180. / dlat) + 1
        lon = np.linspace(-180., 180., nlon)
        lat = np.linspace(-90., 90., nlat)

        # Start with far-field resolution everywhere
        cellWidth = res_far * np.ones((nlat, nlon))

        # TODO: Add Thwaites grounding zone refinement when geojson is available
        # For now, create a simple latitudinal refinement in the Thwaites region
        # Thwaites is roughly at 75°S, 106°W

        # Create a simple box refinement for testing
        # This will be replaced with grounding-line-based refinement
        thwaites_lat = -75.0
        thwaites_lon = -106.0

        # Create distance-based refinement around Thwaites approximate location
        lon_grid, lat_grid = np.meshgrid(lon, lat)

        # Simple Gaussian-like refinement for testing
        # Convert to approximate distance (very rough for high latitudes)
        dist_lat = (lat_grid - thwaites_lat) ** 2
        dist_lon = ((lon_grid - thwaites_lon) * np.cos(np.radians(lat_grid))) ** 2
        approx_dist_deg = np.sqrt(dist_lat + dist_lon)

        # Define refinement zones by approximate distance (degrees)
        # GZ band: within ~0.2 degrees (~20km at this latitude)
        # Cavity: within ~1 degree
        # Shelf: within ~3 degrees

        gz_dist = 0.2
        cavity_dist = 1.0
        shelf_dist = 3.0

        # Apply refinements with smooth transitions
        # GZ refinement
        transition_width = 0.1
        mask_gz = 0.5 * (1 + np.tanh((approx_dist_deg - gz_dist) / transition_width))
        cellWidth = res_gz * (1 - mask_gz) + cellWidth * mask_gz

        # Cavity refinement
        mask_cavity = 0.5 * (1 + np.tanh((approx_dist_deg - cavity_dist) / transition_width))
        cellWidth = np.minimum(cellWidth,
                              res_cavity * (1 - mask_cavity) + cellWidth * mask_cavity)

        # Shelf refinement
        mask_shelf = 0.5 * (1 + np.tanh((approx_dist_deg - shelf_dist) / transition_width))
        cellWidth = np.minimum(cellWidth,
                              res_shelf * (1 - mask_shelf) + cellWidth * mask_shelf)

        print(f'  CellWidth range: {cellWidth.min():.2f} - {cellWidth.max():.2f} km')
        print('  NOTE: Using approximate Gaussian refinement around Thwaites')
        print('  TODO: Replace with grounding-line-based refinement from geojson')

        return cellWidth, lon, lat
