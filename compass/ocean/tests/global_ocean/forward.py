import os
from importlib.resources import contents

from compass.testcase import get_step_default
from compass.io import symlink
from compass import namelist, streams
from compass.model import partition, run_model
from compass.parallel import update_namelist_pio
from compass.ocean.tests.global_ocean.mesh import get_mesh_package


def collect(mesh_name, cores, min_cores=None, max_memory=1000,
            max_disk=1000, threads=1, testcase_module=None,
            namelist_file=None, streams_file=None,
            time_integrator='split_explicit'):
    """
    Get a dictionary of step properties

    Parameters
    ----------
    mesh_name : str
        The name of the mesh

    cores : int
        The number of cores to run on in forward runs. If this many cores are
        available on the machine or batch job, the task will run on that
        number. If fewer are available (but no fewer than min_cores), the job
        will run on all available cores instead.

    min_cores : int, optional
        The minimum allowed cores.  If that number of cores are not available
        on the machine or in the batch job, the run will fail.  By default,
        ``min_cores = cores``

    max_memory : int, optional
        The maximum amount of memory (in MB) this step is allowed to use

    max_disk : int, optional
        The maximum amount of disk space  (in MB) this step is allowed to use

    threads : int, optional
        The number of threads to run with during forward runs

    testcase_module : str, optional
        The module for the testcase

    namelist_file : str, optional
        The name of a namelist file in the testcase package directory

    streams_file : str, optional
        The name of a streams file in the testcase package directory

    time_integrator : {'split_explicit', 'RK4'}, optional
        The time integrator to use for the run

    Returns
    -------
    step : dict
        A dictionary of properties of this step
    """
    step = get_step_default(__name__)
    step['mesh_name'] = mesh_name
    step['cores'] = cores
    step['max_memory'] = max_memory
    step['max_disk'] = max_disk
    if min_cores is None:
        min_cores = cores
    step['min_cores'] = min_cores
    step['threads'] = threads
    if testcase_module is not None:
        step['testcase_module'] = testcase_module
    else:
        if namelist_file is not None or streams_file is not None:
            raise ValueError('You must supply a testcase module for the '
                             'namelist and/or streams file')
    if namelist_file is not None:
        step['namelist'] = namelist_file
    if streams_file is not None:
        step['streams'] = streams_file

    step['time_integrator'] = time_integrator

    return step


def setup(step, config):
    """
    Set up the test case in the work directory, including downloading any
    dependencies

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step from the ``collect()`` function

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core, configuration and testcase
    """
    mesh_name = step['mesh_name']
    step_dir = step['work_dir']
    time_integrator = step['time_integrator']

    # generate the namelist, replacing a few default options
    replacements = dict()

    replacements.update(namelist.parse_replacements(
        'compass.ocean.tests.global_ocean', 'namelist.forward'))

    if 'testcase_module' in step:
        testcase_module = step['testcase_module']
    else:
        testcase_module = None

    # add forward namelist options for this mesh
    mesh_package = get_mesh_package(mesh_name)
    mesh_package_contents = list(contents(mesh_package))
    mesh_namelists = ['namelist.forward',
                      'namelist.{}'.format(time_integrator.lower())]
    for mesh_namelist in mesh_namelists:
        if mesh_namelist in mesh_package_contents:
            replacements.update(namelist.parse_replacements(
                mesh_package, mesh_namelist))

    if 'namelist.forward' in mesh_package_contents:
        replacements.update(namelist.parse_replacements(
            mesh_package, 'namelist.forward'))

    # see if there's one for the testcase itself
    if 'namelist' in step:
        replacements.update(namelist.parse_replacements(
            testcase_module, step['namelist']))

    namelist.generate(config=config, replacements=replacements,
                      step_work_dir=step_dir, core='ocean', mode='forward')

    # generate the streams file
    streams_data = streams.read('compass.ocean.tests.global_ocean',
                                'streams.forward')

    # add streams for the mesh
    mesh_streams = ['streams.forward',
                    'streams.{}'.format(time_integrator.lower())]
    for mesh_stream in mesh_streams:
        if mesh_stream in mesh_package_contents:
            streams.read(mesh_package, mesh_stream, tree=streams_data)

    # see if there's one for the testcase itself
    if 'streams' in step:
        streams_data = streams.read(testcase_module, step['streams'],
                                    tree=streams_data)

    streams.generate(config=config, tree=streams_data, step_work_dir=step_dir,
                     core='ocean', mode='forward')

    # make a link to the ocean_model executable
    symlink(os.path.abspath(config.get('executables', 'model')),
            os.path.join(step_dir, 'ocean_model'))

    inputs = []
    outputs = []

    init_path = _get_init_relative_path(step)

    links = {'initial_state/initial_state.nc': 'init.nc',
             'initial_state/init_mode_forcing_data.nc':'forcing_data.nc',
             'mesh/culled_graph.info': 'graph.info'}
    for target, link in links.items():
        target = os.path.join(init_path, target)
        symlink(target, os.path.join(step_dir, link))
        inputs.append(os.path.abspath(os.path.join(step_dir, target)))

    for file in ['output.nc']:
        outputs.append(os.path.join(step_dir, file))

    step['inputs'] = inputs
    step['outputs'] = outputs


def run(step, test_suite, config, logger):
    """
    Run this step of the testcase

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step from the ``collect()``
        function, with modifications from the ``setup()`` function.

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core and configuration

    logger : logging.Logger
        A logger for output from the step
    """
    cores = step['cores']
    threads = step['threads']
    step_dir = step['work_dir']
    update_namelist_pio(config, cores, step_dir)
    partition(cores, logger)

    run_model(config, core='ocean', core_count=cores, logger=logger,
              threads=threads)


def _get_init_relative_path(step):
    """ get the relative path to the init testcase """

    # build a path that has a '..' for each directory in subdir
    subdir = os.path.join(step['testcase_subdir'], step['subdir'])
    # skip the mesh directory, which is common to all tests
    subdirs = subdir.split('/')[1:]
    path = '/'.join(['..' for _ in subdirs])
    path = '{}/init'.format(path)
    return path
