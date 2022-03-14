"""
Module to create an additional file for SUMO.
"""

from pathlib import Path
from datetime import timedelta

str_start_additional = '<additional>\n\n'
str_end_additional = '\n</additional>\n'


def create_additional_file(path_to_sumo: Path,
                           path_to_additional_file: Path,
                           path_to_edge_dump_file: Path,
                           sumo_edge_dump_interval: timedelta
                           ) -> None:
    """
    A function to create the SUMO configuration file.

    Args:
        path_to_sumo: Path to SUMO folder
        path_to_additional_file:
        path_to_edge_dump_file: Path to edge dump file
        sumo_edge_dump_interval:

    Returns:
        None

    """

    #: create relative paths
    rel_path_to_edge_dump_file = '..' / Path.relative_to(path_to_edge_dump_file, path_to_sumo)

    str_edge_dump = '\t<edgeData id=\"{0}\" freq=\"{1}" vTypes=\"{2}" file=\"{3}\" excludeEmpty=\"{4}\"/>\n'.format(
        'mesurement',
        sumo_edge_dump_interval.total_seconds(),
        '5 9',
        str(rel_path_to_edge_dump_file),
        'true')

    str_additional = str_start_additional + str_edge_dump + str_end_additional

    #: create/open, fill and close SUMO configuration file
    with open(path_to_additional_file, 'w') as f:
        f.write(str_additional)
