import sys
import os
import getopt
import pandas as pd
import multiprocessing as mp
from datetime import timedelta
from pathlib import Path

from pandas.core.series import Series
from class_simulation import Simulation

path_to_simulation = Path('../artery/scenarios/dave/')
path_to_results = Path('../../../results/')
if not path_to_simulation.exists():
    path_to_simulation = Path('../dave/')
    path_to_results = Path('../results/')

automation_config_dict = {
    'SzenarioID': [0, str],
    'Netz': [1, str],
    'Verkehr': [2, str],
    'Hindernis': [3, bool],
    'Simulationsdauer': [4, timedelta],
    'QSV Abfolge': [5, str],
    'V2X-Rate': [6, float],
    'tau': [7, float],
    'Anzahl Wiederholungen': [8, int],
    'LSA': [9, bool]
}


def get_automation_config(path_to_config: Path) -> pd.DataFrame:
    """
    A function to read the configuration file for the automation process and check for correct input.

    Args:
        path_to_config (Path): path to the configuration file

    Returns:
        Configurations as pd.Dataframe. Each row is one configuration

    Raises:
        FileNotFoundError: If 'path_to_config' does not exist.
        NameError: If columns in configuration file are not named as expected.
        TypeError: If a value in configuration file has an unexpected datatype.

    """
    #: check if files exist
    try:
        path_to_config.resolve(strict=True)
    except FileNotFoundError:
        raise

    with open(path_to_config, newline='') as f:
        df_config = pd.read_csv(f, sep=';')

    #: check if config contains only expected columns
    try:
        if not list(automation_config_dict.keys()) == list(df_config.keys()):
            raise NameError
    except NameError:
        err_msg =\
            'Columns in configuration file are not named as expected!\nExpected:\n{0}\nbut got this:\n{1}'.format(
                list(automation_config_dict.keys()),
                list(df_config.keys()))
        print(err_msg)
        raise

    for key, definition in automation_config_dict.items():
        pos, val_type = definition
        if val_type is bool:
            df_config.loc[:, key] = df_config.loc[:, key].map(lambda num: bool(num))
        elif val_type is int:
            df_config.loc[:, key] = df_config.loc[:, key].map(lambda num: int(num))
        elif val_type is float:
            df_config.loc[:, key] = df_config.loc[:, key].map(lambda num: float(num.replace(',', '.')))
        elif val_type is timedelta:
            df_config.loc[:, key] = df_config.loc[:, key].map(lambda num: timedelta(seconds=num))
        elif val_type is str:
            df_config.loc[:, key] = df_config.loc[:, key].map(lambda num: str(num))
        else:
            print('Unexpected value type in configuration file!')
            raise TypeError

    return df_config


def sim_worker(config: Series):

    sim = Simulation(config, path_to_simulation=path_to_simulation, path_to_results=path_to_results)
    sim.prepare_sim()
    # sim.run_artery_sim()
    sim.run_sumo_standalone()
    sim.clean()


def main(argv):
    """
    Main method for simulation preparation.

    Main method to start the automated process of creating all necessary config files
    and iterate through the simulations.
    The simulation results will be stored in the results folder -- with sub-folders for each simulation.

    Returns:
        None

    """

    config_file = ''
    try:
        opts, args = getopt.getopt(argv, "hc:", ["cfile="])
    except getopt.GetoptError:
        print('main.py -c <configfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -c <configfile>')
            sys.exit()
        elif opt in ("-c", "--cfile"):
            config_file = Path(arg)

    print('config file is {0}'.format(config_file))

    #: check if SUMO_HOME is declared
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    #: read configuration file
    config_df = get_automation_config(path_to_config=config_file)

    # begin multiprocessing
    seq = [row for _, row in config_df.iterrows()]
    
    with mp.Pool(processes=mp.cpu_count()) as p:
        p.map(sim_worker, seq)


if __name__ == "__main__":
    #: main entry point
    main(sys.argv[1:])
