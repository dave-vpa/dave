"""
Module to create the OD matrix files as .od-files.
"""

from pathlib import Path
from datetime import timedelta, datetime
import pandas as pd

od_matrix_duration = 3600   #: input OD matrix files (.csv) are designed for this time duration


def create_od_matrix_file(od_matrix_file_csv: Path,
                          traffic_factor: float,
                          vtype: int,
                          output_file_name: Path,
                          start_time: datetime,
                          duration: timedelta) -> None:
    """
    A function to create OD matrix files for SUMO.

    Args:
        od_matrix_file_csv (Path): Path to OD matrix definition.
        traffic_factor (float): Multiplication factor for traffic.
        vtype (int): vType for this OD matrix.
        output_file_name (Path): Filename for the generated SUMO OD matrix file.
        start_time (datetime): Begin of traffic.
        duration (timedelta): Duration of traffic.

    Returns:
        None

    Raises:
        FileNotFoundError: If OD matrix .csv file is not found.

    """

    #: define variables
    format_info = '$OM;D2'
    end_time = (start_time + duration).time()

    #: check if file exists
    try:
        od_matrix_file_csv.resolve(strict=True)
    except FileNotFoundError:
        raise

    with open(od_matrix_file_csv, newline='') as f:
        od_matrix = pd.read_csv(f, sep=';')

    #: calculate time factor (input od matrix is designed for one hour)
    time_factor = duration.total_seconds() / od_matrix_duration

    #: generate output string
    front_text = f"{format_info}\n" \
                 f"*vehicle type\n" \
                 f"{vtype}\n" \
                 f"*from-time to-time\n" \
                 f"{start_time.hour:02d}.{start_time.minute:02d}\t{end_time.hour:02d}.{end_time.minute:02d}\n" \
                 f"*factor\n{traffic_factor:0.2f}\n\n"

    list_od_matrix: list[str] = []
    for index, row in od_matrix.iterrows():
        str_matrix_line = f"\t {row['from']} " \
                          f"\t {row['to']} " \
                          f"\t {int(row['num'] * time_factor)}\n"
        list_od_matrix.append(str_matrix_line)

    str_od_matrix = ''.join(list_od_matrix)

    #: open/create, fill and close OD matrix file
    with open(output_file_name, 'w') as f:
        f.write(front_text + str_od_matrix)
