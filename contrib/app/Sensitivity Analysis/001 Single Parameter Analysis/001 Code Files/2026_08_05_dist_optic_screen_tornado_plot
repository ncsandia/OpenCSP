import os
import json
import pandas as pd
import csv
import matplotlib.pyplot as plt

########################################## HELPER FUNCTIONS ##########################################
#### DO NOT MODIFY


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


def find_focal_length_files(output_dir, file_end_key, save_json_filepath=False, file_name=None):
    matching_files_list = []
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for filename in filenames:
            if filename.endswith(file_end_key):
                full_path = os.path.join(dirpath, filename)
                matching_files_list.append(full_path)

    if save_json_filepath == True:
        analysis_dir = find_or_create_analysis_folder(output_dir)
        if file_name == None:
            jsonfilepaths = pd.DataFrame(matching_files_list, columns=['focal_length_data_filepaths'])
            csv_path = os.path.join(analysis_dir, 'focal_length_data_filepaths.csv')
            jsonfilepaths.to_csv(csv_path, index=False)
            print(f"Focal Length filepaths saved to {csv_path}")
        else:
            jsonfilepaths = pd.DataFrame(matching_files_list, columns=[f'{file_name}'])
            saved_file_name = f'{file_name}.csv'
            csv_path = os.path.join(analysis_dir, saved_file_name)
            jsonfilepaths.to_csv(csv_path, index=False)
            print(f"Focal Length filepaths saved to {csv_path}")

        return matching_files_list, csv_path
    else:
        return matching_files_list


def tabulate_data_from_json_files(files, key, name_start='sa_', name_end='_', exclude_substrings=None):

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
                data = json.load(f)
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

    # Exclude rows containing any exclude_substrings
    if exclude_substrings:
        mask = df['settings'].apply(lambda s: not any(sub in s for sub in exclude_substrings))
        df = df[mask]
    return df


def extend_settings_column(df):
    df['sign'] = None
    df['increment'] = None
    for i, row in df.iterrows():
        value = row.iloc[0]
        for scale in ['n', 'p', 'b']:
            # Find all occurrences of scale in value, in order
            indices = [idx for idx, ch in enumerate(value) if ch == scale]
            for idx in indices:
                # Check if next character exists and is a digit
                if idx + 1 < len(value) and value[idx + 1].isdigit():
                    sign = scale
                    start = idx + 1
                    # Find underscore followed by non-digit character
                    for j in range(start, len(value) - 1):
                        if value[j] == '_' and not value[j + 1].isdigit():
                            end = j
                            break
                    else:
                        end = len(value)
                    increment = value[start:end].replace('_', '.', 1)
                    df.at[i, 'sign'] = sign
                    df.at[i, 'increment'] = increment
                    break  # Found valid occurrence, break inner loop
            else:
                # Continue if inner loop did not break (no valid occurrence)
                continue
            # Inner loop broke, so break outer scale loop
            break
    print('sign and increment variables generated.')
    df['sign'] = df['sign'].astype('category')
    df['increment'] = df['increment'].astype('float64')
    df.loc[df['sign'] == 'n', 'increment'] *= -1
    if df['settings'].str.contains('row').all():
        df['row'] = None
    if 'row' in df.columns:
        for i, row in df.iterrows():
            rownum = row.loc['settings'].split('row')
            rownum = rownum[1].split('_')
            rownum = rownum[0]
            df['row'].iloc[i] = rownum
        df['row'] = df['row'].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna().astype(int)
        unique_rows = set(df['row'].unique())
        print(f'the uniqure rows correspond with the array elements found. They are: {unique_rows}')
        if len(unique_rows) == 3:
            df['vector_direction'] = None
            allowed = {0, 1, 2}
            # Check if all unique values are subset of {0,1,2}
            if unique_rows.issubset(allowed):
                mapping = {0: 'x', 1: 'y', 2: 'z'}
                df['vector_direction'] = df['row'].map(mapping)
            else:
                print("Column 'row' contains values outside 0,1,2; skipping vector_direction creation.")
        elif len(unique_rows) == 2:
            df['vector_direction'] = None
            allowed = {0, 1}
            # Check if all unique values are subset of {0,1}
            if unique_rows.issubset(allowed):
                mapping = {0: 'x', 1: 'y'}
                df['vector_direction'] = df['row'].map(mapping)
            else:
                print("Column 'row' contains values outside 0,1; skipping vector_direction creation.")
        else:
            print('dataset have dimensions outside x,y or x,y,z. vector_direction variable is not')

    if 'vector_direction' in df.columns:
        dfs = [df[df['vector_direction'] == level].copy() for level in df['vector_direction'].dropna().unique()]
        return dfs
    else:
        return df


def find_enclosed_energy_files(output_dir, file_end_key, save_filepath=False, file_name=None):
    matching_files_list = []
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for filename in filenames:
            if filename.endswith(file_end_key):
                full_path = os.path.join(dirpath, filename)
                matching_files_list.append(full_path)

    if save_filepath == True:
        analysis_dir = find_or_create_analysis_folder(output_dir)
        if file_name == None:
            savefilepathdf = pd.DataFrame(matching_files_list, columns=['enclosed_energy_data_filepaths'])
            csv_path = os.path.join(analysis_dir, 'enclosed_energy_data_filepaths.csv')
            savefilepathdf.to_csv(csv_path, index=False)
            print(f"Enclosed energy data filepaths saved to {csv_path}")

        else:
            savefilepathdf = pd.DataFrame(matching_files_list, columns=[f'{file_name}'])
            saved_file_name = f'{file_name}.csv'
            csv_path = os.path.join(analysis_dir, saved_file_name)
            savefilepathdf.to_csv(csv_path, index=False)
            print(f"Enclosed energy data filepaths saved to {csv_path}")
        return matching_files_list, csv_path
    else:
        return matching_files_list


def tabulate_enclosed_energy_data_from_hdf5_files(files, name_start='sa_', name_end='_', exclude_substrings=None):

    if exclude_substrings is None:
        exclude_substrings = []

    all_rows = []
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
            with h5py.File(file_path, 'r') as f:
                # Check if datasets exist
                if 'energy_values' in f and 'energy_widths' in f:
                    energy_values = f['energy_values'][:]
                    energy_widths = f['energy_widths'][:]

                    # Check lengths match
                    if len(energy_values) == len(energy_widths):
                        for i in range(len(energy_values)):
                            all_rows.append(
                                {
                                    'settings': extracted_name,
                                    'dataset_row_index': i + 1,
                                    'energy_values': energy_values[i],
                                    'energy_widths': energy_widths[i],
                                }
                            )
                    else:
                        print(
                            f"Length mismatch in {file_path}: energy_values and energy_widths have different lengths."
                        )
                else:
                    print(f"Datasets 'energy_values' or 'energy_widths' not found in {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    df = pd.DataFrame(all_rows)

    # Exclude rows containing any exclude_substrings
    if exclude_substrings:
        mask = df['settings'].apply(lambda s: not any(sub in s for sub in exclude_substrings))
        df = df[mask]
    return df


def find_rmse_files(output_dir, file_end_key, save_json_filepath=False, file_name=None):
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


def find_dataset_with_keyword(file, keyword):
    """
    Recursively search for a dataset whose key contains the keyword.
    Returns the first matching dataset found, else None.
    """

    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset) and keyword in name:
            print(f"dataset with '{keyword}' found : {name}")
            found_dataset_name = name
            found_dataset = obj
            found_dataset = pd.DataFrame(found_dataset)
            return found_dataset_name, found_dataset  # stop visiting further
        else:
            print(f"dataset with '{keyword} was not found.'")
            found_dataset = None
            return None

    found_dataset_name, dataset = file.visititems(visitor)
    print(dataset.shape)
    return dataset


def calculate_rmse(df):
    deviations = df.values.flatten()
    mse = np.mean(deviations**2)
    rmse = np.sqrt(mse)
    return rmse


########################################## EXECUTION FUNCTIONS ##########################################
# output data directory

dist_optic_screen_output_dir = (
    "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/002_output"
)


# Focal Length
def tornado_plot_data(
    output_dir,
    name_start='sa_',
    name_end='_',
    increments_to_filter=[-0.05, 0.05, 0.05],
    default_setting_substring='0b000',
    energy_width_min=0.48,
    energy_width_max=0.51,
):

    def focal_length_data(
        focal_length_dir,
        file_end_key='_measurement_statistics.json',
        save_json_filepath=False,
        key='focal_lengths_parabolic_xy',
        name_start=name_start,
        name_end=name_end,
    ):
        files = find_focal_length_files(focal_length_dir, file_end_key, save_json_filepath, file_name=None)
        df = tabulate_data_from_json_files(files, key, name_start, name_end)
        print('data tabulated')
        print(df)
        return df

    focal_length_df = focal_length_data(output_dir)

    # Enclosed Energy

    def enclosed_energy_data(
        enclosed_energy_dir,
        file_end_key='enclosed_energy_image.h5',
        save_filepath=False,
        name_start=name_start,
        name_end=name_end,
    ):
        files = find_enclosed_energy_files(enclosed_energy_dir, file_end_key, save_filepath=False, file_name=None)
        df = tabulate_enclosed_energy_data_from_hdf5_files(files, name_start, name_end, exclude_substrings=None)
        print('data tabulated')
        print(df)
        return df

    enclosed_energy_df = enclosed_energy_data(output_dir)

    # RMSE

    def process_rmse_hdf5_files(
        output_dir,
        keyword,
        name_start,
        file_end_key='slope_deviation_image_xy.h5',
        save_json_filepath=True,
        file_name="pathlist_slope_deviation_xy",
        name_end=None,
        compare_to_baseline=True,
    ):
        files, filepaths_list = find_rmse_files(output_dir, file_end_key, save_json_filepath, file_name)
        results = []
        for file_path in files:
            extracted_name = extract_filename(file_path, name_start, name_end)
            if extracted_name is None:
                extracted_name = os.path.basename(file_path)  # fallback
                # print(f"file name: {extracted_name}")

            with h5py.File(file_path, 'r') as f:
                dataset = find_dataset_with_keyword(f, keyword)
                if dataset is not None:
                    rmse = calculate_rmse(dataset)
                    print(rmse)
                    results.append([extracted_name, rmse])
                else:
                    print(f"No dataset containing keyword '{keyword}' found in file {file_path}")

        rmse_df = pd.DataFrame(results, columns=["settings", "RMSE"])
        print(rmse_df)
        rmse_df['param'] = None
        rmse_df['sign'] = None
        rmse_df['increment'] = None
        for i, row in rmse_df.iterrows():
            value = row.iloc[0]
            for scale in ['n', 'p', 'b']:
                # Find all occurrences of scale in value, in order
                indices = [idx for idx, ch in enumerate(value) if ch == scale]
                for idx in indices:
                    # Check if next character exists and is a digit
                    if idx + 1 < len(value) and value[idx + 1].isdigit():
                        sign = scale
                        start = idx + 1
                        # Find underscore followed by non-digit character
                        for j in range(start, len(value) - 1):
                            if value[j] == '_' and not value[j + 1].isdigit():
                                end = j
                                break
                        else:
                            end = len(value)
                        increment = value[start:end].replace('_', '.', 1)
                        rmse_df['param'] = value[:idx].replace('sa_', '', 1)
                        rmse_df.at[i, 'sign'] = sign
                        rmse_df.at[i, 'increment'] = increment
                        break  # Found valid occurrence, break inner loop
                else:
                    # Continue if inner loop did not break (no valid occurrence)
                    continue
                # Inner loop broke, so break outer scale loop
                break
        print(rmse_df)
        if rmse_df["settings"].str.contains('row').all():
            rmse_df['row'] = None
        print(rmse_df)
        if 'row' in rmse_df.columns:
            for i, row in rmse_df.iterrows():
                rownum = row.loc['settings'].split('row')
                rownum = rownum[1].split('_')
                rownum = rownum[0]
                rmse_df['row'].iloc[i] = rownum
            rmse_df['row'] = rmse_df['row'].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna().astype(int)
            unique_rows = set(rmse_df['row'].unique())
            print(rmse_df)
            if len(unique_rows) == 3:
                rmse_df['vector_direction'] = None
                allowed = {0, 1, 2}
                # Check if all unique values are subset of {0,1,2}
                if unique_rows.issubset(allowed):
                    mapping = {0: 'x', 1: 'y', 2: 'z'}
                    rmse_df['vector_direction'] = rmse_df['row'].map(mapping)
                else:
                    print("Column 'row' contains values outside 0,1,2; skipping vector_direction creation.")
            elif len(unique_rows) == 2:
                rmse_df['vector_direction'] = None
                allowed = {0, 1}
                # Check if all unique values are subset of {0,1}
                if unique_rows.issubset(allowed):
                    mapping = {0: 'x', 1: 'y'}
                    rmse_df['vector_direction'] = rmse_df['row'].map(mapping)
                else:
                    print("Column 'row' contains values outside 0,1; skipping vector_direction creation.")
            else:
                print('dataset have dimensions outside x,y or x,y,z. vector_direction variable is not')
            print(rmse_df)
        if compare_to_baseline:
            rmse_df['rmse_diff'] = np.nan
            if 'row' in rmse_df.columns:
                for row_value, group in rmse_df.groupby('row'):
                    default_rmse_series = group.loc[group['settings'].str.contains('0b000', na=False), 'RMSE']
                    if default_rmse_series.empty:
                        print(f"Warning: No baseline '0b000' found in group {row_value}, skipping this group.")
                        default_rmse_series = np.NaN
                        continue
                    default_rmse = default_rmse_series.iloc[0]
                    print(f"for group {row_value}, the row containing baseline is:", default_rmse)
                    diff = group['RMSE'] - default_rmse
                    rmse_df.loc[group.index, 'rmse_diff'] = diff
            else:
                default_rmse_series = rmse_df.loc[rmse_df['settings'].str.contains("0b000", na=False), 'RMSE']
                default_rmse = default_rmse_series.iloc[0]
                rmse_df['rmse_diff'] = rmse_df['RMSE'] - default_rmse

        rmse_df['sign'] = rmse_df['sign'].astype('category')
        rmse_df['increment'] = rmse_df['increment'].astype('float64')
        rmse_df.loc[rmse_df['sign'] == 'n', 'increment'] *= -1

        # if 'vector_direction' in rmse_df.columns:
        #     rmse_df = [
        #         rmse_df[rmse_df['vector_direction'] == level].copy()
        #         for level in rmse_df['vector_direction'].dropna().unique()
        #   ]
        print(rmse_df)
        return rmse_df

    rmse_df = process_rmse_hdf5_files(output_dir=output_dir, keyword='image', name_start=name_start, name_end=name_end)

    main_df = pd.merge(focal_length_df, enclosed_energy_df, on='settings')
    main_df = pd.merge(main_df, rmse_df, on='settings')

    def calculate_deltas(df, increments_to_filter, default_setting_substring, energy_width_min, energy_width_max):
        # Filter the default data (baseline)
        default_df = df[df['settings'].str.contains(default_setting_substring)].copy()

        # Filter the data for the specified increments
        filtered_df = df[df['increment'].isin(increments_to_filter)].copy()

        # Merge filtered data with default data on 'dataset_row_index' to align rows for delta calculation
        merged_df = pd.merge(
            filtered_df,
            default_df[['dataset_row_index', 'x', 'y', 'energy_values']],
            on='dataset_row_index',
            suffixes=('', '_default'),
        )

        # Calculate deltas
        merged_df['delta_x'] = merged_df['x'] - merged_df['x_default']
        merged_df['delta_y'] = merged_df['y'] - merged_df['y_default']
        merged_df['delta_energy'] = merged_df['energy_values'] - merged_df['energy_values_default']

        # Filter merged_df to only rows where energy_widths is within the specified range
        filtered_energy_df = merged_df[
            (merged_df['energy_widths'] >= energy_width_min) & (merged_df['energy_widths'] <= energy_width_max)
        ].copy()

        # Calculate delta_energy only on this filtered subset
        filtered_energy_df['delta_energy'] = (
            filtered_energy_df['energy_values'] - filtered_energy_df['energy_values_default']
        )

        # Optionally drop the default columns after calculation
        filtered_energy_df.drop(columns=['x_default', 'y_default', 'energy_values_default'], inplace=True)

        return filtered_energy_df

    df = calculate_deltas(main_df, increments_to_filter, default_setting_substring, energy_width_min, energy_width_max)

    return df


dist_optic_screen_data = tornado_plot_data(dist_optic_screen_output_dir, name_start='sa_', name_end='_d')

v_cam_screen_cam_output_dir = (
    "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"
)

v_cam_screen_cam_data = tornado_plot_data(v_cam_screen_cam_output_dir, name_start='sa_', name_end='_nichowd')

df = pd.concat([dist_optic_screen_data, v_cam_screen_cam_data], axis=0)
print(df)

print(df['param_row'].unique())
########################################## PLOTTING FUNCTIONS ##########################################
### Update plot titles and axis labels below BEFORE running plotting function

metrics_plot_title = {
    'RMSE': 'RMSE Comparison for Parameter Measure Difference of .05 m',
    'delta_x': 'Focal Length Difference of X for Parameter Measure Difference of .05 m ',
    'delta_y': 'Focal Length Difference of Y for Parameter Measure Difference of .05 m ',
    'delta_energy': str('Change in Enclosed Energy (fraction)' + '\n' + '(at Receiver Width between .48 m and .51 m)'),
}

metric_plot_x_axis = {
    'RMSE': 'RMSE (mrad)',
    'delta_x': 'Difference in focal length of X (m)',
    'delta_y': 'Difference in focal length of Y (m)',
    'delta_energy': 'Difference in Enclosed Energy (fraction)',
}

metric_plot_y_axis = {
    'RMSE': 'Parameters',
    'delta_x': 'Parameter and Row Combination',
    'delta_y': 'Parameter and Row Combination',
    'delta_energy': 'Parameter and Row Combination',
}

param_row_label_map = {
    'mdAAA_nan': str(fr'$\Delta$' + fr'$d_{{ms}}$'),
    'mdAAB_0.0': str(fr'$\Delta$' + fr'$\vec{{v}}_{{x_{{cs}}}}$'),
    'mdAAB_1.0': str(fr'$\Delta$' + fr'$\vec{{v}}_{{y_{{cs}}}}$'),
    'mdAAB_2.0': str(fr'$\Delta$' + fr'$\vec{{v}}_{{z_{{cs}}}}$'),
}


def plot_tornado_by_param_row(df, metrics_plot_title, metric_plot_x_axis, param_row_label_map):
    # Create combined param_row column
    df['param_row'] = df['param'].astype(str) + '_' + df['row'].astype(str)

    # Group by 'param_row' and 'increment', calculate mean of required columns
    grouped = (
        df.groupby(['param_row', 'increment'])
        .agg({'RMSE': 'mean', 'delta_x': 'mean', 'delta_y': 'mean', 'delta_energy': 'mean'})
        .reset_index()
    )

    metrics = ['RMSE', 'delta_x', 'delta_y', 'delta_energy']

    for metric in metrics:
        # Prepare data for left and right increments
        left_data = grouped[grouped['increment'] == -0.05][['param_row', metric]].set_index('param_row')
        right_data = grouped[grouped['increment'] == 0.05][['param_row', metric]].set_index('param_row')

        # Get all unique param_row combos
        all_param_rows = sorted(set(left_data.index).union(right_data.index))

        # Reindex and fill missing with 0
        left_vals = left_data.reindex(all_param_rows).fillna(0)[metric].values
        right_vals = right_data.reindex(all_param_rows).fillna(0)[metric].values

        # Calculate max absolute change per param_row for sorting
        max_abs_change = np.maximum(np.abs(left_vals), np.abs(right_vals))

        # Sort indices by descending max_abs_change
        sorted_indices = np.argsort(-max_abs_change)

        # Apply sorting
        sorted_param_rows = [all_param_rows[i] for i in sorted_indices]
        left_vals_sorted = left_vals[sorted_indices]
        right_vals_sorted = right_vals[sorted_indices]

        y_pos = np.arange(len(sorted_param_rows))

        fig, ax = plt.subplots(
            figsize=(12, max(6, len(sorted_param_rows) * 0.3))
        )  # height scales with number of param_row combos

        # Plot bars for increment = -0.05 (left side)
        for i, val in enumerate(left_vals_sorted):
            color = 'tab:blue' if val >= 0 else 'tab:red'
            ax.barh(y_pos[i], -abs(val), left=0, color=color)

        # Plot bars for increment = 0.05 (right side)
        for i, val in enumerate(right_vals_sorted):
            color = 'tab:blue' if val >= 0 else 'tab:red'
            ax.barh(y_pos[i], abs(val), left=0, color=color)

        ax.axvline(0, color='black', linewidth=0.8)
        ax.set_yticks(y_pos)
        y_labels = [param_row_label_map.get(pr, pr) for pr in sorted_param_rows]
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()  # largest change on top

        # Adjust x-axis limits to add padding for labels
        all_vals = np.concatenate([left_vals_sorted, right_vals_sorted])
        max_val = max(abs(all_vals)) if len(all_vals) > 0 else 1
        padding = max_val * 0.25
        ax.set_xlim(-max_val - padding, max_val + padding)

        # Add numeric labels next to bars
        for i, val in enumerate(left_vals_sorted):
            color = 'tab:blue' if val >= 0 else 'tab:red'
            xpos = -abs(val) - padding * 0.05
            ax.text(xpos, y_pos[i], f'{val:.3f}', va='center', ha='right', color=color, fontsize=7)

        for i, val in enumerate(right_vals_sorted):
            color = 'tab:blue' if val >= 0 else 'tab:red'
            xpos = abs(val) + padding * 0.05
            ax.text(xpos, y_pos[i], f'{val:.3f}', va='center', ha='left', color=color, fontsize=7)

        # Custom x-axis labels for left and right sides
        ax.set_xticks([-max_val, 0, max_val])
        ax.set_xticklabels([r'-0.05 increment', '0', r'0.05 increment'])

        ax.set_xlabel('Average Value')
        ax.set_title(f'Tornado Plot for metric: {metric}')

        ax.set_title(metrics_plot_title.get(metric, ''))
        ax.set_xlabel(metric_plot_x_axis.get(metric, ''))
        ax.set_ylabel('Parameters')

        # Legend for colors
        from matplotlib.patches import Patch

        if metric not in 'RMSE':
            legend_elements = [
                Patch(facecolor='tab:blue', label='Positive Value'),
                Patch(facecolor='tab:red', label='Negative Value'),
            ]
            ax.legend(handles=legend_elements, loc='best', fontsize='x-small')

        plt.tight_layout()
        plt.show()


plot_tornado_by_param_row(df, metrics_plot_title, metric_plot_x_axis, param_row_label_map)


########################################################################
