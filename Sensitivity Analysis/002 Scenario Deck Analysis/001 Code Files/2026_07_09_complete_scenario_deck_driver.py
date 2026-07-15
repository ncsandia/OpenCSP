"""

Summary
-------

This module is for modifying single facet procress input files using a scenario deck file.

This script performs the following steps:

1. Loads and validates scenario deck csv file.
2. Compiles modifications from scenario deck by row into a set of dictionary for each input file.
3. Extracts the desired dataset and element to be modified from the input files into a temporary dictionary.
4. Replaces old value in the extracted dataset with new values found in the dictionaries of modificiations
5. Creates copies of the input file and replace datasets with the modified datasets
6. Saves the newly modified input file in an output directory inside a folder corresponding with the type of input file.
7. Modifies a template .ini file to create a new .ini file that includes all unmodified and modified input filepaths
    - This ini file is to be processed using single facet process file.

Libraries
---------
pandas
h5py
copy
pathlib/Path
collections/defaultdict
os

Examples
--------
To run the script, simply update the file paths stored as variables at the bottom of the file and run function.

                scenario_deck_file_path = 'C:/Users/.../scenario_deck.csv'
                output_dir = "C:/Users/.../002_output"
                sofast_measurement = "C:/Users/.../measurement_facet.h5"
                sofast_orientation = "C:/Users/.../spatial_orientation.h5"
                sofast_camera = "C:/Users/.../camera_sofast_downsampled.h5"
                sofast_display = "C:/Users/.../display_distorted_2d.h5"
                facet_data = "C:/Users/.../Facet_NSTTF.json"
                sofast_calibration = "C:/Users/.../image_calibration.h5"
                input_ini_template_path = "C:/Users/.../ini_template.ini"
                measurement_id = "test123"
                post_process_id = "test1234"

                scenario_deck_input_and_ini_file_update(
                    scenario_deck_file_path,
                    output_dir,
                    sofast_measurement,
                    sofast_orientation,
                    sofast_camera,
                    sofast_display,
                    calibration,
                    facet_data,
                )

                scenario_deck_input_and_ini_file_update()


Expected Outputs
----------------
This code will save the resulting output files to the output directory in the following subfolders:

    xxx_camera - Subfolder containing the modified h5 input file corresponding to the camera
    xxx_display - Subfolder containing the modified h5 input file corresponding to the display
    xxx_measurement - Subfolder containing the modified h5 input fle corresponding to measurement
    xxx_orientation - Subfolder containing the modified h5 input file corresponding to the orientation
    xxx_updated_ini_file - Subfolder containing a generated ini file containing
        file id, filepaths for unmodified and modified input files, and output directory for sofastprocess.

    Note: xxx refers to the row number in scenario deck for which all modified input files and .ini files were generated.

AI Acknowledgement
------------------
SandiaAI was used to faciliate code development and docstring documentation.

"""

####### IMPORT LIBRARIES ######

import pandas as pd
import h5py
import copy
from pathlib import Path
import copy
from collections import defaultdict
import os

####### HELPER FUNCTIONS ######
#### DO NOT MODIFY


def read_and_validate_csv(path):
    """
    Summary
    -------

    This helper function performs the following:
    - reads filepath as a .csv file and transforms it into a dataframe for subsequent manipulations

    Parameters
    ----------
    path : _str_
        a string text of the scenario deck .csv filepath

    Returns
    -------
    Pandas DataFrame
        The csv filepath is converted and returned as a dataframe.
    """
    try:
        df = pd.read_csv(path)
        if isinstance(df, pd.DataFrame):
            return df
        else:
            print("Error: The file was read but is not a valid DataFrame.")
            return None
    except FileNotFoundError:
        print(f"Error: The file at path '{path}' was not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file at path '{path}' is empty.")
        return None
    except pd.errors.ParserError:
        print(f"Error: The file at path '{path}' could not be parsed as CSV.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def parse_reference(ref_str):
    """
    Summary
    -------

    This helper function is used to parse array entry to :
    - identify dataset inside input file and store it as a variable
    - identify the row index for the respective dataset if it is a 1D array and store it as a variable
    - identify the row and column index for the respective dataset if it is a 2D array and store it as a variable

    Parameters
    ----------
    ref_str : _array element_
        The reference string refers to the specific array element to be parsed to generate two or three variables.

    Returns
    -------
    dataset_name: _str_
        a string variable storing the name of the dataset to be accessed for subsequent manipulation.
    row_idx: _int_
        a integer variable storing the name of the row index of 1D or 2D array.
    col_idx: _int_
        a integer variable storing the name of the column index of a 2D array.

    """
    split_pos = ref_str.find('[')
    dataset_name = ref_str[:split_pos]
    index_part = ref_str[split_pos:].strip('[]')

    if ',' in index_part:
        # 2D indexing
        indices = index_part.split(',')
        row_idx = int(indices[0])
        col_idx = int(indices[1])
        return dataset_name, row_idx, col_idx
    else:
        # 1D indexing
        row_idx = int(index_part)
        return dataset_name, row_idx, None  # Use None for col_idx when 1D


def replace_element(dataset_array, row_idx, col_idx, updated_value):
    """
    Summary
    -------

    This helper function is used to replace element in specified dataset with a new value.


    Parameters
    ----------
    dataset_array : _array_
        A variable representing the array of the dataset being modified.
    row_idx : _int_
        the row index of the element in a 1D or 2D array to be modified.
    col_idx : _int_
        the column index of the element in a 2D array to be modified.
    updated_value : _type_
        the new value that be used in place of the old value in the modified element.


    Returns
    -------
    _array_
        The function returns a new dataset array containing the modified value for a specified element.


    """
    if col_idx is None:
        old_value = dataset_array[row_idx]
        dataset_array[row_idx] = updated_value
        print(f"Replaced element at [{row_idx}] from {old_value} to {updated_value}")
    else:
        old_value = dataset_array[row_idx, col_idx]
        dataset_array[row_idx, col_idx] = updated_value
        print(f"Replaced element at [{row_idx},{col_idx}] from {old_value} to {updated_value}")
    return dataset_array


def modifications_list_per_row(df, sofastarg=None):
    """

    Summary
    -------

    This helper function stores all specified modification into a a list of dictionaries.


    Parameters
    ----------
    df : _array_
        An array of the dataset that is referenced for all modification in a list of dictionaries
    sofastarg : _str_, optional
        by default None
        If specified, a subset of the modifications will be compiled into a list of dictionaries for
        a specific corresponding input file.
        Arguments:
        - "m" : Only modifications for dataset in the measurement input file are compiled
        - "o" : Only modifications for dataset in the orientation input file are compiled
        - "c" : Only modifications for dataset in the camera input file are compiled
        = "d" : Only modifications for dataset in the display input file are compiled

    Returns
    -------
    all modified list: _list_
        A list of dictionaries containing key-value paired information for each modification, including:
        - the input file
        - the dataset within input file
        - element location (row and column index)
        - a new value for the element to replace the previous value


    """
    all_mod_lists = []
    for row in df.itertuples():
        # skip the first two rows which are headerlines, parameter names, and ...
        if row.Index < 2:
            continue
        master_mod_list = []
        for col in df.columns:
            target_input_file = col
            target_data = df.at[0, col]
            parname = df.at[1, col]
            col_index = df.columns.get_loc(col)
            updated_value = row[col_index + 1]
            print(target_input_file, target_data, parname, updated_value)  # LEONIDAS do we need this?
            target_dataset, r_idx, c_idx = parse_reference(target_data)
            if sofastarg is None or sofastarg in col:
                master_mod_list.append(
                    {
                        'parname': parname,
                        'target_input_file': target_input_file,
                        'target_dataset': target_dataset,
                        'r_idx': r_idx,
                        'c_idx': c_idx,
                        'updated_value': updated_value,
                    }
                )
            # else:
            #    print("the file specification is not found in directory")
        all_mod_lists.append(master_mod_list)
    return all_mod_lists


def newh5filename(master_mod_list, parname_key='parname', value_key='updated_value', prefix_key='target_input_file'):
    """

    Summary
    -------

    This helper function provides a file name for the output file containing all updated modifications for the input file.

    Parameters
    ----------
    master_mod_list : _list_
        a list of dictionaries referencing all row-wise modifications to be made to input files
    parname_key : str, optional
        by default 'parname'
        This is a key-value pair in each dictionary item for each modification that
        - Takes the 3-letter reference for the dataset and parameter that is modified.
        - Is included in the file naming function to provide insight into which parameter and dataset is being modified.
    value_key : str, optional
        by default 'updated_value'
        This is a key-value pair in each dictionary item for each modification that
        - Takes provides a the new value for an element of a dataset to be modified.
        - Is included in the file naming function to provide insight into the value of the parameter and dataset that is modified.
    prefix_key : str, optional
        by default 'target_input_file'
        This is a string varialbe referencing the input file for each dictionary item for each modification.
        - This provides a reference for which input file is being modified.
        - Is included in the file naming function to distinguished with so fast argument input file is modified.
        - Options of prefix will include:
            - "m" - referencing measurement input file
            - "o" - referencing orientation input file
            - "c" - referencing camera input file
            - "d" - referencing display input file

    Returns
    -------
    final_strin g: _str_
        A string variable that provides a name to be used for an output file for each row-wise compiled modification of the input file.
    """
    # Extract the prefix from the first dictionary
    prefix = str(master_mod_list[0][prefix_key]) if master_mod_list else ''

    # Extract parnames and updated_values
    parnames = [str(mod[parname_key]) for mod in master_mod_list]
    values = [str(mod[value_key]) for mod in master_mod_list]

    # Join each pair with underscore
    row_strings = [f"{p}_{v}" for p, v in zip(parnames, values)]

    # Join all pairs with underscore and prepend the prefix
    final_string = f"{prefix}_" + '_'.join(row_strings) if prefix else '_'.join(row_strings)

    print(f"Generated filename string: {final_string}")
    return final_string


def get_data_for_mods(poi_input_data_path, master_mod_list):
    """

    Summary
    -------

    This helper function performs the following:
    - finds dataset from input file that matches the dataset listed in the list of dictionaries of modifications.
    - makes a copy of the dataset and stores into a dictionary.

    Parameters
    ----------
    poi_input_data_path : _str_

    master_mod_list : _list_

    Returns
    -------

    data_dict: _dictionary_
        A dictionary of datasets that is copied from the input file.
    """
    with h5py.File(poi_input_data_path, 'r') as f:
        data_dict = {}
        dataset_names = set(dataset_dict['target_dataset'] for dataset_dict in master_mod_list)

        def get_dataset(name, obj):
            nonlocal data_dict
            if isinstance(obj, h5py.Dataset):
                for dataset_name in dataset_names:
                    if dataset_name in name:
                        print(f'{dataset_name} is found in h5 file.')
                        if name not in data_dict:
                            data_dict[name] = obj[()]

        f.visititems(get_dataset)
    return data_dict


def make_and_save_mods(poi_input_data_path, master_mod_list, data_dict, output_dir, folder_name, return_flag=None):
    """

    Summary
    -------

    This helper function does the following:
    - makes copy of the dictionary of dataset called data_dict2 to make and save all modification without affecting original files
    - initialize a dictionary of list that will group modification dictionaries by keys corresponding to paths of datasets to be modified.
    - iterates over each dataset in the list of modifications, matches dataset name from modification list to the dataset in data_dict2
    - cumaltively applies modifications to dataset in data_dict2 corresponding to the list of modifications using a helper function, replace_element()
    - generates an output file that includes all desired modification of the input file

    Returns
    -------
    new_file_path : _filepath_
        Generates a filepath for a new output file that includes all modifications desired for a corresponding input file.

    """

    data_dict2 = copy.deepcopy(data_dict)

    # Group modifications by target dataset path
    mods_by_path = defaultdict(list)
    for dataset_dict in master_mod_list:
        target_dataset_name = dataset_dict['target_dataset']
        target_path = None
        for key in data_dict2.keys():
            if target_dataset_name in key:
                target_path = key
                break
        if target_path is None:
            print(f"Dataset {target_dataset_name} not found in loaded data")
            continue
        mods_by_path[target_path].append(dataset_dict)

    # Apply all modifications per dataset cumulatively
    for target_path, mods in mods_by_path.items():
        for mod in mods:
            data_dict2[target_path] = replace_element(
                data_dict2[target_path], mod['r_idx'], mod['c_idx'], mod['updated_value']
            )

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    folder_path = output_dir_path / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    new_name = newh5filename(master_mod_list)
    new_file_path = folder_path / f"{new_name}.h5"

    with h5py.File(poi_input_data_path, 'r') as f_src, h5py.File(new_file_path, 'w') as f_new:

        def replace_dataset(name, obj):
            if isinstance(obj, h5py.Group):
                f_new.require_group(name)
            elif isinstance(obj, h5py.Dataset):
                if name in mods_by_path:
                    f_new.create_dataset(
                        name,
                        data=data_dict2[name],
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

    print(f"Saved modified file: {new_file_path}")

    if return_flag == 'on':
        return str(new_file_path)


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


def scenario_deck_input_and_ini_file_update(
    scenario_deck_file_path=scenario_deck_file_path,
    output_dir=output_dir,
    measurement=sofast_measurement,
    orientation=sofast_orientation,
    camera=sofast_camera,
    display=sofast_display,
    calibration=sofast_calibration,
    facet=facet_data,
    measurement_id=measurement_id,
    post_process_id=post_process_id,
    input_ini_template_path=input_ini_template_path,
):
    """

    Summary
    -------

    This function processes a scenario deck CSV file and generates corresponding ini files with file paths for modified datasets.

    This function performs the following:
    - Reads and validates the scenario deck CSV.
    - Applies modifications to datasets in the measurement, orientation, camera, and display H5 input files.
    - Generates updated HDF5 files with modifications to the datasets within H5 files corresponding to the scenario deck CSV file.
    - generates updated ini configuration files with new file paths and identifiers corresponding to the changes in H5 input files.

    Helper Functions Used
    ---------------------
    - parse_reference(): Parses reference element from source file to identify dataset and specified indices for an element in data array.
    - replace_element(): Replaces elements in datasets at specified indices with a new assigned value.
    - modifications_list_per_row(): Generates a list of dictionaries (of modifications to be made) grouped by row.
    - newh5filename(): Generates new filenames for modified HDF5 files based on parameter name and assigned new value.
    - make_and_save_mods(): Reads input H5 file, applies modifications_list_per_row, and saves new HDF5 files.
    - update_ini_file_by_search(): generates ini files with filepaths for modified input files.

    Parameters
    ----------
        scenario_deck_file_path (str or Path): Path to the scenario deck CSV file.
        output_dir (str or Path): Directory where output files will be saved.
        measurement (str or Path): Path to the measurement HDF5 file.
        orientation (str or Path): Path to the orientation HDF5 file.
        camera (str or Path): Path to the camera HDF5 file.
        display (str or Path): Path to the display HDF5 file.
        calibration (str or Path): Path to the calibration file.
        facet (str or Path): Path to the facet JSON file.
        measurement_id (str): Identifier for the measurement.
        post_process_id (str): Identifier for post-processing.
        input_ini_template_path (str or Path): Path to the ini template file.


    Returns
    -------
        None

    Raises
    ------
        Various exceptions depending on file I/O and data processing errors.

    """

    import pandas as pd
    import h5py
    import copy
    from pathlib import Path
    from collections import defaultdict
    import os

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    df = read_and_validate_csv(scenario_deck_file_path)

    pathlist = []
    poi_input_data_paths = {}

    # Modification of Measurement File
    all_measurement_mod_lists = modifications_list_per_row(df, sofastarg='m')  # or None for all

    for i, master_mod_list in enumerate(all_measurement_mod_lists):
        poi_input_data_paths['measurement'] = Path(measurement)
        measurement_data_dict = get_data_for_mods(poi_input_data_paths['measurement'], master_mod_list)
        if i < 10:
            newfilename = f'{i:03d}_measurement'
        elif i < 99:
            newfilename = f'{i:02d}_measurement'
        else:
            newfilename = f'{i}_measurement'
        measurement_file_path = make_and_save_mods(
            poi_input_data_paths['measurement'],
            master_mod_list,
            measurement_data_dict,
            output_dir,
            folder_name=newfilename,
            return_flag='on',
        )
        pathlist.append({'row': f'{i}', 'file': 'measurement', 'path': measurement_file_path})

    # Modification of Orientation File
    all_orientation_mod_lists = modifications_list_per_row(df, sofastarg='o')  # or None for all

    for i, master_mod_list in enumerate(all_orientation_mod_lists):
        poi_input_data_paths['orientation'] = Path(orientation)
        orientation_data_dict = get_data_for_mods(poi_input_data_paths['orientation'], master_mod_list)
        if i < 10:
            newfilename = f'{i:03d}_orientation'
        elif i < 100:
            newfilename = f'{i:02d}_orientation'
        else:
            newfilename = f'{i}_orientation'
        orientation_file_path = make_and_save_mods(
            poi_input_data_paths['orientation'],
            master_mod_list,
            orientation_data_dict,
            output_dir,
            folder_name=newfilename,
            return_flag='on',
        )
        pathlist.append({'row': f'{i}', 'file': 'orientation', 'path': orientation_file_path})

    # Modification of Camera File
    all_camera_mod_lists = modifications_list_per_row(df, sofastarg='c')  # or None for all
    for i, master_mod_list in enumerate(all_camera_mod_lists):
        poi_input_data_paths['camera'] = Path(camera)
        camera_data_dict = get_data_for_mods(poi_input_data_paths['camera'], master_mod_list)
        if i < 10:
            newfilename = f'{i:03d}_camera'
        elif i < 100:
            newfilename = f'{i:02d}_camera'
        else:
            newfilename = f'{i}_camera'
        camera_file_path = make_and_save_mods(
            poi_input_data_paths['camera'],
            master_mod_list,
            camera_data_dict,
            output_dir,
            folder_name=newfilename,
            return_flag='on',
        )
        pathlist.append({'row': f'{i}', 'file': 'camera', 'path': camera_file_path})

    # Modification of display File
    all_display_mod_lists = modifications_list_per_row(df, sofastarg='d')  # or None for all

    for i, master_mod_list in enumerate(all_display_mod_lists):
        poi_input_data_paths['display'] = Path(display)
        display_data_dict = get_data_for_mods(poi_input_data_paths['display'], master_mod_list)
        if i < 10:
            newfilename = f'{i:03d}_display'
        elif i < 100:
            newfilename = f'{i:02d}_display'
        else:
            newfilename = f'{i}_display'
        display_file_path = make_and_save_mods(
            poi_input_data_paths['display'],
            master_mod_list,
            display_data_dict,
            output_dir,
            folder_name=newfilename,
            return_flag='on',
        )
        pathlist.append({'row': f'{i}', 'file': 'display', 'path': display_file_path})

    print(pathlist)

    # creation of ini file with updated paths for measurement, orientation, camera, and display for each row
    updated_id = {'measurement_id': measurement_id, 'post_process_id': post_process_id}

    unique_rows = sorted(set(item['row'] for item in pathlist))

    for i in unique_rows:
        updated_process_input_file_path = {
            'file_camera': str(camera),
            'file_orientation': str(orientation),
            'file_display': str(display),
            'file_facet': str(facet),
            'file_measurement': str(measurement),
            'file_calibration': str(calibration),
            'dir_save_root': '',
        }

    for item in pathlist:
        if item['row'] == i:
            if item['file'] == 'camera':
                updated_process_input_file_path['file_camera'] = item['path']
            if item['file'] == 'orientation':
                updated_process_input_file_path['file_orientation'] = item['path']
            if item['file'] == 'display':
                updated_process_input_file_path['file_display'] = item['path']
            if item['file'] == 'measurement':
                updated_process_input_file_path['file_measurement'] = item['path']

        print(f"Row {i} updated paths:")
        for k, v in updated_process_input_file_path.items():
            print(f"  {k}: {v}")

        if int(i) < 10:
            ini_folder_name = f'{int(i):03d}_updated_ini_file'
            ini_file_name = f'{int(i):03d}_config.ini'
            updated_process_input_file_path['dir_save_root'] = f'{output_dir_path}/{int(i):03d}_sofastprocess_results'
        elif int(i) < 100:
            ini_folder_name = f'{int(i):02d}_updated_ini_file'
            ini_file_name = f'{int(i):02d}_config.ini'
            updated_process_input_file_path['dir_save_root'] = f'{output_dir_path}/{int(i):02d}_sofastprocess_results'
        else:
            ini_folder_name = f'{int(i)}_updated_ini_file'
            ini_file_name = f'{int(i)}_config.ini'
            updated_process_input_file_path['dir_save_root'] = f'{output_dir_path}/{int(i)}_sofastprocess_results'

        ini_folder_path = output_dir_path / ini_folder_name
        ini_folder_path.mkdir(parents=True, exist_ok=True)
        ini_file_path = ini_folder_path / f"{ini_file_name}"

        update_ini_file_by_search(input_ini_template_path, ini_file_path, updated_id, updated_process_input_file_path)


####### EXECUTION OF MAIN FUNCTION ######
##### Update filepaths for the following variables #####

# update filepath for your scenario deck. File must be saved as csv.
scenario_deck_file_path = 'C:/Users/nichowd/Desktop/single_facet_sensitivity/000_scenario_deck/scenario_deck.csv'

# update filepath for your output directory. All modified h5 files and related generated .ini files will be stored here.
output_dir = "C:/Users/nichowd/Desktop/single_facet_sensitivity/002_output"

# update filepath for the unmodified h5 measurment input file to be used to generated newly modified h5 input file.
sofast_measurement = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/measurement_facet.h5"

# update filepath for the unmodified h5 orientation input file to be used to generated newly modified h5 input file.
sofast_orientation = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/spatial_orientation.h5"

# update filepath for the unmodified h5 camera input file to be used to generated newly modified h5 input file.
sofast_camera = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/camera_sofast_downsampled.h5"

# update filepath for the unmodified h5 display input file to be used to generated newly modified h5 input file.
sofast_display = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/display_distorted_2d.h5"

# update filepath for the unmodified .json facet data file. This is only needed for generating filepath for facet data in .ini file.
facet_data = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/Facet_NSTTF.json"

# update filepath for the unmodified h5 calibration file. This is only needed for generating filepath for facet data in .ini file.
sofast_calibration = "C:/Users/nichowd/Desktop/single_facet_sensitivity/001_input/image_calibration.h5"

# update filepath for your empty .ini file to be used to generate all new .ini file for each row-wise modifications.
input_ini_template_path = "C:/Users/nichowd/Desktop/single_facet_sensitivity/004_ini_files/ini_template.ini"

# update relevant identification information for the .ini files.
measurement_id = "test123"
post_process_id = "test1234"

# after updating file paths above, run the function below to generate new input files and .ini files.
scenario_deck_input_and_ini_file_update()
