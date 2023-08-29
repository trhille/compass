from compass.landice.tests.time_convergence.conv_test_case import ConvTestCase
from compass.landice.tests.time_convergence.halfar.analysis import (  # noqa
    Analysis,
)
from compass.landice.tests.time_convergence.halfar.init import Init


class Halfar(ConvTestCase):
    """
    A test case for testing mesh convergence with the Halfar analytic test
    """
    def __init__(self, test_group):
        """
        Create test case for creating a MALI mesh

        Parameters
        ----------
        test_group : compass.landice.tests.time_convergence.TimeConvergence
            The landice test group that this test case belongs to
        """
        super().__init__(test_group=test_group, name='halfar')

        self.add_step(Analysis(test_case=self, dts=self.dts))

    def create_init(self, dt):
        """
        Child class must override this to return an instance of a
        ConvInit step

        Parameters
        ----------
        resolution : int
            The resolution of the test case

        Returns
        -------
        init : compass.landice.tests.time_convergence.conv_init.ConvInit
            The init step object
        """

        return Init(test_case=self, dt=dt)

    def create_analysis(self, dts):
        """

        Child class must override this to return an instance of a
        ConvergenceInit step

        Parameters
        ----------
        dts : list of int
            The dts of the other steps in the test case

        Returns
        -------
        analysis : compass.landice.tests.time_convergence.conv_analysis.ConvAnalysis  # noqa
            The init step object
        """

        return Analysis(test_case=self, dts=dts)
