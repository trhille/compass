from compass.config import CompassConfigParser
from compass.landice.tests.time_convergence.forward import Forward
from compass.testcase import TestCase


class ConvTestCase(TestCase):
    """
    A test case for various convergence tests on in MALI with planar,
    doubly periodic meshes

    Attributes
    ----------
    resolutions : list of int
    """
    def __init__(self, test_group, name):
        """
        Create test case for creating a MALI mesh

        Parameters
        ----------
        test_group : compass.ocean.tests.time_convergence.TimeConvergence
            The test group that this test case belongs to

        name : str
            The name of the test case
        """
        super().__init__(test_group=test_group, name=name)
        self.dts = None
        # add the steps with default resolutions so they can be listed
        config = CompassConfigParser()
        module = 'compass.landice.tests.time_convergence'
        config.add_from_package(module, 'time_convergence.cfg')
        self._setup_steps(config)

    def configure(self):
        """
        Set config options for the test case
        """
        config = self.config
        # set up the steps again in case a user has provided new resolutions
        self._setup_steps(config)

        self.update_cores()

    def update_cores(self):
        """ Update the number of cores and min_tasks for each forward step """

        config = self.config

        goal_cells_per_core = config.getfloat('time_convergence',
                                              'goal_cells_per_core')
        max_cells_per_core = config.getfloat('time_convergence',
                                             'max_cells_per_core')

        section = config['time_convergence']
        nx_1km = section.getint('nx_1km')
        ny_1km = section.getint('ny_1km')
        self.resolution = section.getint('resolution')
        resolution = self.resolution

        for dt in self.dts:
            nx = int(nx_1km / resolution)
            ny = int(ny_1km / resolution)
            # a heuristic based on
            cell_count = nx * ny
            # ideally, about 300 cells per core
            # (make it a multiple of 4 because...it looks better?)
            ntasks = max(1, 4 * round(cell_count / (4 * goal_cells_per_core)))
            # In a pinch, about 3000 cells per core
            min_tasks = max(1, round(cell_count / max_cells_per_core))
            step = self.steps[f'{dt}yr_forward']
            step.ntasks = ntasks
            step.min_tasks = min_tasks

            config.set('time_convergence', f'{dt}yr_ntasks',
                       str(ntasks))
            config.set('time_convergence', f'{dt}yr_min_tasks',
                       str(min_tasks))

    def _setup_steps(self, config):
        """
        setup steps given resolutions

        Parameters
        ----------
        config : compass.config.CompassConfigParser
            The config options containing the resolutions
        """

        dts = config.getlist('time_convergence', 'dts', dtype=float)

        if self.dts is not None and self.dts == dts:
            return

        # start fresh with no steps
        self.steps = dict()
        self.steps_to_run = list()

        self.dts = dts

        for dt in dts:
            self.add_step(self.create_init(dt=dt))
            self.add_step(Forward(test_case=self, dt=dt))

        self.add_step(self.create_analysis(dts=dts))

    def create_init(self, dt):
        """

        Child class must override this to return an instance of a
        ConvergenceInit step

        Parameters
        ----------
        resolution : int
            The resolution of the step

        Returns
        -------
        init : compass.landice.tests.time_convergence.convergence_init.ConvergenceInit  # noqa
            The init step object
        """

        pass

    def create_analysis(self, dt):
        """

        Child class must override this to return an instance of a
        ConvergenceInit step

        Parameters
        ----------
        resolutions : list of int
            The resolutions of the other steps in the test case

        Returns
        -------
        analysis : compass.landice.tests.time_convergence.conv_analysis.ConvAnalysis  # noqa
            The init step object
        """

        pass
