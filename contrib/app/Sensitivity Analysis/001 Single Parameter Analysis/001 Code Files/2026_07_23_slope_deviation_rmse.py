import os
import h5py
import pandas as pd
import numpy as np


def find_or_create_analysis_folder(output_dir, return_all_dir=False):
    # Get parent directory of output_dir
    parent_dir = os.path.dirname(os.path.abspath(output_dir))

    # List all folders in parent_dir
    try:
        entries = os.listdir(parent_dir)
    except FileNotFoundError:
        entries = []

    # Find folder containing 'analysis' in its name (case-insensitive)
    analysis_folders = [
        entry for entry in entries if os.path.isdir(os.path.join(parent_dir, entry)) and 'analysis' in entry.lower()
    ]

    if analysis_folders:
        # Use the first matching folder
        analysis_dir = os.path.join(parent_dir, analysis_folders[0])
    else:
        # Create 'analysis' folder if none found
        analysis_dir = os.path.join(parent_dir, 'analysis')
        os.makedirs(analysis_dir, exist_ok=True)
    if return_all_dir == True:
        return analysis_dir, parent_dir
    else:
        return analysis_dir


## check if find_or_create_analysis_folder function is working
# find_or_create_analysis_folder(root_directory)

files = []
files_paths_list = []


def find_files(output_dir, file_end_key, save_json_filepath=False, file_name=None):
    matching_files_list = []
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for filename in filenames:
            if filename.endswith(file_end_key):
                full_path = os.path.join(dirpath, filename)
                matching_files_list.append(full_path)
    if save_json_filepath == True:
        analysis_dir = find_or_create_analysis_folder(output_dir)
        if file_name == None:
            jsonfilepaths = pd.DataFrame(matching_files_list, columns=['filepaths'])
            file_name = file_end_key.split(".")[0]
            saved_file_name = f'filepaths_{file_name}.csv'
            csv_path = os.path.join(analysis_dir, saved_file_name)
            jsonfilepaths.to_csv(csv_path, index=False)
            print(f" filepaths saved to {csv_path}")

        else:
            jsonfilepaths = pd.DataFrame(matching_files_list, columns=[f'{file_name}'])
            saved_file_name = f'{file_name}.csv'
            csv_path = os.path.join(analysis_dir, saved_file_name)
            jsonfilepaths.to_csv(csv_path, index=False)
            print(f"filepaths saved to {csv_path}")
        return matching_files_list, csv_path
    else:
        return matching_files_list


# check if find_files function is working

test_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output/sa_mdAAB0b000/SOFAST_Results_sa_mdAAB0b000_row0_nichowd"

# files = find_files(test_directory, file_end_key='_measurement_statistics.json', save_json_filepath=True, file_name="testing_file_name")
# print(files)

find_files(
    test_directory,
    file_end_key='slope_deviation_image_x.h5',
    save_json_filepath=True,
    file_name="pathlist_slope_deviation_x",
)

files, file_paths_test = find_files(
    test_directory,
    file_end_key='slope_deviation_image_x.h5',
    save_json_filepath=True,
    file_name="pathlist_slope_deviation_x",
)
print(files)

print(file_paths_test)

"""
def tabulate_data_from_files(files, key, name_start='sa_', name_end='_', exclude_substrings=None):

    if exclude_substrings is None:
        exclude_substrings = []

    results = []
    for file_path in files:
        # find filepath and file name
        results_folder_name = os.path.dirname(os.path.abspath(file_path))
        parent_folder_name = os.path.dirname(os.path.abspath(results_folder_name))
        filename = os.path.basename(parent_folder_name)

        # set table data using file name
        # # Find the index of the first part starting with 'sa'
        start_index = filename.find(name_start)
        if start_index != -1:
            if name_end:
                next_end_index = filename.find(name_end, start_index + len(name_start))
                if next_end_index != -1:
                    extracted_name = filename[start_index:next_end_index]
                else:
                    extracted_name = filename[start_index:]
            else:
                # No name_end provided, extract from start_index to end
                extracted_name = filename[start_index:]
        try:
            with open(file_path, 'r') as f:
            if isinstance(data, list) and len(data) > 0:
                value = data[0].get(key, None)
                if isinstance(value, list) and len(value) == 2:
                    x, y = value
                    results.append((extracted_name, x, y))
            else:
                value = None
                
            # print(f"Extracted name: {extracted_name}\n{key}: {value}\n")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {file_path}: {e}")
    df = pd.DataFrame(results, columns=['settings', 'x', 'y'])

            with h5py.File(file_path, 'r') as f:
            dataset = find_dataset_with_keyword(f, keyword)
            if dataset is not None:
                data = dataset[()]
                df = pd.DataFrame(data)
                rmse = calculate_rmse(df)
                results.append((extracted_name, rmse))
            else:
                print(f"No dataset containing keyword '{keyword}' found in file {file_path}")
    return result

    # Exclude rows containing any exclude_substrings
    if exclude_substrings:
        mask = df['settings'].apply(lambda s: not any(sub in s for sub in exclude_substrings))
        df = df[mask]
    return df
"""

# # check if tabulate_data_from_files function is working without excluding substrings

# key_to_extract = 'focal_lengths_parabolic_xy'  # Replace with your key
# df = tabulate_data_from_files(files, key_to_extract, name_end='_nichowd3')
# print(df)


def extract_filename(file_path, name_start, name_end=None):
    results_folder_name = os.path.dirname(os.path.abspath(file_path))
    parent_folder_name = os.path.dirname(os.path.abspath(results_folder_name))
    filename = os.path.basename(parent_folder_name)

    start_index = filename.find(name_start)
    if start_index != -1:
        if name_end:
            next_end_index = filename.find(name_end, start_index + len(name_start))
            if next_end_index != -1:
                extracted_name = filename[start_index:next_end_index]
            else:
                extracted_name = filename[start_index:]
        else:
            extracted_name = filename[start_index:]
        return extracted_name
    else:
        return None


# for file in files:
#     extract_filename(file, "sa_")


def find_dataset_with_keyword(file, keyword):
    """
    Recursively search for a dataset whose key contains the keyword.
    Returns the first matching dataset found, else None.
    """
    found_dataset = None

    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset) and keyword in name:
            print(f"dataset with '{keyword}' found : {name}")
            found_dataset_name = name
            found_dataset = obj
            found_dataset = pd.DataFrame(found_dataset)
            return found_dataset_name, found_dataset  # stop visiting further

    datasetname, dataset = file.visititems(visitor)

    print(dataset.shape)
    return dataset


for file in files:
    with h5py.File(file, 'r') as f:
        dataset = find_dataset_with_keyword(f, 'image')

dataset.values.flatten() ** 2


def calculate_rmse(df):
    deviations = df.values.flatten()
    mse = np.mean(deviations**2)
    rmse = np.sqrt(mse)
    return rmse


calculate_rmse(dataset)


def process_hdf5_files(files, keyword, name_start, name_end=None):
    results = []
    for file_path in files:
        extracted_name = extract_filename(file_path, name_start, name_end)
        if extracted_name is None:
            extracted_name = os.path.basename(file_path)  # fallback
            print(f"file name: {extracted_name}")

        with h5py.File(file_path, 'r') as f:
            dataset = find_dataset_with_keyword(f, keyword)
            if dataset is not None:
                data = dataset[()]
                df = pd.DataFrame(data)
                rmse = calculate_rmse(df)
                results.append((extracted_name, rmse))
            else:
                print(f"No dataset containing keyword '{keyword}' found in file {file_path}")
    return results


keyword = "image"  # keyword to search for in dataset keys
name_start = "sa"
name_end = None

rmse_results = process_hdf5_files(files, keyword, name_start, name_end)

for filename, rmse in rmse_results:
    print(f"File: {filename}, RMSE: {rmse}")
