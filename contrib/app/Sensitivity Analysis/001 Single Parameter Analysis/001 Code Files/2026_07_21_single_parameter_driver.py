"""

Summary
-------

This module is for modifying a single parameter in a single facet procress input files using incremental change

This script performs the following steps:

1. Parses through input directory to find the target dataset
2. Stores copy of the target data and its corresponding filepath
3. Performs and stores a incrimental modifications to target data based on assigned margins for sensitivity
4. Generatse a copy of the input h5 file containing the target dataset for each modification
5. Stores each modified input file in a separate output folder for the specified modification
5. Generates a corresponding ini file for each modification in the respective folder

Libraries
---------
pandas
numpy
h5py
copy
pathlib/Path
os

Examples
--------

To run the script, simply update the file paths stored as variables at the bottom of the file and run function.

                input_dir = 'C:/Users/.../input_folder'
                target_variable = "dist_optic_screen"
                target_variable_type = "m"
                output_dir = "C:/Users/.../002_output"
                naming_prefix = 'mdAAA'
                sofast_measurement = "C:/Users/.../measurement_facet.h5"
                sofast_orientation = "C:/Users/.../spatial_orientation.h5"
                sofast_camera = "C:/Users/.../camera_sofast_downsampled.h5"
                sofast_display = "C:/Users/.../display_distorted_2d.h5"
                facet_data = "C:/Users/.../Facet_NSTTF.json"
                sofast_calibration = "C:/Users/.../image_calibration.h5"
                input_ini_template_path = "C:/Users/.../ini_template.ini"
                measurement_id = "test123"
                post_process_id = "test1234"

                singleparametersa(
                    input_dir=Path(input_dir),
                    target_variable=target_variable,
                    targetvartype=target_variable_type,
                    output_dir=output_dir,
                    naming_prefix=naming_prefix,
                    measurement=sofast_measurement,
                    orientation=sofast_orientation,
                    camera=sofast_camera,
                    display=sofast_display,
                    calibration=sofast_calibration,
                    facet=facet_data,
                    measurement_id=measurement_id,
                    post_process_id=post_process_id,
                    input_ini_template_path=input_ini_template_path,
                )


Expected Outputs
----------------
This code will save a resulting output folder in the output directory for each modification and will consist of:

    sa_mdAAAn01 - Subfolder containing the modified h5 input file and corresponding ini file
        sa_mdAAAn01.h5 - an H5 file in subfolder containing a single incrimental modification of the parameter of interest
        sa_mdAAAn01.ini - an INI file in subfolder containing an updated filepath for the modified h5 input fle.

    Note: xxx refers to the row number in scenario deck for which all modified input files and .ini files were generated.


AI Acknowledgement
------------------
SandiaAI was used to faciliate code development and docstring documentation.

"""

####### IMPORT LIBRARIES ######

import pandas as pd
import numpy as np
import h5py
import copy
from pathlib import Path
import copy
import os
import csv
import subprocess
from tqdm import tqdm

####### HELPER FUNCTIONS ######
#### DO NOT MODIFY


def increment_change(lower_limit=-100, upper_limit=100, steps=1, naming_prefix='', unit_sig=3):
    """

    Summary
    -------

    This helper function performes the following:
    - calculates a function to calculate new value for a numeric variable based on predetermined value range and increment size
    - generates a dictonary of key-value pairs for all incremental changes consisting of:
        - key: a name for the value based on a predetermined naming convention for the incriment change
        - value: a numeric function for a new value to replace the old value

    ----------
    lower_limit : int, optional
        by default -100
        The negative margin of the range of values to be used for incrimental calculation
    upper_limit : int, optional
        by default 100
        The positive margin of the range of values to be used for incrimental calculation
    steps : int, optional
        by default 1
        The increment size to be added in the numeric calculation of the new value
    naming_prefix : _str_, optional
        by default None
        An optional prefix string text to be incorporated into dictionary key for classification purposes

    Returns
    -------
    _dictionary_
        A dictionary of names and functions to be used for calculating new values of a numeric variable.
    """
    modifications = {}

    def format_float_key(value, prefix, unit_sig=3):
        abs_val = abs(value)
        int_part = int(abs_val)
        decimal_part = abs_val - int_part

        # Extract decimal digits as string without leading '0.'
        # For example, 0.4 -> '4', 0.45 -> '45', 0.456 -> '456'
        decimal_str = f"{decimal_part:.{unit_sig}f}".split('.')[1]  # 3 signficance digits

        # Pad integer part if less than 100
        if int_part < 10:
            int_str = f"{int_part:03d}"
        elif int_part < 100:
            int_str = f"{int_part:02d}"
        else:
            int_str = str(int_part)

        sign = 'n' if value < 0 else 'p'
        return f'sa_{prefix}{sign}{int_str}_{decimal_str}'

    if any(isinstance(x, float) for x in (lower_limit, upper_limit, steps)):
        i = lower_limit
        while i <= upper_limit + 1e-12:
            # Define the function capturing the current i value correctly using default argument
            my_function = lambda x, increment=i: x + increment

            if abs(i) < 1e-12:
                key = f'sa_{naming_prefix}0b000'  # zero-padded for single digit negative
            else:
                key = format_float_key(i, naming_prefix, unit_sig)
            modifications[key] = my_function
            i += steps
    else:
        for i in range(lower_limit, upper_limit + 1, steps):
            # Define the function capturing the current i value correctly using default argument
            my_function = lambda x, increment=i: x + increment
            if i == 0:
                key = f'sa_{naming_prefix}0b000'  # zero-padded for single digit negative
            elif i < 0:
                abs_i = abs(i)
                if abs_i < 10:
                    key = f'sa_{naming_prefix}n{abs_i:03d}'  # zero-padded for single digit negative
                elif abs_i < 100:
                    key = f'sa_{naming_prefix}n{abs_i:02d}'
                else:
                    key = f'sa_{naming_prefix}n{abs_i}'
            else:
                if i < 10:
                    key = f'sa_{naming_prefix}p{i:03d}'  # zero-padded for single digit negative
                elif i < 100:
                    key = f'sa_{naming_prefix}p{i:02d}'
                else:
                    key = f'sa_{naming_prefix}p{i}'
            modifications[key] = my_function

    zero_key = f'sa_{naming_prefix}0b000'
    if zero_key not in modifications:
        modifications[zero_key] = lambda x: x
    return modifications


# testdata= {}
# fx = 5
# testmod = increment_change(-.5,.5,.2, naming_prefix='test')
# for key,func in testmod.items():
#     testdata[key] = func(fx)

# print(testdata)


def update_ini_file_by_search(
    input_ini_template_path, output_ini_file_path, updated_id, updated_process_input_file_path
):
    """

    Summary
    -------

    This helper function performs the following:
    - reads a template ini file
    - Updates to filepath for each sofast process argument with a provided new filepath
    - saves a new changes as a new ini file

    Parameters
    ----------
    input_ini_template_path : _str_
        a file path for a template ini file
    output_ini_file_path : _filepath_
        a file path for an output ini file
    updated_id : _str_
        a string variable providing assigning a new value to the experimental id of the output ini file
    updated_process_input_file_path : _dictionary_
        a dictionary of file paths as string to be assigned to sofast procoess input filepaths in ini file.

    """

    with open(input_ini_template_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            updated_lines.append(line)
            continue

        # Check if line contains '=' to separate key and value
        if '=' in line:
            key_part, sep, value_part = line.partition('=')
            key = key_part.strip()
            if key in updated_process_input_file_path:
                # Replace the value with updated_vars[key]
                new_value = str(updated_process_input_file_path[key]).replace('/', '\\')
                # Preserve original spacing around '='
                left_spaces = key_part[len(key) :]
                right_spaces = value_part[: len(value_part) - len(value_part.lstrip())]
                new_line = f"{key}{left_spaces}={right_spaces}{new_value}\n"
                updated_lines.append(new_line)
            elif key in updated_id:
                new_value = updated_id[key].replace('/', '\\')
                # Preserve original spacing around '='
                left_spaces = key_part[len(key) :]
                right_spaces = value_part[: len(value_part) - len(value_part.lstrip())]
                new_line = f"{key}{left_spaces}={right_spaces}{new_value}\n"
                updated_lines.append(new_line)
            else:
                # Key not in updated_vars, keep line as is
                updated_lines.append(line)
        else:
            # Line without '=' (unlikely for your file), keep as is
            updated_lines.append(line)

    # Write updated lines to output file
    if os.path.exists(output_ini_file_path):
        os.remove(output_ini_file_path)

    with open(output_ini_file_path, 'w') as f:
        f.writelines(updated_lines)


####### MAIN FUNCTION ######
#### DO NOT MODIFY


def singleparametersa(
    input_dir=None,
    target_variable=None,
    targetvartype=None,
    output_dir=None,
    measurement=None,
    orientation=None,
    camera=None,
    display=None,
    calibration=None,
    facet=None,
    measurement_id=None,
    post_process_id=None,
    input_ini_template_path=None,
    lower_limit=-100,
    upper_limit=100,
    steps=1,
    naming_prefix='',
):
    """

    Summary
    -------
    This function performes the following:
    - searches through H5 files in the input directory for a specified dataset
    - modifies the dataset with incremental changes and stores a copy of the modified dataset in a list
        - the increment_change() function is applied to dataset to calculate incremental changes to parameter
        - increment_change() assigns a single modification for chosen parameter and saves it as a new dataset
    - generates a new H5 file for each modification of a parameter in the dataset.
        - Modified HDF5 files are saved in subdirectories named after the modification suffix.
    - generates an INI configuration files corresponding with each newly generated H5 filem with an updated filepath.
    - returns a csv file with all the filepaths for newly generated INI files for subsequent terminal processing.


    Parameters
    ----------
    input_dir :                 pathlib.Path or str
                                File directory containing all SOFAST Process input files
    target_variable :           str
                                Substring to identify the specified dataset to be modified.
    targetvartype :             str
                                identifier for the category of H5 file in which the target dataset is to be found:
                                - Used to update filepaths in the INI file.
                                - Expected values:
                                > 'm' (measurement)
                                > 'o' (orientation)
                                > 'c' (camera)
                                or
                                > 'd' (display)
    output_dir :                pathlib.Path or str
                                Output directory where all modified HDF5 files and corresponding INI files will be saved.
    measurement :               str or pathlib.Path
                                Path or identifier for the measurement file.
                                - Used to update filepath in INI file.
    orientation :               str or pathlib.Path
                                Path or identifier for the orientation file.
                                - Used to update filepath in INI file.
    camera :                    str or pathlib.Path
                                Path or identifier for the camera file
                                - Used to update filepath in INI file.
    display :                   str or pathlib.Path
                                Path or identifier for the display file.
                                - Used to update filepath in INI file.
    calibration :               str or pathlib.Path
                                Path or identifier for the calibration file
                                - Used to update filepath in INI file.
    facet :                     str or pathlib.Path
                                Path or identifier for the facet data file.
                                - Used to update filepath in INI file.
    measurement_id :            str or int
                                Identifier for the measurement.
                                - Used to update filepath in INI file.
    post_process_id :           str or int
                                Identifier for the post-processing step, used in INI file updates.
    input_ini_template_path :   pathlib.Path or str
                                    Path to the INI template file used as a base for generating new INI files.
    lower_limit :               int, optional
                                Lower bound for incremental changes applied to the dataset values (default is -100).
    upper_limit :               int, optional
                                Upper bound for incremental changes applied to the dataset values (default is 100).
    steps :                     int, optional
                                Step size for increments between lower and upper limits (default is 1).
    naming_prefix :             str, optional
                                Prefix used in naming the modified datasets and output files (default is empty string).

    Examples
    --------
                    singleparametersa(
                        input_dir=Path("/path/to/input"),
                        target_variable="fringe_periods_x",
                        targetvartype="m",
                        output_dir=Path("/path/to/output"),
                        measurement="measurement_file.h5",
                        orientation="orientation_file.h5",
                        camera="camera_file.h5",
                        display="display_file.h5",
                        calibration="calibration_file.h5",
                        facet="facet_file.h5",
                        measurement_id="12345",
                        post_process_id="67890",
                        input_ini_template_path=Path("/path/to/template.ini"),
                        lower_limit=-10,
                        upper_limit=10,
                        steps=5,
                        naming_prefix="mdAAA"
                        )


    Raises
    ------
    StopIteration
        Raised internally to stop traversal of HDF5 datasets once the target dataset is found.
    KeyError
        If the target dataset is not found or multiple datasets match the target variable.
    ValueError
        If the target dataset's shape is unsupported (not scalar or 1D array).


    """

    # Iterate over all input file in input directory and extract dataset of interest from the h5 file.
    for h5_file in input_dir.glob("*.h5"):
        print(f"Processing file: {h5_file}")
        with h5py.File(h5_file, 'r') as f:
            data_dict = {}
            poi_input_data_path = None

            def get_dataset(name, obj):
                nonlocal data_dict, poi_input_data_path
                if isinstance(obj, h5py.Dataset) and target_variable in name:
                    print(f'{target_variable} is found in {h5_file}.')
                    data_dict[name] = obj[()]
                    poi_input_data_path = str(h5_file)
                    raise StopIteration
                else:
                    print(f'{target_variable} is not found in {h5_file}.')

            try:
                f.visititems(get_dataset)
            except StopIteration:
                pass
        if poi_input_data_path is not None:
            break
    # Define path for the target dataset
    target_path = [key for key in data_dict if target_variable in key]
    if not target_path:
        raise KeyError(f" file path for {target_variable} dataset not found")
    if len(target_path) != 1:
        raise KeyError(f"Expected exactly one dataset matching '{target_variable}'\n, found {len(target_path)}")
    target_path = target_path[0]
    original_values = data_dict[target_path]
    modifications = increment_change(lower_limit, upper_limit, steps, naming_prefix, unit_sig=3)

    inifile_pathlist = []
    # if target dataset is a 1D array
    if isinstance(original_values, np.ndarray) and original_values.ndim == 1:
        for i, row in enumerate(original_values):
            for key, modify_func in modifications.items():

                # Copy original data dict
                modified_data = data_dict.copy()  # make shallow copy of dataset
                modified_data[target_path] = original_values.copy()  # make deep copy to prevent overwrite
                modified_data[target_path][i] = modify_func(row)

                # Construct new subfolder and filename
                output_dir_path = Path(output_dir) / key
                output_dir_path.mkdir(parents=True, exist_ok=True)
                new_name = f"{key}_row{i}.h5"
                return_file_path = output_dir_path / new_name

                # Save modified data to new HDF5 file
                with h5py.File(poi_input_data_path, 'r') as f_src, h5py.File(return_file_path, 'w') as f_new:

                    def replace_dataset(name, obj):
                        if isinstance(obj, h5py.Group):
                            f_new.require_group(name)
                        elif isinstance(obj, h5py.Dataset):
                            if name == target_path:
                                f_new.create_dataset(
                                    name,
                                    data=modified_data[name],
                                    shape=obj.shape,
                                    dtype=obj.dtype,
                                    compression=obj.compression,
                                    chunks=obj.chunks,
                                    shuffle=obj.shuffle,
                                    fletcher32=obj.fletcher32,
                                    maxshape=obj.maxshape,
                                )
                            else:
                                f_src.copy(name, f_new, name)

                    f_src.visititems(replace_dataset)
                print(f"Saved modified file: {return_file_path}")

                # create and save the ini file
                updated_process_input_file_path = {
                    'file_camera': str(camera),
                    'file_orientation': str(orientation),
                    'file_display': str(display),
                    'file_facet': str(facet),
                    'file_measurement': str(measurement),
                    'file_calibration': str(calibration),
                    'dir_save_root': f'{output_dir_path}/SOFAST_Results_2_{key}_row{i}',
                }

                updated_id = {'measurement_id': measurement_id, 'post_process_id': post_process_id}

                if targetvartype == "m":
                    updated_process_input_file_path['file_measurement'] = str(return_file_path)
                elif targetvartype == "o":
                    updated_process_input_file_path['file_orientation'] = str(return_file_path)
                elif targetvartype == "c":
                    updated_process_input_file_path['file_camera'] = str(return_file_path)
                elif targetvartype == "d":
                    updated_process_input_file_path['file_display'] = str(return_file_path)

                output_dir_path.mkdir(parents=True, exist_ok=True)
                ini_file_name = f'{key}_row{i}.ini'
                ini_file_path = output_dir_path / ini_file_name

                update_ini_file_by_search(
                    input_ini_template_path, ini_file_path, updated_id, updated_process_input_file_path
                )
                inifile_pathlist.append(ini_file_path)

    elif np.isscalar(original_values) or (isinstance(original_values, np.ndarray) and original_values.ndim == 0):
        for key, modify_func in modifications.items():
            # copy dataset
            modified_data = data_dict.copy()  # make shallow copy of dataset
            modified_data[target_path] = modify_func(original_values)

            # Construct new subfolder and filename
            output_dir_path = Path(output_dir) / key
            output_dir_path.mkdir(parents=True, exist_ok=True)
            new_name = f"{key}.h5"
            return_file_path = output_dir_path / new_name

            with h5py.File(poi_input_data_path, 'r') as f_src, h5py.File(return_file_path, 'w') as f_new:

                def replace_dataset(name, obj):
                    if isinstance(obj, h5py.Group):
                        f_new.require_group(name)
                    elif isinstance(obj, h5py.Dataset):
                        if name == target_path:
                            f_new.create_dataset(
                                name,
                                data=modified_data[name],
                                shape=obj.shape,
                                dtype=obj.dtype,
                                compression=obj.compression,
                                chunks=obj.chunks,
                                shuffle=obj.shuffle,
                                fletcher32=obj.fletcher32,
                                maxshape=obj.maxshape,
                            )
                        else:
                            f_src.copy(name, f_new, name)

                f_src.visititems(replace_dataset)
            print(f"Saved modified file: {return_file_path}")
            updated_process_input_file_path = {
                'file_camera': str(camera),
                'file_orientation': str(orientation),
                'file_display': str(display),
                'file_facet': str(facet),
                'file_measurement': str(measurement),
                'file_calibration': str(calibration),
                'dir_save_root': f'{output_dir_path}/SOFAST_Results_2_{key}',
            }
            updated_id = {'measurement_id': measurement_id, 'post_process_id': post_process_id}
            # create and save the ini file
            if targetvartype == "m":
                updated_process_input_file_path['file_measurement'] = str(return_file_path)
            elif targetvartype == "o":
                updated_process_input_file_path['file_orientation'] = str(return_file_path)
            elif targetvartype == "c":
                updated_process_input_file_path['file_camera'] = str(return_file_path)
            elif targetvartype == "d":
                updated_process_input_file_path['file_display'] = str(return_file_path)

            output_dir_path.mkdir(parents=True, exist_ok=True)
            ini_file_name = f'sa_{key}.ini'
            ini_file_path = output_dir_path / f"{ini_file_name}"

            update_ini_file_by_search(
                input_ini_template_path, ini_file_path, updated_id, updated_process_input_file_path
            )
            inifile_pathlist.append(ini_file_path)
    else:
        raise ValueError(
            f"Unsupported data shape for target variable '{target_variable}': {getattr(original_values, 'shape', type(original_values))}"
        )

    inifile_pathlist_df = pd.DataFrame(inifile_pathlist, columns=['ini_file_paths'])
    csv_path = os.path.join(output_dir, 'ini_file_paths.csv')
    inifile_pathlist_df.to_csv(csv_path, index=False)
    print(f"list of ini filepaths saved to {csv_path}")

    return inifile_pathlist


####### EXECUTION OF MAIN FUNCTION ######
##### Update filepaths for the following variables #####

# update parameter of interest
target_variable = 'dist_optic_screen'
target_variable_type = "m"

# update file naming prefix. see documentation on file naming convention and parameter key list
naming_prefix = 'mdAAA'

# update filepath for your scenario deck. File must be saved as csv.
input_dir = 'C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input'

# update filepath for your output directory. All modified h5 files and related generated .ini files will be stored here.
output_dir = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/002_output"

# update filepath for the unmodified h5 measurment input file to be used to generated newly modified h5 input file.
sofast_measurement = (
    "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/measurement_facet.h5"
)

# update filepath for the unmodified h5 orientation input file to be used to generated newly modified h5 input file.
sofast_orientation = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/spatial_orientation.h5"

# update filepath for the unmodified h5 camera input file to be used to generated newly modified h5 input file.
sofast_camera = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/camera_sofast_downsampled.h5"

# update filepath for the unmodified h5 display input file to be used to generated newly modified h5 input file.
sofast_display = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/display_distorted_2d.h5"

# update filepath for the unmodified .json facet data file. This is only needed for generating filepath for facet data in .ini file.
facet_data = (
    "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/Facet_NSTTF.json"
)

# update filepath for the unmodified h5 calibration file. This is only needed for generating filepath for facet data in .ini file.
sofast_calibration = (
    "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/001_input/image_calibration.h5"
)

# update filepath for your empty .ini file to be used to generate all new .ini file for each row-wise modifications.
input_ini_template_path = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/004_ini_files/ini_template_2_alan.ini"

# update relevant identification information for the .ini files.
measurement_id = "20260721"
post_process_id = "dist_optic_screen"


# after updating file paths above, run the function below to generate new input files, .ini files, and a .ini filepath list
inifile_pathlist = singleparametersa(
    input_dir=Path(input_dir),
    target_variable=target_variable,
    targetvartype=target_variable_type,
    output_dir=output_dir,
    naming_prefix=naming_prefix,
    measurement=sofast_measurement,
    orientation=sofast_orientation,
    camera=sofast_camera,
    display=sofast_display,
    calibration=sofast_calibration,
    facet=facet_data,
    measurement_id=measurement_id,
    post_process_id=post_process_id,
    input_ini_template_path=input_ini_template_path,
    lower_limit=-0.05,
    upper_limit=0.05,
    steps=0.001,
)


##### Function to process INI Files in SOFAST Process #############


def ini_terminal_execution(inifile_pathlist, python_executable_pathlist, single_facet_process_pyfile):
    for file_path in tqdm(inifile_pathlist, desc="SA_Progress"):
        file_path = Path(file_path)
        python_executable = rf"{python_executable_pathlist}"
        cmd = [python_executable, single_facet_process_pyfile, "--verbose", "-s", file_path]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Successfully processed {file_path}")
            print("Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error processing {file_path}")
            print("Error output:", e.stderr)


### PROCESS single INI File in SOFAST Process - Alan's updated INI settings file used as template ###

## Testing Default INI File -- no parameter changes ##

inipath = [
    "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/002_output/sa_mdAAAn000_001/sa_sa_mdAAAn000_001.ini"
]
ini_terminal_execution(
    inifile_pathlist=inipath,
    python_executable_pathlist="C:/Users/nichowd/Code/env_310_OpenCSP/Scripts/python.exe",
    single_facet_process_pyfile="C:/Users/nichowd/Code/OpenCSP/example/sofast_fringe/single_facet/example_process_single_facet.py",
)

print("ini_terminal_execution compeleted")


# ### PROCESS all INI File in SOFAST Process ###
# ## Testing Default INI File -- no parameter changes ##
# # the following code will process the SOFAST process file using each .ini file in the pathlist.
# for file_path in inifile_pathlist:
#     file_path = Path(file_path)
#     python_executable = r"C:/Users/nichowd/Code/env_310_OpenCSP/Scripts/python.exe"
#     cmd = [
#         python_executable,
#         "C:/Users/nichowd/Code/OpenCSP/example/sofast_fringe/single_facet/example_process_single_facet.py",
#         "--verbose",
#         "-s",
#         file_path,
#     ]
#     try:
#         result = subprocess.run(cmd, check=True, capture_output=True, text=True)
#         print(f"Successfully processed {file_path}")
#         print("Output:", result.stdout)
#     except subprocess.CalledProcessError as e:
#         print(f"Error processing {file_path}")
#         print("Error output:", e.stderr)
