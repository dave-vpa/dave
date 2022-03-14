"""
Module to create the (V2X) Services file for OMNeT.
"""

from pathlib import Path

str_encoding = '<?xml version="1.0" encoding="UTF-8"?>\n'
str_start_config = '<services>\n'
str_end_config = '</services>'
str_start_service = '\t<service type="artery.application.CaService">\n'
str_end_service = '\t</service>\n'
str_listener_port = '\t\t<listener port="2001" />\n'
str_start_filter = '\t\t<filters>\n'
str_end_filter = '\t\t</filters>\n'


def create_services_file(v2x_rate: float,
                         path_to_service_file: Path
                         ) -> None:
    """
    A function to create the services.xml file for OMNeT.

    Args:
        v2x_rate: V2X equipment rate
        path_to_service_file: Path to the services file

    Returns:
        None

    """
    str_penetration_rate = f'\t\t\t<penetration rate="{v2x_rate:0.4f}" />\n'

    list_services_str: list[str] = [str_encoding, str_start_config, str_start_service, str_listener_port,
                                    str_start_filter, str_penetration_rate, str_end_filter, str_end_service,
                                    str_end_config]

    # create/open, file and close output file
    with open(path_to_service_file, 'w') as f:
        f.write(''.join(list_services_str))
