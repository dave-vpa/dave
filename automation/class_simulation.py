"""
Module to manage simulations.
"""

import os
import random
import shutil
from pathlib import Path
import pandas as pd
from datetime import time, datetime, date, timedelta
from createODMatrixFile import create_od_matrix_file
from createSUMOConfigFile import create_sumo_config_file
from createServicesFile import create_services_file
from createOmnetppFile import create_omnetpp_file
from createAdditionalFile import create_additional_file


def customize_vtype_file(path_to_vtypes_ref: Path,
                         path_to_vtypes_new: Path,
                         tau: float) -> None:
    """
    A function to create / manipulate an additional file for vtypes.

    It replaces the value for tau in 'vtype.add.xml' and saves it as new additional file.
    Args:
        path_to_vtypes_ref: path to template file
        path_to_vtypes_new: path to new output file
        tau: value for tau (tau = drivers desired time headway (in seconds))

    Returns:
        None

    """

    with open(path_to_vtypes_ref, 'r') as f:
        file_content = f.read()

    old_string = 'tau="1.0"'
    new_string = 'tau="{0}"'.format(tau)
    new_content = file_content.replace(old_string, new_string)

    with open(path_to_vtypes_new, 'w') as f:
        f.write(new_content)
    pass


class Simulation:
    """
    A class to manage a single simulation.

    Class Attributes:
        num_sim (int):
            instance counter
        radius_rsu (int):
            CAM transmission distance in meter (= CAM receiving radius for RSU)
        sumo_action_step_length (float):
            !!!only used for B170!!!,
            action-step-length of SUMO
            vehicles perform calculations for the adaption of accelerations or lane-change maneuvers only at intervals
            of the given length and not within every simulations step (which is the default)
        dict_traffic_types:
            dictionary with used traffic types
        dict_qsv_x:
            dictionary with 'Auslastungsgrad'

    Attributes:
        sim_id (str): unique ID to identify the simulation

    """

    num_sim = 0
    
    # Artery specific parameters
    radius_rsu = 600

    # SUMO specific parameters
    _sumo_action_step_length = timedelta(milliseconds=1000)
    _sumo_step_length = timedelta(milliseconds=100)
    _sumo_fcd_output_interval = timedelta(milliseconds=100)
    _sumo_edge_dump_interval = timedelta(seconds=60)
    _sumo_max_depart_delay = timedelta(seconds=1)

    dict_traffic_types = {
        'miv': 5,
        'sv': 9
    }

    dict_qsv_x = {
        'a': [0.00, 0.30],
        'b': [0.30, 0.55],
        'c': [0.55, 0.75],
        'd': [0.75, 0.90],
        'e': [0.90, 1.00],
        'f': [1.00, 1.15],
        'g': [1.00, 1.00],
        'h': [0.10, 0.10],
        'i': [0.20, 0.20],
        'j': [0.30, 0.30],
        'k': [0.40, 0.40],
        'l': [0.50, 0.50],
        'm': [0.60, 0.60],
        'n': [0.70, 0.70],
        'o': [0.80, 0.80],
        'p': [0.85, 0.85],
        'q': [0.90, 0.90],
        'r': [0.95, 0.95],
        's': [1.00, 1.00],
        't': [1.05, 1.05],
        'u': [1.10, 1.10],
        'v': [1.20, 1.20],
        'w': [1.30, 1.30],
        'x': [1.40, 1.40],
        'y': [1.50, 1.50],
        'z': [1.60, 1.60],
        '1': [1.70, 1.70],
        '2': [1.80, 1.80],
        '3': [1.90, 1.90],
    }

    def __init__(self, sim_config: pd.Series, path_to_simulation: Path, path_to_results: Path):
        """
        Init method for Class 'Simulation'.

        Args:
            sim_config (pd.Series): configuration for one simulation
            path_to_simulation (Path): path to simulation

        Raises:
            FileNotFoundError: If one of the necessary files or directories is missing.

        """

        self.sim_id: str = sim_config[0]
        self._net = sim_config[1]
        self._traffic = sim_config[2]
        self._obstruction = sim_config[3]
        self._duration = sim_config[4]
        self._qsv_sequence = list(sim_config[5])
        self._v2x_rate = sim_config[6]
        self._tau = sim_config[7]
        self._num_repeat = sim_config[8]
        self._use_tls = sim_config[9]
        self._sim_config = sim_config
        self._start_time = time(hour=0, minute=0, second=0)

        self._path_to_simulation = path_to_simulation
        self._path_to_sumo = self._path_to_simulation / 'sumo'
        self._path_to_additional = self._path_to_sumo / 'additional'
        self._path_to_traffic = self._path_to_sumo / 'traffic' / self._traffic
        self._path_to_routes = self._path_to_sumo / 'routes' / self.sim_id
        self._path_to_config = self._path_to_sumo / 'config'

        self._path_to_results = self._path_to_simulation / path_to_results / '{0}'.format(self.sim_id)
        self._path_to_results_sumo = self._path_to_sumo / '../{0}/{1}/sumo'.format(path_to_results, self.sim_id)
        self._path_to_results_omnet = self._path_to_results / 'omnet'
        self._path_to_results_dave = self._path_to_results / 'dave'
        self._path_to_results_config = self._path_to_results / 'config'

        Path(self._path_to_routes).mkdir(parents=True, exist_ok=True)
        Path(self._path_to_config).mkdir(parents=True, exist_ok=True)
        Path(self._path_to_results_sumo).mkdir(parents=True, exist_ok=True)
        Path(self._path_to_results_omnet).mkdir(parents=True, exist_ok=True)
        Path(self._path_to_results_dave).mkdir(parents=True, exist_ok=True)
        Path(self._path_to_results_config).mkdir(parents=True, exist_ok=True)

        self._path_to_sumo_config_file = self._path_to_sumo / 'config' / '{0}.sumocfg'.format(self.sim_id)
        self._path_to_net_file = self._path_to_sumo / 'net' / self._net
        self._path_to_additional_file = self._path_to_additional / '{0}_additional.add.xml'.format(self.sim_id)
        self._path_to_poly_file = self._path_to_sumo / 'net' / 'dave.poly.add.xml'
        self._path_to_taz_file = self._path_to_traffic / 'taz.xml'
        self._path_to_detector_config = self._path_to_traffic / 'detector_config.csv'
        self._path_to_fcd_output_file = self._path_to_results_sumo / 'fcd.out.xml'
        self._path_to_edge_dump_file = self._path_to_results_sumo / 'edge_dump.out.xml'

        self._path_to_vtypes_ref = self._path_to_additional / 'vtypes.add.xml'
        self._path_to_vtypes = self._path_to_additional / '{0}_vtypes.add.xml'.format(self.sim_id)
        self._path_to_gui_view_file = self._path_to_additional / 'view.add.xml'
        self._path_to_obstruction_trips_file = self._path_to_traffic / 'obstruction.trips.xml'
        self._path_to_odroute_file = self._path_to_routes / '{0}_od_routes.rou.xml'.format(self.sim_id)

        self._path_to_services_file = self._path_to_simulation / '{0}_services.xml'.format(self.sim_id)
        self._path_to_omnetpp_file = Path('{0}_omnetpp.ini'.format(self.sim_id))
        self._path_to_omnetpp_file_long = Path('{0}/{1}_omnetpp.ini'.format(self._path_to_simulation, self.sim_id))
        self._path_to_rsu_config = self._path_to_traffic / 'rsu_config.csv'
        self._path_to_artery_shell_file = Path('../../build/run_artery.sh')

        #: check if files / directories exist
        try:
            self._path_to_simulation.resolve(strict=True)
            self._path_to_sumo.resolve(strict=True)
            self._path_to_additional.resolve(strict=True)
            self._path_to_routes.resolve(strict=True)
            self._path_to_traffic.resolve(strict=True)
            self._path_to_net_file.resolve(strict=True)
        except FileNotFoundError:
            raise

        type(self).num_sim += 1  #: increment instance counter

    def __del__(self):
        type(self).num_sim -= 1  #: decrement instance counter

    def prepare_sim(self) -> None:
        """
        A method to do all preparations for SUMO & OMNeT/Artery simulation.

        Returns:
            None

        """

        self.__save_configs()
        self.__prepare_sumo()
        self.__prepare_omnet()

    def run_artery_sim(self) -> None:
        """
        A method to run the Artery V2X-simulation.

        Returns:
            None

        """

        #: create command line command
        cmd_omnet = '{0} -u Cmdenv -f {1}'.format(self._path_to_artery_shell_file, self._path_to_omnetpp_file)
        print('Start Artery:\n{0}'.format(cmd_omnet))

        #: start simulation
        cwd = os.getcwd()  #: get current working directory
        os.chdir(self._path_to_simulation)  #: change to simulation directory
        os.system(cmd_omnet)  #: start simulation
        os.chdir(cwd)  #: change back directory

    def run_sumo_standalone(self) -> None:
        """
        A method to run only the SUMO simulation.

        It's meant for testing, evaluation & validation of the SUMO simulation.

        Returns:
            None

        """
        cmd_sumo = 'sumo-gui -c {0} -X never'.format(self._path_to_sumo_config_file)

        print('Start SUMO:\n{0}'.format(cmd_sumo))
        os.system(cmd_sumo)

    def clean(self) -> None:
        """
        A method to remove all temporary files created for each individual simulation.

        Returns:
            None

        """

        #: Creates list of files/directories for removal.
        objects_2_delete = [self._path_to_vtypes,
                            self._path_to_sumo_config_file,
                            self._path_to_omnetpp_file_long,
                            self._path_to_services_file,
                            self._path_to_routes,
                            self._path_to_additional_file]

        #: Iterates list and delete.
        for object_2_delete in objects_2_delete:
            if object_2_delete.is_file():
                os.remove(object_2_delete)
            elif object_2_delete.is_dir():
                shutil.rmtree(object_2_delete)

    def __save_configs(self) -> None:
        """
        A method to copy the configuration files to the results folder.

        Considered configurations are:\n
        - RSU configuration
        - Detector configuration

        Returns:
            None

        """

        sim_config_copy = self._sim_config
        sim_config_copy['Simulationsdauer'] = int(sim_config_copy['Simulationsdauer'].total_seconds())
        sim_config_copy['Hindernis'] = int(sim_config_copy['Hindernis'])
        sim_config_copy.to_csv(path_or_buf=self._path_to_results_config / 'sim_config.csv', sep=';', header=True)
        shutil.copy2(self._path_to_rsu_config, self._path_to_results_config)
        shutil.copy2(self._path_to_detector_config, self._path_to_results_config)

    def __prepare_sumo(self) -> None:
        """
        A method to prepare the SUMO simulation.

        It creates:\n
        - detector files
        - vType file
        - trip files (includes od-matrix files)
        - route file for rolling obstruction (=fat -- fahrbare Absperrtafel)
        - sumo config file

        Returns:
            None

        Raises:
            TypeError: If value for QSV is out of range.

        """

        #: Calls function to create an additional file for SUMO simulation.
        create_additional_file(path_to_sumo=self._path_to_sumo,
                               path_to_additional_file=self._path_to_additional_file,
                               path_to_edge_dump_file=self._path_to_edge_dump_file,
                               sumo_edge_dump_interval=self._sumo_edge_dump_interval
                               )

        #: Calls function to create vtype file for SUMO simulation.
        customize_vtype_file(path_to_vtypes_ref=self._path_to_vtypes_ref,
                             path_to_vtypes_new=self._path_to_vtypes,
                             tau=self._tau)

        list_trip_files: list[Path] = []  #: list containing all trip file paths

        #: Creates od-matrices for each traffic type in 'dict_traffic_types'.
        for key, value in self.dict_traffic_types.items():
            str_csv_file = 'odm_{0}.csv'.format(key)
            vtype = value
            list_od_matrix_files: list[Path] = []

            for idx, qsv in enumerate(self._qsv_sequence):
                if qsv not in self.dict_qsv_x.keys():
                    err_msg = \
                        'Unexpected value for QSV in configuration file!\nExpected:\na to f\nbut got this:\n{0}'.format(
                            list(qsv))
                    print(err_msg)
                    raise TypeError

                qsv_limits = self.dict_qsv_x[qsv]
                traffic_factor = sum(qsv_limits) / len(qsv_limits)  # calc mean value
                start_time = datetime.combine(date.today(),
                                              self._start_time) + (self._duration / len(self._qsv_sequence) * idx)
                duration = self._duration / len(self._qsv_sequence)
                str_od_file = '{0}_odm_{1}_{2}_qsv_{3}.od'.format(self.sim_id, key, idx, qsv)
                od_file_name = self._path_to_routes / str_od_file

                #: Calls function to create od-matrix file.
                create_od_matrix_file(od_matrix_file_csv=self._path_to_traffic / str_csv_file,
                                      traffic_factor=traffic_factor,
                                      vtype=vtype,
                                      output_file_name=od_file_name,
                                      start_time=start_time,
                                      duration=duration)

                list_od_matrix_files.append(od_file_name)

            #: Converts od matrices to trips.
            str_obstruction_trip_file = '{0}_trip_{1}.odtrips.xml'.format(self.sim_id, key)
            path_to_od_trip_file = self._path_to_routes / str_obstruction_trip_file
            str_list_od_files = ','.join(str(i) for i in list_od_matrix_files)

            #: Sets departure lanes for the vehicle types. Trucks have to depart on the right lane.
            if key == 'sv':  #: sv: Schwerverkehr
                depart_lane = 'first'  #: first: most right lane
            else:
                depart_lane = 'best'  #: best: SUMO chooses best lane for departure

            #: Creates command for SUMO Tool 'od2trips'. In this case it converts the od-matrices to traffic flows.
            cmd_od2trips = 'od2trips -n {0} -X never -d {1} --flow-output {2} --prefix {3}_ --departlane {4}'.format(
                str(self._path_to_taz_file),
                str(str_list_od_files),
                str(path_to_od_trip_file),
                key,
                depart_lane
            )

            list_trip_files.append(path_to_od_trip_file)  #: append trip file path to list
            os.system(cmd_od2trips)  #: execute od2trips

        #: Converts trip of rolling obstruction to route.
        if self._obstruction is True:
            try:
                self._path_to_obstruction_trips_file.resolve(strict=True)
            except FileNotFoundError:
                raise

            #: Creates command for SUMO tool 'duarouter'.
            cmd_duarouter = 'duarouter -n {0} -X never --route-files {1} --additional-files {2} -o {3}'.format(
                str(self._path_to_net_file),
                str(self._path_to_obstruction_trips_file),
                str(self._path_to_vtypes),
                str(self._path_to_odroute_file))

            #: Executes duarouter command to generate route file for rolling obstruction.
            os.system(cmd_duarouter)
            list_trip_files.append(self._path_to_odroute_file)

        #: Calls function to create SUMO config file.
        create_sumo_config_file(path_to_sumo=self._path_to_sumo,
                                path_to_net_file=self._path_to_net_file,
                                list_path_to_trip_files=list_trip_files,
                                sumo_start_time=self._start_time,
                                sumo_duration=self._duration,
                                sumo_step_length=self._sumo_step_length,
                                sumo_action_step_length=self._sumo_action_step_length,
                                sumo_max_depart_delay=self._sumo_max_depart_delay,
                                sumo_fcd_output_interval=self._sumo_fcd_output_interval,
                                sumo_use_tls=self._use_tls,
                                path_to_sumo_config_file=self._path_to_sumo_config_file,
                                path_to_fcd_output_file=self._path_to_fcd_output_file,
                                path_to_additional_file=self._path_to_additional_file,
                                path_to_taz_file=self._path_to_taz_file,
                                path_to_vtypes_file=self._path_to_vtypes,
                                path_to_gui_view=self._path_to_gui_view_file,
                                path_to_poly_file=self._path_to_poly_file)

    def __prepare_omnet(self) -> None:
        """
        A method to prepare the OMNeT simulation.

        It creates:\n
        - services.xml
        - omnet.ini

        Returns:
            None

        """
        #: Calls function to create services.xml.
        create_services_file(v2x_rate=self._v2x_rate,
                             path_to_service_file=self._path_to_services_file)
        
        #: Calls function to create omnet.ini.
        create_omnetpp_file(sim_duration=self._duration,
                            com_range=self.radius_rsu,
                            path_to_rsu_config_file=self._path_to_rsu_config,
                            list_seeds=random.sample(range(1, 9999), self._num_repeat),
                            path_to_sumo_config_file=self._path_to_sumo_config_file,
                            path_to_service_file=self._path_to_services_file,
                            path_to_omnetpp_file=self._path_to_omnetpp_file_long,
                            path_to_net_file=self._path_to_net_file,
                            path_to_results_omnet=Path.relative_to(self._path_to_results_omnet,
                                                                   self._path_to_simulation))
