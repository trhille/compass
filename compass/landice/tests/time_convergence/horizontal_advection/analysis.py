import warnings

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from compass.landice.tests.time_convergence.conv_analysis import ConvAnalysis


class Analysis(ConvAnalysis):
    """
    A step for visualizing the output from the advection convergence test case
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
        super().__init__(test_case=test_case, dts=dts)
        self.dts = dts
        self.add_output_file('convergence.png')

    def run(self):
        """
        Run this step of the test case
        """
        plt.switch_backend('Agg')
        dts = self.dts
        ncells_list = list()
        errors = list()
        for dt in dts:
            rms_error, ncells = self.rmse(dt, variable='passiveTracer')
            ncells_list.append(ncells)
            errors.append(rms_error)

        ncells = np.array(ncells_list)
        errors = np.array(errors)

        p = np.polyfit(np.log10(dts), np.log10(errors), 1)
        conv = abs(p[0]) * 2.0

        error_fit = dts**p[0] * 10**p[1]

        plt.loglog(dts, error_fit, 'k')
        plt.loglog(dts, errors, 'or')
        plt.annotate('Order of Convergence = {}'.format(np.round(conv, 3)),
                     xycoords='axes fraction', xy=(0.3, 0.95), fontsize=14)
        plt.xlabel('dt', fontsize=14)
        plt.ylabel('L2 Norm', fontsize=14)
        section = self.config['time_convergence']
        duration = section.getfloat('duration')
        plt.title(f'Horizontal advection convergence test, {duration} yrs')
        plt.savefig('convergence.png', bbox_inches='tight', pad_inches=0.1)

        section = self.config['horizontal_advection']
        conv_thresh = section.getfloat('conv_thresh')
        conv_max = section.getfloat('conv_max')

        if conv < conv_thresh:
            raise ValueError(f'order of convergence '
                             f' {conv} < min tolerence {conv_thresh}')

        if conv > conv_max:
            warnings.warn(f'order of convergence '
                          f'{conv} > max tolerence {conv_max}')

    def rmse(self, dt, variable):
        """
        Compute the RMSE for a given resolution

        Parameters
        ----------
        resolution : int
            The resolution of the (uniform) mesh in km

        variable : str
            The name of a variable in the output file to analyze.

        Returns
        -------
        rms_error : float
            The root-mean-squared error

        ncells : int
            The number of cells in the mesh
        """
        dt_tag = '{}yr'.format(dt)

        ds = xr.open_dataset('{}_output.nc'.format(dt_tag))
        init = ds[variable].isel(Time=0)
        final = ds[variable].isel(Time=-1)
        diff = final - init
        rms_error = np.sqrt((diff**2).mean()).values
        ncells = ds.sizes['nCells']
        return rms_error, ncells
