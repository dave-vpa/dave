"""
Module to create the configuration file for SUMO.
"""

from pathlib import Path
from datetime import time, timedelta

str_start_config = '<configuration>\n\n'
str_end_config = '\n</configuration>\n'

str_start_input = '\t<input>\n'
str_end_input = '\t</input>\n'

str_start_output = '\n\t<output>\n'
str_end_output = '\t</output>\n'

str_start_time = '\n\t<time>\n'
str_end_time = '\t</time>\n'

str_start_processing = '\n\t<processing>\n'
str_end_processing = '\t</processing>\n'

str_start_add = '<additional>\n'
str_end_add = '</additional>\n'


def create_sumo_config_file(path_to_sumo: Path,
                            path_to_net_file: Path,
                            list_path_to_trip_files: list[Path],
                            sumo_start_time: time,
                            sumo_duration: timedelta,
                            sumo_step_length: timedelta,
                            sumo_action_step_length: timedelta,
                            sumo_max_depart_delay: timedelta,
                            sumo_fcd_output_interval: timedelta,
                            sumo_use_tls: bool,
                            path_to_sumo_config_file: Path,
                            path_to_fcd_output_file: Path,
                            path_to_additional_file: Path,
                            path_to_taz_file: Path,
                            path_to_vtypes_file: Path,
                            path_to_gui_view: Path,
                            path_to_poly_file: Path
                            ) -> None:
    """
    A function to create the SUMO configuration file.

    Args:
        path_to_sumo: Path to SUMO folder
        path_to_net_file: Path to net file
        list_path_to_trip_files: List with paths to trip files
        sumo_start_time: Start time of SUMO simulation
        sumo_duration: Duration of SUMO simulation
        sumo_step_length: step length of SUMO simulation
        sumo_action_step_length: action step length of SUMO simulation
        sumo_max_depart_delay: max. departure delay of vehicles in SUMO simulation
        sumo_fcd_output_interval: logging interval for fcd output
        sumo_use_tls: flag for use of trafic lights in SUMO simulation
        path_to_sumo_config_file: Path to SUMO configuration file
        path_to_fcd_output_file: Path to FCD output file
        path_to_additional_file:
        path_to_taz_file: Path to traffic assignment zone file
        path_to_vtypes_file: Path to vehicle type definition file
        path_to_gui_view: Path to GUI configuration file
        path_to_poly_file: Path to ploygon file

    Returns:
        None

    """
    #: create relative paths
    rel_path_to_net_file = '..' / Path.relative_to(path_to_net_file, path_to_sumo)
    rel_path_to_route_file_list = ['..' / Path.relative_to(i, path_to_sumo) for i in list_path_to_trip_files]
    rel_path_to_fcd_output_file = '..' / Path.relative_to(path_to_fcd_output_file, path_to_sumo)
    rel_path_to_taz_file = '..' / Path.relative_to(path_to_taz_file, path_to_sumo)
    rel_path_to_vtypes_file = '..' / Path.relative_to(path_to_vtypes_file, path_to_sumo)
    rel_path_to_gui_view_file = '..' / Path.relative_to(path_to_gui_view, path_to_sumo)
    rel_path_to_poly_file = '..' / Path.relative_to(path_to_poly_file, path_to_sumo)
    rel_path_to_additional_file = '..' / Path.relative_to(path_to_additional_file, path_to_sumo)

    #: get start and end time of simulation
    t_start = sumo_start_time
    t_start_in_seconds = (t_start.hour * 60 + t_start.minute) * 60 + t_start.second
    t_end = t_start_in_seconds + int(sumo_duration.total_seconds())

    #: concatenate all route files to a single string
    str_traffic = ', '.join(str(i) for i in rel_path_to_route_file_list)

    #: create strings for configuration file
    str_input_net = '\t\t<net-file value = \"{0}\"/>\n'.format(str(rel_path_to_net_file))
    str_input_route = '\t\t<route-files value = \"{0}\"/>\n'.format(str_traffic)
    str_time_begin = '\t\t<begin value = \"{0}\"/>\n'.format(t_start_in_seconds)
    str_time_end = '\t\t<end value = \"{0}\"/>\n'.format(t_end)
    str_step_length = '\t\t<step-length value = \"{0}\"/>\n'.format(sumo_step_length.total_seconds())
    str_action_step_length = '\t\t<default.action-step-length value = \"{0}\"/>\n'.format(
        sumo_action_step_length.total_seconds())
    str_time_to_teleport = '\t\t<time-to-teleport value = \"{0}\"/>\n'.format(-1)
    str_max_depart_delay = '\t\t<max-depart-delay value = \"{0}\"/>\n'.format(sumo_max_depart_delay.total_seconds())
    str_use_tls = '\t\t<tls.all-off value = \"{0}\"/>\n'.format(not sumo_use_tls)
    str_output_fcd = '\t\t<fcd-output value = \"{0}\"/>\n'.format(str(rel_path_to_fcd_output_file))
    str_output_fcd_period = '\t\t<device.fcd.period value = \"{0}\"/>\n'.format(
        sumo_fcd_output_interval.total_seconds())
    str_input_additional = '\t\t<additional-files value = \"{0}, {1}, {2}, {3}\"/>\n'.format(
        str(rel_path_to_vtypes_file),
        str(rel_path_to_taz_file),
        str(rel_path_to_poly_file),
        str(rel_path_to_additional_file))
    str_gui_only = '\n\t<gui_only>\n\t\t <gui-settings-file value=\"{0}\"/>\n\t</gui_only>\n'.format(
        rel_path_to_gui_view_file)
    str_seed = '\t\t<seed value = \"{0}\"/>\n'.format(23424)

    #: concatenate strings
    str_input = str_start_input + str_input_net + str_input_route + str_input_additional + str_seed + str_end_input
    str_output = str_start_output + str_output_fcd + str_output_fcd_period + str_end_output
    str_time = str_start_time + str_time_begin + str_time_end + str_step_length + str_end_time
    str_processing = str_start_processing + str_action_step_length + str_time_to_teleport + str_use_tls + str_max_depart_delay + str_end_processing
    str_config = str_start_config + str_input + str_output + str_time + str_processing + str_gui_only + str_end_config

    #: create/open, fill and close SUMO configuration file
    with open(path_to_sumo_config_file, 'w') as f:
        f.write(str_config)
