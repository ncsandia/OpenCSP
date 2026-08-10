"""
Summary
-------

This module is for tabulating and visualizing Root Mean Squared Error (RMSE) comparisons during sensitivity analysis of SOFAST input parameters.

This script performs the following steps:

1. Finds and compiles a list of all slope deviation HDF5 output filepaths from SOFAST analysis in the output directory
2. Extracts and tabulates all slope deviation data from HDF5 output files in the output directory.
3. Calculates RMSE for each file
3. If desired, saves tabulated data as a csv file in the parent directory under analysis folder.
4. Generate plots for enclosed enerfy and stores it in analysis folder in the parent directory.


Libraries
---------
os
json
h5py
pandas
csv
matplotlib

Examples
--------
To run the script, simply update the output directory file path and run the execution function:

            output_directory = "C:/Users/nichowd/Desktop/single_parameter_SA/002_output/"


Expected Outputs
----------------
This code can save the resulting plot images files to an analysis folder in the parent directory in the following subfolders:

    enclosed_energy_diff_plot_minimal_xxx - png file that contains figure of a line plot of enclosed energy difference for each parameter
    enclosed_energy_and_increment_diff_plot_minimal_xxx - png file that contains figure of a scatter plot of enclosed energy difference as a function of incremental changes for each parameter

    Note: xxx is the image file name suffix which refers to whether the tornado plot is a plot of x, y, delta_x, or delta_y

AI Acknowledgement
------------------
SandiaAI was used to faciliate code development and docstring documentation.


"""

import os
import h5py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

####################################### HELPER FUNCTIONS #################################################
######################################### DO NOT TOUCH #################################################


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


# # # check if find_files function is working

# test_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"

# files, filepaths_list = find_files(
#     test_directory,
#     file_end_key='slope_deviation_image_xy.h5',
#     save_json_filepath=True,
#     file_name="pathlist_slope_deviation_x",
# )
# print(files)

# print(filepaths_list)


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


# # check if extract_filename function is working
# for file in files:
#     extract_filename(file,"sa_")


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


# # check if find_dataset_with_keyword function is working
# for file in files:
#     with h5py.File(file, 'r') as f:
#         dataset = find_dataset_with_keyword(f, 'image')


def calculate_rmse(df):
    deviations = df.values.flatten()
    mse = np.mean(deviations**2)
    rmse = np.sqrt(mse)
    return rmse


# # check if calculate_rmse function is working
# calculate_rmse(dataset)


def process_hdf5_files(
    output_dir,
    keyword,
    name_start,
    file_end_key='slope_deviation_image_xy.h5',
    save_json_filepath=True,
    file_name="pathlist_slope_deviation_xy",
    name_end=None,
    compare_to_baseline=True,
):
    files, filepaths_list = find_files(output_dir, file_end_key, save_json_filepath, file_name)
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

    if 'vector_direction' in rmse_df.columns:
        rmse_df = [
            rmse_df[rmse_df['vector_direction'] == level].copy()
            for level in rmse_df['vector_direction'].dropna().unique()
        ]
    print(rmse_df)
    return rmse_df


# for file in files:
#     print(f'{file} \n')
# df = process_hdf5_files(file_path_list=files, keyword='image', name_start='sa_', name_end='_d')
# print(df)


####################################### UPDATE DIRECTORY TO RUN PLOTS #################################################

output_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"
analysis_folder = find_or_create_analysis_folder(output_directory)
df = process_hdf5_files(output_dir=output_directory, keyword='image', name_start='sa_', name_end='_nichowd')

####################################### RMSE PLOT #################################################


def rmse_line_plot(
    df,
    directory,
    xlabel,
    legend_y=None,
    y2=None,
    legend_y2=None,
    save_plot=False,
    plot_title_assigned=None,
    xlim=None,
    ylim=None,
):
    def plot_rmse(x, y, legend_y, xlabel, ylabel, title, imagefile_name, y2, legend_y2, save_plot, output_dir):
        fig, ax = plt.subplots()
        ax.plot(x, y, color='tab:blue')
        ax.tick_params(axis='x', labelrotation=45, labelsize=9)
        ax.tick_params(axis='x', labelsize=10)
        if y2 is not None:
            ax.plot(x, y2, color='tab:green')
            ax.legend([legend_y, legend_y2])
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        # else:
        #     ax.legend([legend_y])
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
        ax.grid()
        plt.tight_layout()
        if save_plot == True:
            fig.savefig(f'{imagefile_name}.png')
            save_path = os.path.join(output_dir, f'{imagefile_name}.png')
            plt.savefig(save_path, dpi=300)
            print(f'RMSE plot saved in {output_dir}')
        plt.show()

    def process_rmse_line_plot(df):
        plot_x_label = 'incremental change (m)' if xlabel is None else xlabel
        plot_title_given = 'Variation in RMSE (mrad)' if plot_title_assigned is None else plot_title_assigned
        plot_y_label = fr'RMSE(mrad)'
        plot_imagefile_name = 'rmse_line_plot'
        plot_legend_y = fr'$RMSE$' if legend_y is None else legend_y

        if isinstance(df, list):
            for i, single_df in enumerate(df):
                if 'vector_direction' in single_df.columns:
                    sorted_df = single_df.sort_values(by='increment')
                    print(sorted_df.to_string())
                    # Data for plotting
                    increment = sorted_df['increment']
                    rmse_value = sorted_df['RMSE']
                    if 'rmse_diff' in sorted_df.columns:
                        rmse_diff = sorted_df['rmse_diff']
                    vector_dir = single_df['vector_direction'].dropna().unique()
                    x_label = (
                        fr'Incremental change in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                        if len(vector_dir) == 1
                        else 'incremental change (m)'
                    )
                    if plot_title_assigned is None:
                        plot_title_assigned_vectorized = str(
                            'RMSE as a function of change in the'
                            + '\n'
                            + fr'camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                        )

                    plot_imagefile_name_vectorized = f'rmse_line_plot_{vector_dir[0]}'

                    print(f"plotting with vector direction for DataFrame {i}/{len(df)}")
                    plot_rmse(
                        x=increment,
                        y=rmse_value,
                        legend_y=plot_legend_y,
                        xlabel=x_label,
                        ylabel=plot_y_label,
                        title=plot_title_assigned_vectorized,
                        imagefile_name=plot_imagefile_name_vectorized,
                        y2=None,
                        legend_y2=None,
                        save_plot=save_plot,
                        output_dir=directory,
                    )
                else:
                    print('dataset is a list of dataframe without vector reference. check dataset and rerun.')

        else:
            sorted_df = df.sort_values(by='increment')
            print(sorted_df.to_string())
            # Data for plotting
            increment = sorted_df['increment']
            rmse_value = sorted_df['RMSE']
            if 'rmse_diff' in sorted_df.columns:
                rmse_diff = sorted_df['rmse_diff']
            plot_rmse(
                x=increment,
                y=rmse_value,
                legend_y=plot_legend_y,
                xlabel=plot_x_label,
                ylabel=plot_y_label,
                title=plot_title_given,
                imagefile_name=plot_imagefile_name,
                y2=None,
                legend_y2=None,
                save_plot=save_plot,
                output_dir=directory,
            )

    process_rmse_line_plot(df)


rmse_line_plot(df, directory=analysis_folder, xlabel=None, save_plot=True, ylim=(0.45, 0.75))
