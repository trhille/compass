from compass.step import Step


class ConvAnalysis(Step):
    """
    A step for visualizing and/or analyzing the output from a convergence test
    case

    Attributes
    ----------
    resolutions : list of int
        The resolutions of the meshes that have been run
    """
    def __init__(self, test_case, dts):
        """
        Create the step

        Parameters
        ----------
        test_case : compass.TestCase
            The test case this step belongs to

        resolutions : list of int
            The resolutions of the meshes that have been run
        """
        super().__init__(test_case=test_case, name='analysis')
        self.dts = dts

        # typically, the analysis will rely on the output from the forward
        # steps
        for dt in dts:
            self.add_input_file(
                filename='{}yr_output.nc'.format(dt),
                target='../{}yr/forward/output.nc'.format(dt))
