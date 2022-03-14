"""
Module to create the .ini-file for OMNeT/Artery.
"""

from pathlib import Path
import sumolib
import pandas as pd
from datetime import timedelta

dict_rsu_config = {
    'rsuID': [0, str],
    'lon': [1, float],
    'lat': [2, float],
}


def get_rsu_config(path_to_rsu_config: Path) -> pd.DataFrame:
    """
    A function to get the configuration for RSUs.

    Args:
        path_to_rsu_config: Path to RSU configuration file (.csv-file).

    Returns:
        DataFrame with configurations ('rsuID', 'lon', 'lat') for RSUs.

    Raises:
        FileNotFoundError: If no configuration file is found.
        NameError: If columns in the configuration are not named as expected.

    """
    #: check if files exist
    try:
        path_to_rsu_config.resolve(strict=True)
    except FileNotFoundError:
        raise

    #: read configuration
    with open(path_to_rsu_config, newline='') as f:
        df_rsu_config = pd.read_csv(f, sep=';')

    #: check if config contains only expected columns
    try:
        if not list(dict_rsu_config.keys()) == list(df_rsu_config.keys()):
            raise NameError
    except NameError:
        err_msg = \
            'Columns in RSU configuration file are not named as expected!\nExpected:\n{0}\nbut got this:\n{1}'.format(
                list(dict_rsu_config.keys()),
                list(df_rsu_config.keys()))
        print(err_msg)
        raise

    return df_rsu_config


def convert_lon_lat_2_xy_omnet(lon_rsu: float, lat_rsu: float, path_2_net: str) -> [float, float]:
    """
    Function to convert geo coordinates to OMNeT++ coordinates.

    Converts [lon, lat] to [x, y].

    [x, y] coordinates in SUMO and OMNeT are not the same!!

    Args:
        lon_rsu (float): lon coordinate of RSU
        lat_rsu (float): lat coordinate of RSU
        path_2_net (str): path to sumo net file

    Returns:
        [x,y] as RSU coordinates for OMNeT++
    """
    net = sumolib.net.readNet(path_2_net)
    conv_bound_x_min, conv_bound_y_min, conv_bound_x_max, conv_bound_y_max = net.getBoundary()
    net_offset_x, net_offset_y = net.getLocationOffset()

    #: convert RSU coordinates to SUMO coordinates
    x_rsu_sumo, y_rsu_sumo = net.convertLonLat2XY(lon=lon_rsu,
                                                  lat=lat_rsu,
                                                  rawUTM=True)

    #: convert SUMO coordinates to Omnet++ coordinates
    x_rsu_omnet = x_rsu_sumo - conv_bound_x_min + net_offset_x
    y_rsu_omnet = -(y_rsu_sumo - conv_bound_y_max + net_offset_y)

    return x_rsu_omnet, y_rsu_omnet


def create_omnetpp_file(sim_duration: timedelta,
                        com_range: int,
                        list_seeds: list,
                        path_to_rsu_config_file: Path,
                        path_to_sumo_config_file: Path,
                        path_to_service_file: Path,
                        path_to_omnetpp_file: Path,
                        path_to_net_file: Path,
                        path_to_results_omnet: Path
                        ) -> None:
    """
    A function to create the OMNeT ini file.

    Args:
        sim_duration: Duration of simulation
        com_range: Communication distance
        list_seeds: List with seeds for random number generator; used for V2X vehicle equipment
        path_to_rsu_config_file: Path to RSU configuration file
        path_to_sumo_config_file: Path to SUMO configuration file
        path_to_service_file: Path to service.xml file containing the V2X-rate
        path_to_omnetpp_file: Path to OMNeT ini file
        path_to_net_file: Path to net file
        path_to_results_omnet: Path to OMNeT results

    Returns:
        None

    """

    str_seeds = ', '.join(['%.0f'] * len(list_seeds)) % tuple(list_seeds)
    df_rsu_config = get_rsu_config(path_to_rsu_config=path_to_rsu_config_file)
    list_rsu_strings = []

    for index, rsu_config in df_rsu_config.iterrows():
        rsu_id = rsu_config[0]
        rsu_lon = float(rsu_config[1].replace(',', '.'))
        rsu_lat = float(rsu_config[2].replace(',', '.'))

        rsu_x, rsu_y = convert_lon_lat_2_xy_omnet(lon_rsu=rsu_lon,
                                                  lat_rsu=rsu_lat,
                                                  path_2_net=str(path_to_net_file))

        list_rsu_strings.append('*.rsu[{0}].mobility.initialZ = 0m\n'.format(index))
        list_rsu_strings.append('*.rsu[{0}].mobility.initialX = {1:0.2f}m\n'.format(index, rsu_x))
        list_rsu_strings.append('*.rsu[{0}].mobility.initialY = {1:0.2f}m\n'.format(index, rsu_y))
        list_rsu_strings.append('*.rsu[{0}].middleware.RsuCALog.outputDirectory ='
                                ' "{1}_"\n\n'.format(index, path_to_results_omnet / rsu_id))

    list_str_omnetpp: list[str] = []
    list_str_omnetpp.append('[General]\n')
    list_str_omnetpp.append('network = artery.envmod.World\n')
    list_str_omnetpp.append('sim-time-limit = {0}s\n'.format(int(sim_duration.total_seconds())))
    list_str_omnetpp.append('debug-on-errors = true\n')
    list_str_omnetpp.append('print-undisposed = true\n')
    list_str_omnetpp.append('cmdenv-express-mode = true\n')
    list_str_omnetpp.append('**.scalar-recording = false\n')
    list_str_omnetpp.append('**.vector-recording = false\n')
    list_str_omnetpp.append('**.middleware.datetime = "2021-01-08 12:00:00"\n')
    list_str_omnetpp.append('*.traci.core.version = -1\n')
    list_str_omnetpp.append('*.traci.launcher.typename = "PosixLauncher"\n')
    list_str_omnetpp.append(
        '*.traci.launcher.sumocfg = "{0}"\n'.format(Path('sumo') / 'config' / path_to_sumo_config_file.name))
    list_str_omnetpp.append('num-rngs = 2\n')
    list_str_omnetpp.append('*.traci.mapper.rng-0 = 1\n')
    list_str_omnetpp.append('seed-1-mt = ${{seed={0}}}\n'.format(str_seeds))
    list_str_omnetpp.append('*.traci.mapper.typename = "traci.MultiTypeModuleMapper"\n')
    list_str_omnetpp.append('*.traci.mapper.vehicleTypes = xmldoc("vehicles.xml")\n')
    list_str_omnetpp.append('*.numRoadSideUnits = {0}\n'.format(len(df_rsu_config)))
    list_str_omnetpp.append('*.rsu[*].middleware.services = xmldoc("services-rsu.xml")\n')
    list_str_omnetpp.append('*.rsu[*].middleware.RsuCa.reception.result-recording-modes = all\n\n')
    list_str_omnetpp.append(''.join(list_rsu_strings))
    list_str_omnetpp.append('*.radioMedium.rangeFilter = "communicationRange"\n')
    list_str_omnetpp.append('*.node[*].wlan[*].typename = "VanetNic"\n')
    list_str_omnetpp.append('*.node[*].wlan[*].radio.channelNumber = 180\n')
    list_str_omnetpp.append('*.node[*].wlan[*].radio.carrierFrequency = 5.9 GHz\n')
    list_str_omnetpp.append('*.node[*].wlan[*].radio.transmitter.communicationRange = {0}m\n'.format(com_range))
    list_str_omnetpp.append('*.node[*].middleware.updateInterval = 0.1s\n')
    list_str_omnetpp.append('*.node[*].middleware.services = xmldoc("{0}")\n'.format(path_to_service_file.name))

    #: create/open, file and close output file
    with open(path_to_omnetpp_file, 'w') as f:
        f.write(''.join(list_str_omnetpp))
