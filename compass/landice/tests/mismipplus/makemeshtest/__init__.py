from compass.config import CompassConfigParser
from compass.landice.tests.mismipplus.setup_mesh import SetupMesh
from compass.testcase import TestCase


class MakeMeshTest(TestCase):
    """
    Mock test case for create the MISMIP+ mesh and initial conditions

    Attributes
    ----------
    resolution : int
        The resolution of the mesh (as defined configuration file)
    """
    def __init__(self, test_group):
        """
        Create the test case

        Parameters
        ----------
        test_group : compass.landice.test.mismipplus.setup_mesh
            The test group that this test case belongs to

        resolution : int
            The distance between horizontal (x-y) grid points
        """
        name = "MakeMeshTest"

        super().__init__(test_group=test_group, name=name)

        config = CompassConfigParser()
        module = 'compass.landice.tests.mismipplus'
        # add from config
        config.add_from_package(module, 'mismipplus.cfg')

        resolution = config.getint('mismipplus', 'resolution')

        # Setting up steps of test case
        self.add_step(SetupMesh(test_case=self, resolution=resolution))
