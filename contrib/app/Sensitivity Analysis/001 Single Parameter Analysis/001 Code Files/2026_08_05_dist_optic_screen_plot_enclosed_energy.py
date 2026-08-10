"""
Summary
-------

This module is for tabulating and visualizing enclosed energy comparisonsduring sensitivity analysis of SOFAST input parameters.

This script performs the following steps:

1. Finds and compiles a list of all enclosed energy HDF5 output filepaths from SOFAST analysis in the output directory
2. Extracts and tabulates all enclosed energy data from HDF5 output files in the output directory.
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
itertools

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
import json
import h5py
import pandas as pd
import csv
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from itertools import cycle

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


# # check if find_or_create_analysis_folder function is working
# root_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"
# find_or_create_analysis_folder(root_directory)


def find_files(output_dir, file_end_key, save_filepath=False, file_name=None):
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


# ## check if find_files function is working

# test_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"

# # files = find_files(test_directory, file_end_key='enclosed_energy_image.h5', save_filepath=False)
# # print(files)


# files, file_paths_test = find_files(
#     test_directory,
#     file_end_key='enclosed_energy_image.h5',
#     save_filepath=True,
#     file_name="enclosed_energy_data_filepaths_list",
# )
# print(files)
# print(file_paths_test)

# for file in files:
#     print(file)


def tabulate_data_from_hdf5_files(files, name_start='sa_', name_end='_', exclude_substrings=None):

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


# df = tabulate_data_from_hdf5_files(files, name_end='_nichowd')
# print(df)

# settings_with_0b00 = df[df['settings'].str.contains('0b00')]
# print(settings_with_0b00)

# settings_others = df[~df.index.isin(settings_with_0b00.index)]
# print(settings_others)


def extend_settings_column(df, column_name, print_check=False):
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


# dfs = extend_settings_column(df, 'settings')
# print(dfs)


def add_energy_value_diff_column(df):
    # Extract default setting rows
    default_mask = df['settings'].str.contains('0b000')
    default_df = df[default_mask][['energy_widths', 'energy_values']].set_index('energy_widths')

    # Map default energy values to all rows based on energy_widths
    df = df.copy()
    df['default_energy_values'] = df['energy_widths'].map(default_df['energy_values'])

    # Calculate difference
    df['energy_value_diff'] = df['energy_values'] - df['default_energy_values']

    # Optional: For default setting rows, difference will be zero or NaN, you can set to 0
    df.loc[default_mask, 'energy_value_diff'] = 0.0

    # Drop the helper column if you want
    df.drop(columns=['default_energy_values'], inplace=True)

    return df


# # create column with energy difference
# df_with_diff = add_energy_value_diff_column(df)
# print(df_with_diff)


####################################### UPDATE DIRECTORY TO RUN PLOTS #################################################

output_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/002_output"
files, file_paths_test = find_files(
    output_directory,
    file_end_key='enclosed_energy_image.h5',
    save_filepath=True,
    file_name="enclosed_energy_data_filepaths_list",
)
print(files)
print(file_paths_test)

for file in files:
    print(file)

analysis_folder = find_or_create_analysis_folder(output_directory)
df = tabulate_data_from_hdf5_files(files, name_end='_nichowd')
dfs = extend_settings_column(df, 'settings')
print(dfs)


####################################### PLOTS #################################################

######## PLOT TYPE 1 : Basic Enclosed Energy Curve with extended legend ################################


def plot_enclosed_energy_curve(df, default_data_key='0b00', xlim=None, ylim=None):

    def enclosed_energy_plot(
        df,
        plot_x_label='Reciever Width (m)',
        plot_y_label='Enclosed Energy (fraction)',
        plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
    ):

        plt.figure(figsize=(10, 6))
        # Separate settings with '0b00' and others
        settings_with_0b00 = df[df['settings'].str.contains(default_data_key)]['settings'].unique()
        settings_others = [s for s in df['settings'].unique() if s not in settings_with_0b00]

        # Prepare colors for other settings (excluding red)
        # Use tab10 colormap, skipping red (which is the first color)
        cmap = plt.get_cmap('tab10')
        # tab10 colors: 0=blue, 1=orange, 2=green, 3=red, 4=purple, ...
        # red is index 3, so skip that
        available_colors = [cmap(i) for i in range(cmap.N) if i != 3]

        # Cycle through colors if more settings than colors
        color_cycle = cycle(available_colors)

        # Plot other lines with distinct colors (not red)
        for setting in settings_others:
            df_sub = df[df['settings'] == setting]
            color = next(color_cycle)
            plt.plot(df_sub['energy_widths'], df_sub['energy_values'], color=color, label=fr'$d_{{ms}}$ = {setting} m')

        # Plot lines with '0b00' in red
        for setting in settings_with_0b00:
            df_sub = df[df['settings'] == setting]
            plt.plot(df_sub['energy_widths'], df_sub['energy_values'], color='red', label=fr'$d_{{ms}}$ = {setting} m')

        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)

        # Place legend outside the plot
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Settings', fontsize='small', ncols=3)

        plt.tight_layout(rect=[0, 0, 0.75, 1])  # leave space on right for legend
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
            enclosed_energy_plot(single_df, plot_title=plot_title_updated)

    else:
        enclosed_energy_plot(df)


plot_enclosed_energy_curve(dfs)


######## PLOT TYPE 2 : Basic Enclosed Energy Curve with shortened legend ################################


def plot_enclosed_energy_curve_2(df, default_data_key='0b00', xlim=None, ylim=None):
    def enclosed_energy_curve_plot_2(
        df,
        plot_x_label='Reciever Width (m)',
        plot_y_label='Enclosed Energy (fraction)',
        plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
    ):
        plt.figure(figsize=(10, 6))
        # Separate settings with '0b00' and others
        settings_with_0b00 = df[df['settings'].str.contains(default_data_key)]['settings'].unique()
        settings_others = [s for s in df['settings'].unique() if s not in settings_with_0b00]

        # # Prepare colors for other settings (excluding red)
        # # Use tab10 colormap, skipping red (which is the first color)
        # cmap = plt.get_cmap('tab10')
        # # tab10 colors: 0=blue, 1=orange, 2=green, 3=red, 4=purple, ...
        # # red is index 3, so skip that
        # available_colors = [cmap(i) for i in range(cmap.N) if i != 3]

        # # Cycle through colors if more settings than colors
        # color_cycle = cycle(available_colors)

        # Plot other lines with distinct colors (not red)
        for setting in settings_others:
            df_sub = df[df['settings'] == setting]
            # color = next(color_cycle)
            plt.plot(
                df_sub['energy_widths'],
                df_sub['energy_values'],
                # color=color,
                color='gray',
                label=setting,
            )

        # Plot lines with '0b00' in red
        for setting in settings_with_0b00:
            df_sub = df[df['settings'] == setting]
            plt.plot(df_sub['energy_widths'], df_sub['energy_values'], color='red', label=fr'$d_{{ms}}$ = {setting}m')

        # Create custom legend handles
        red_handles = [Line2D([0], [0], color='red', label='baseline') for setting in settings_with_0b00]
        gray_handle = Line2D([0], [0], color='gray', label='other settings')

        # Combine handles: gray first, then red
        handles = [gray_handle] + red_handles

        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)

        # Place legend outside the plot
        # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Settings', fontsize='small', ncols=3)
        plt.legend(handles=handles, loc='best', title='Settings', fontsize='small', ncol=3)

        plt.tight_layout(rect=[0, 0, 0.75, 1])  # leave space on right for legend
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
                enclosed_energy_curve_plot_2(single_df, plot_title=plot_title_updated)
            else:
                print('dataset is a list but vector_direction not found. check data.')

    else:
        enclosed_energy_curve_plot_2(df)


plot_enclosed_energy_curve_2(dfs)

######## PLOT TYPE 3 : Basic Enclosed Energy Curve with extended legend of increment as labels ################################


def plot_enclosed_energy_curve_3(df, default_data_key='0b00', xlim=None, ylim=None):
    def enclosed_energy_curve_plot_3(
        df,
        plot_x_label='Reciever Width (m)',
        plot_y_label='Enclosed Energy (fraction)',
        plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
    ):
        plt.figure(figsize=(10, 6))

        # Subset settings
        settings_with_originals = df[df['settings'].str.contains(default_data_key)]['settings'].unique()
        settings_others = [s for s in df['settings'].unique() if s not in settings_with_originals]

        # Colors for settings_others (excluding red)
        cmap = plt.get_cmap('tab10')
        available_colors = [cmap(i) for i in range(cmap.N) if i != 3]  # skip red (index 3)
        color_cycle = cycle(available_colors)

        labeled_increments = set()

        # Plot other settings with distinct colors
        for setting in settings_others:
            df_sub = df[df['settings'] == setting]
            color = next(color_cycle)
            for increment in df_sub['increment'].unique():
                df_group = df_sub[df_sub['increment'] == increment]
                label = str(fr'$d_{{ms}}$ = {increment}m') if increment not in labeled_increments else None
                plt.plot(df_group['energy_widths'], df_group['energy_values'], color=color, label=label)
                labeled_increments.add(increment)

        # Plot settings with '0b00' in red
        for setting in settings_with_originals:
            df_sub = df[df['settings'] == setting]
            for increment in df_sub['increment'].unique():
                df_group = df_sub[df_sub['increment'] == increment]
                label = str(fr'$d_{{ms}}$ = {increment}m') if increment not in labeled_increments else None
                plt.plot(df_group['energy_widths'], df_group['energy_values'], color='red', label=label)
                labeled_increments.add(increment)

        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)

        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='small', ncol=4)
        plt.tight_layout(rect=[0, 0, 0.75, 1])  # leave space for legend
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
                enclosed_energy_curve_plot_3(single_df, plot_title=plot_title_updated)
            else:
                print('dataset is a list but vector_direction not found. check data.')
    else:
        enclosed_energy_curve_plot_3(df)


plot_enclosed_energy_curve_3(dfs)

######## PLOT TYPE 4 : Enclosed Energy Difference with extended legend of increment as labels ################################


def plot_energy_value_diff(df, xlim=None, ylim=None):
    def energy_value_diff_plot1(
        df,
        plot_x_label='Reciever Width (m)',
        plot_y_label='Difference in Enclosed Energy (fraction)',
        plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
    ):
        plt.figure(figsize=(10, 6))

        # Get unique settings excluding the default (where diff is zero)
        increment = df['increment'].unique()

        for increment in increment:
            subset = df[df['increment'] == increment]
            plt.plot(subset['energy_widths'], subset['energy_value_diff'], label=fr'$d_{{ms}}$ = {increment}m')

        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)

        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncols=3)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            df_with_diff = add_energy_value_diff_column(single_df)
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
                energy_value_diff_plot1(df_with_diff, plot_title=plot_title_updated)
            else:
                print('dataset is a list but vector_direction not found. check data.')
    else:
        df_with_diff = add_energy_value_diff_column(df)
        energy_value_diff_plot1(df_with_diff)


plot_energy_value_diff(dfs)


######## PLOT TYPE 5 : Enclosed Energy Difference of reduced parameter variation (half as much of variation plotted) with legend of increment ################################

# # create column with energy difference
# df_with_diff = add_energy_value_diff_column(df)
# print(df_with_diff)


# def plot_energy_value_diff_2(df):
#     def energy_value_diff_plot2(
#         df,
#         xlim = None,
#         ylim = None
#         plot_x_label='Reciever Width (m)',
#         plot_y_label='Difference in Enclosed Energy (fraction)',
#         plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
#     ):
#         plt.figure(figsize=(10, 6))

#         # Get unique increments
#         unique_increments = df['increment'].unique()

#         # Filter increments: keep those that are 0.00, 0.05, or even numbers
#         def is_valid_increment(inc):
#             # Convert to float if not already
#             inc_float = float(inc)
#             # Check if inc is 0.00 or 0.05
#             if inc_float in [0.00, -0.05, 0.05]:
#                 return True
#             # Check if inc is an even integer
#             if int(inc_float * 1000) % 2 == 0:
#                 return True
#             return False

#         filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]

#         for increment in filtered_increments:
#             subset = df[df['increment'] == increment]
#             plt.plot(subset['energy_widths'], subset['energy_value_diff'], label=str(fr'$d_{{ms}}$ = {increment}m'))

#         if xlim is not None:
#             plt.xlim(xlim)
#         if ylim is not None:
#             plt.ylim(ylim)
#         plt.xlabel(plot_x_label)
#         plt.ylabel(plot_y_label)
#         plt.title(plot_title)
#         plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncols=3)
#         plt.grid(True)
#         plt.tight_layout()
#         plt.show()

#     if isinstance(df, list):
#         for i, single_df in enumerate(df):
#             if 'vector_direction' in single_df.columns:
#                 vector_dir = single_df['vector_direction'].dropna().unique()
#                 plot_title_updated = str(
#                     'Enclosed Energy as a Function of Reciever Width'
#                     + '\n'
#                     + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
#                 )
#             df_with_diff = add_energy_value_diff_column(single_df)
#             energy_value_diff_plot2(df_with_diff, plot_title=plot_title_updated)

#     else:
#         df_with_diff = add_energy_value_diff_column(df)
#         energy_value_diff_plot2(df_with_diff)


# plot_energy_value_diff_2(dfs)

# ######## PLOT TYPE 6 : Enclosed Energy Difference of reduced parameter variation (half as much of variation plotted) with reduced legend ################################

# # # create column with energy difference
# # df_with_diff = add_energy_value_diff_column(df)
# # print(df_with_diff)

# def plot_energy_value_diff_3(df):
#     def energy_value_diff_plot_3(df,
#                                  xlim = None,
#                                  ylim = None,
#                                  plot_x_label= 'Reciever Width (m)',
#                                  plot_y_label= 'Difference in Enclosed Energy (fraction)',
#                                  plot_title= 'Difference in Enclosed Energy as a Function of Reciever Width'):

#         plt.figure(figsize=(10, 6))

#         # Define the special increments and their colors
#         special_increments = {0.0: 'red', -0.05: 'black', 0.05: 'black'}

#         # Get unique increments
#         unique_increments = df['increment'].unique()

#         # Filter increments: keep those that are 0.00, 0.05, -0.05, or even numbers (times 1000)
#         def is_valid_increment(inc):
#             inc_float = float(inc)
#             if inc_float in special_increments:
#                 return True
#             if int(inc_float * 1000) % 2 == 0:
#                 return True
#             return False

#         filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]

#         # Keep track of which special increments have been plotted (for legend)
#         plotted_special = set()

#         for increment in filtered_increments:
#             subset = df[df['increment'] == increment]

#             if increment not in special_increments:
#                 color = 'gray'
#                 label = None  # No legend for gray lines
#             else:
#                 color = special_increments[increment]
#                 label = str(increment) if increment not in plotted_special else None
#                 plotted_special.add(increment)

#             plt.plot(subset['energy_widths'], subset['energy_value_diff'], color=color, label=label)

#         if xlim is not None:
#             plt.xlim(xlim)
#         if ylim is not None:
#             plt.ylim(ylim)
#         plt.xlabel(plot_x_label)
#         plt.ylabel(plot_y_label)
#         plt.title(plot_title)
#         plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncol=1)
#         plt.grid(True)
#         plt.tight_layout()
#         plt.show()

#     if isinstance(df,list):
#         for i, single_df in enumerate(df):
#             if 'vector_direction' in single_df.columns:
#                 vector_dir = single_df['vector_direction'].dropna().unique()
#                 plot_title_updated = str(
#                     'Enclosed Energy as a Function of Reciever Width'
#                     + '\n'
#                     + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
#                     )
#             df_with_diff = add_energy_value_diff_column(single_df)
#             energy_value_diff_plot_3(df_with_diff,
#                              plot_title= plot_title_updated)

#     else:
#         df_with_diff = add_energy_value_diff_column(df)
#         energy_value_diff_plot_3(df_with_diff)

# plot_energy_value_diff_3(dfs)


# def plot_energy_value_diff_4(df):

#     def energy_value_diff_plot_4(df,
#                                  xlim = None,
#                                  ylim = None,
#                                  plot_x_label= 'Reciever Width (m)',
#                                  plot_y_label= 'Difference in Enclosed Energy (fraction)',
#                                  plot_title= 'Difference in Enclosed Energy as a Function of Reciever Width'):
#         plt.figure(figsize=(10, 6))

#         magnitudes = [0.01 * i for i in range(1, 6)]

#         # Use a more saturated colormap like 'viridis'
#         cmap = plt.get_cmap('viridis')

#         # Normalize magnitudes from 0.01 to 0.05
#         norm = plt.Normalize(min(magnitudes), max(magnitudes))

#         # Gamma correction to darken colors (gamma < 1)
#         gamma = 0.5

#         unique_increments = df['increment'].unique()

#         def is_valid_increment(inc):
#             inc_float = float(inc)
#             if any(np.isclose(abs(inc_float), mag) for mag in magnitudes):
#                 return True
#             if int(inc_float * 1000) % 2 == 0:
#                 return True
#             return False

#         filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]

#         plotted_magnitudes = set()

#         for increment in filtered_increments:
#             subset = df[df['increment'] == increment]
#             inc_float = float(increment)
#             abs_inc = abs(inc_float)

#             if any(np.isclose(abs_inc, mag) for mag in magnitudes):
#                 norm_val = norm(abs_inc)
#                 # Apply gamma correction
#                 norm_val = norm_val**gamma
#                 norm_val = np.clip(norm_val, 0, 1)
#                 base_color = cmap(norm_val)

#                 if inc_float > 0:
#                     color = base_color
#                 else:
#                     white = np.array([1, 1, 1, 1])
#                     base_color_arr = np.array(base_color)
#                     color = 0.6 * base_color_arr + 0.4 * white
#                     color = tuple(color)

#                 label = fr'$d_{{ms}}$ = {increment}m' if abs_inc not in plotted_magnitudes else None
#                 plotted_magnitudes.add(abs_inc)

#                 plt.plot(subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2.5, label=label)
#             else:
#                 plt.plot(subset['energy_widths'], subset['energy_value_diff'], color='lightgray', linewidth=0.8)

#         if xlim is not None:
#             plt.xlim(xlim)
#         if ylim is not None:
#             plt.ylim(ylim)
#         plt.xlabel(plot_x_label)
#         plt.ylabel(plot_y_label)
#         plt.title(plot_title)
#         plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncol=1)
#         plt.grid(True)
#         plt.tight_layout()
#         plt.show()

#     if isinstance(df,list):
#         for i, single_df in enumerate(df):
#             if 'vector_direction' in single_df.columns:
#                 vector_dir = single_df['vector_direction'].dropna().unique()
#                 plot_title_updated = str(
#                     'Enclosed Energy as a Function of Reciever Width'
#                     + '\n'
#                     + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
#                     )
#             df_with_diff = add_energy_value_diff_column(single_df)
#             energy_value_diff_plot_4(df_with_diff,
#                              plot_title= plot_title_updated)

#     else:
#         df_with_diff = add_energy_value_diff_column(df)
#         energy_value_diff_plot_4(df_with_diff)

# plot_energy_value_diff_4(dfs)


# def plot_energy_value_diff_5(df):

#     def energy_value_diff_plot_5(df,
#                                  xlim = None,
#                                  ylim = None,
#                                  plot_x_label= 'Reciever Width (m)',
#                                  plot_y_label= 'Difference in Enclosed Energy (fraction)',
#                                  plot_title= 'Difference in Enclosed Energy as a Function of Reciever Width'):

#         plt.figure(figsize=(10, 6))

#         magnitudes = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
#         cmap = plt.get_cmap('Blues')

#         # Adjust normalization to avoid very light colors (start from 0.015 instead of 0.01)
#         norm = plt.Normalize(0.015, max(magnitudes))

#         unique_increments = df['increment'].unique()

#         def is_valid_increment(inc):
#             inc_float = float(inc)
#             if any(np.isclose(abs(inc_float), mag) for mag in magnitudes):
#                 return True
#             if int(inc_float * 1000) % 2 == 0:
#                 return True
#             return False

#         filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]

#         plotted_magnitudes = set()

#         for increment in filtered_increments:
#             subset = df[df['increment'] == increment]
#             inc_float = float(increment)
#             abs_inc = abs(inc_float)

#             if any(np.isclose(abs_inc, mag) for mag in magnitudes):
#                 # Normalize with adjusted norm
#                 norm_val = norm(abs_inc)
#                 # Clip norm_val to [0,1] just in case
#                 norm_val = np.clip(norm_val, 0, 1)
#                 base_color = cmap(norm_val)

#                 if inc_float > 0:
#                     color = base_color
#                 else:
#                     white = np.array([1, 1, 1, 1])
#                     base_color_arr = np.array(base_color)
#                     color = 0.6 * base_color_arr + 0.4 * white
#                     color = tuple(color)

#                 label = fr'$d_{{ms}}$ = {increment}m' if abs_inc not in plotted_magnitudes else None
#                 plotted_magnitudes.add(abs_inc)

#                 plt.plot(subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2, label=label)
#             else:
#                 plt.plot(subset['energy_widths'], subset['energy_value_diff'], color='lightgray', linewidth=0.8)


#         if xlim is not None:
#             plt.xlim(xlim)
#         if ylim is not None:
#             plt.ylim(ylim)
#         plt.xlabel(plot_x_label)
#         plt.ylabel(plot_y_label)
#         plt.title(plot_title)
#         plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncol=1)
#         plt.grid(True)
#         plt.tight_layout()
#         plt.show()

#     if isinstance(df,list):
#         for i, single_df in enumerate(df):
#             if 'vector_direction' in single_df.columns:
#                 vector_dir = single_df['vector_direction'].dropna().unique()
#                 plot_title_updated = str(
#                     'Enclosed Energy as a Function of Reciever Width'
#                     + '\n'
#                     + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
#                     )
#             df_with_diff = add_energy_value_diff_column(single_df)
#             energy_value_diff_plot_5(df_with_diff,
#                              plot_title= plot_title_updated)

#     else:
#         df_with_diff = add_energy_value_diff_column(df)
#         energy_value_diff_plot_5(df_with_diff)

# plot_energy_value_diff_5(dfs)


def plot_energy_value_diff_6(
    df,
    colorgrading='twilight_shifted',
    xlim=None,
    ylim=None,
    plot_x_label='Reciever Width (m)',
    plot_y_label='Difference in Enclosed Energy (fraction)',
    plot_title='Difference in Enclosed Energy as a Function of Reciever Width',
):

    def energy_value_diff_plot_6(df, plot_title=plot_title):

        plt.figure(figsize=(10, 6))

        magnitudes = [0.01 * i for i in range(1, 6)]
        cmap = plt.get_cmap(colorgrading)
        norm = plt.Normalize(min(magnitudes), max(magnitudes))
        gamma = 0.8  # gamma correction for darker colors

        unique_increments = df['increment'].unique()

        def is_valid_increment(inc):
            inc_float = float(inc)
            if any(np.isclose(abs(inc_float), mag) for mag in magnitudes):
                return True
            if int(inc_float * 1000) % 2 == 0:
                return True
            if inc_float == 0.00 or 0.000:
                return True
            return False

        filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]

        # Track which increments have been labeled in legend (both positive and negative)
        labeled_increments = set()

        for increment in filtered_increments:
            subset = df[df['increment'] == increment]
            inc_float = float(increment)
            abs_inc = abs(inc_float)

            if any(np.isclose(abs_inc, mag) for mag in magnitudes):
                norm_val = norm(abs_inc)
                norm_val = norm_val**gamma
                norm_val = np.clip(norm_val, 0, 1)
                base_color = cmap(norm_val)

                if inc_float > 0:
                    color = base_color  # darker for positive
                    label = fr'$d_{{ms}}$ = +{increment}m'
                elif inc_float == 0.00 or 0.000:
                    color = 'red'  # darker for positive
                    label = fr'$d_{{ms}}$ = +{increment}m'

                else:
                    # lighter for negative: blend with white
                    white = np.array([1, 1, 1, 1])
                    base_color_arr = np.array(base_color)
                    color = 0.3 * base_color_arr + 0.6 * white
                    color = tuple(color)
                    label = fr'$d_{{ms}}$ = {increment}m'  # negative sign included

                # Add label only once per increment value
                if increment not in labeled_increments:
                    plt.plot(
                        subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2.5, label=label
                    )
                    labeled_increments.add(increment)
                else:
                    plt.plot(subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2.5)
            else:
                plt.plot(subset['energy_widths'], subset['energy_value_diff'], color='lightgray', linewidth=0.8)

        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncol=1)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
            df_with_diff = add_energy_value_diff_column(single_df)
            energy_value_diff_plot_6(df_with_diff, plot_title=plot_title_updated)

    else:
        df_with_diff = add_energy_value_diff_column(df)
        energy_value_diff_plot_6(df_with_diff)


plot_energy_value_diff_6(dfs)


def plot_energy_value_diff_7(df, output_dir, colorgrading='Spectral', xlim=None, ylim=None, save_plot=False):
    def energy_value_diff_plot_7(
        df,
        output_dir=output_dir,
        colorgrading=colorgrading,
        save_plot=save_plot,
        colored_increments=None,
        imagefile_name='enclosed_energy_diff_plot_minimal',
        plot_x_label='Reciever Width (m)',
        plot_y_label='Difference in Enclosed Energy (fraction)',
        plot_title=str(
            'Enclosed Energy as a Function of Reciever Width' + '\n' + fr'and Mirror to Screen Distance $d_{{ms}} (m)$'
        ),
    ):

        plt.figure(figsize=(10, 6))

        if colored_increments:
            magnitudes = colored_increments
        else:
            magnitudes = [0.01 * i for i in range(-5, 6)]
        cmap = plt.get_cmap(colorgrading)
        norm = plt.Normalize(min(magnitudes), max(magnitudes))
        gamma = 0.8  # gamma correction for darker colors

        unique_increments = df['increment'].unique()

        def is_valid_increment(inc):
            inc_float = float(inc)
            if any(np.isclose(abs(inc_float), mag) for mag in magnitudes):
                return True
            if int(inc_float * 1000) % 2 == 0:
                return True
            return False

        filtered_increments = [inc for inc in unique_increments if is_valid_increment(inc)]
        filtered_increments = sorted(filtered_increments, reverse=True)
        # Track which increments have been labeled in legend (both positive and negative)
        labeled_increments = set()
        for increment in filtered_increments:
            subset = df[df['increment'] == increment]
            inc_float = float(increment)
            abs_inc = abs(inc_float)

            if any(np.isclose(abs_inc, mag) for mag in magnitudes):
                norm_val = norm(abs_inc)
                norm_val = norm_val**gamma
                norm_val = np.clip(norm_val, 0, 1)
                base_color = cmap(norm_val)

                if inc_float > 0:
                    color = base_color  # darker for positive
                    label = fr'$d_{{ms}}$ = +{increment}m'

                elif inc_float == 0.0:
                    color = 'red'  # darker for positive
                    label = fr'$d_{{ms}}$ = +{increment}m'
                else:
                    # lighter for negative: blend with white
                    white = np.array([1, 1, 1, 1])
                    base_color_arr = np.array(base_color)
                    color = 0.3 * base_color_arr + 0.6 * white
                    color = tuple(color)
                    label = fr'$d_{{ms}}$ = {increment}m'  # negative sign included

                # Add label only once per increment value
                if increment not in labeled_increments:
                    plt.plot(
                        subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2.5, label=label
                    )
                    labeled_increments.add(increment)
                else:
                    plt.plot(subset['energy_widths'], subset['energy_value_diff'], color=color, linewidth=2.5)
            else:
                plt.plot(subset['energy_widths'], subset['energy_value_diff'], color='lightgray', linewidth=0.8)
        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Increment', fontsize='xx-small', ncol=1)
        plt.grid(True)
        plt.tight_layout()
        if save_plot == True:
            directory = find_or_create_analysis_folder(output_dir)
            image_file_name = 'enclosed_energy_diff_plot_minimal' if imagefile_name is None else imagefile_name
            save_path = os.path.join(directory, f'{image_file_name}.png')
            plt.savefig(save_path, dpi=300)
            print(f'Enclosed Energy Difference Plot saved in {directory}')
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
                imagefile_name_vectorized = f'enclosed_energy_diff_plot_minimal_{vector_dir[0]}'
            df_with_diff = add_energy_value_diff_column(single_df)
            energy_value_diff_plot_7(
                df_with_diff, plot_title=plot_title_updated, imagefile_name=imagefile_name_vectorized
            )

    else:
        df_with_diff = add_energy_value_diff_column(df)
        energy_value_diff_plot_7(df_with_diff)


plot_energy_value_diff_7(dfs, analysis_folder, ylim=(-0.03, 0.03), save_plot=True)

######## PLOT TYPE 7 :  Scatter Plot of Enclosed Energy Difference of reduced parameter variation as a function of increment  ################################

# # create column with energy difference
# df_with_diff = add_energy_value_diff_column(df)
# print(df_with_diff)


def plot_increment_vs_energy_diff(df, output_dir, save_plot=False, imagefile_name=None, xlim=None, ylim=None):

    def increment_vs_energy_diff_plot1(
        df,
        output_dir=output_dir,
        plot_x_label=fr'Incremental change in the Mirror to Screen Distance $d_{{ms}}$ (m)',
        plot_y_label='Difference in Enclosed Energy (fraction)',
        plot_title=str(
            'Difference in Enclosed Energy as a Function of Increment Change in'
            + '\n'
            + fr'Mirror to Screen Distance $d_{{ms}}$ (Energy Width between 0.48 to 0.51) (m)'
        ),
        imagefile_name=imagefile_name,
        save_plot=save_plot,
    ):
        # Filter for energy_widths between 0.2 and 0.6
        filtered_df = df[(df['energy_widths'] >= 0.48) & (df['energy_widths'] <= 0.51)]

        plt.figure(figsize=(8, 6))

        # Scatter plot of increment vs energy_value_diff
        plt.scatter(filtered_df['increment'], filtered_df['energy_value_diff'], alpha=0.7)
        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)
        plt.grid(True)
        plt.tight_layout()
        if save_plot == True:
            directory = find_or_create_analysis_folder(output_dir)
            image_file_name = (
                'enclosed_energy_and_increment_diff_plot_minimal' if imagefile_name is None else imagefile_name
            )
            save_path = os.path.join(directory, f'{image_file_name}.png')
            plt.savefig(save_path, dpi=300)
            print(f'Enclosed Energy Difference Plot saved in {directory}')
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Increment'
                    + '\n'
                    + fr'in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                    + '\n'
                    + '(at Reciever Width Between .48 and .51)'
                )
                x_label = fr'Incremental change in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                imagefile_name_vectorized = fr'enclosed_energy_and_increment_diff_plot_minimal_{vector_dir[0]}'
            df_with_diff = add_energy_value_diff_column(single_df)
            increment_vs_energy_diff_plot1(
                df_with_diff,
                plot_x_label=x_label,
                plot_title=plot_title_updated,
                save_plot=save_plot,
                imagefile_name=imagefile_name_vectorized,
            )

    else:
        df_with_diff = add_energy_value_diff_column(df)
        increment_vs_energy_diff_plot1(df_with_diff)


plot_increment_vs_energy_diff(dfs, analysis_folder, ylim=(-0.03, 0.03), save_plot=True)


######## PLOT TYPE 8 :  Scatter Plot of Enclosed Energy Difference of reduced parameter variation as a function of increment with curve fit line ################################

# # create column with energy difference
# df_with_diff = add_energy_value_diff_column(df)
# print(df_with_diff)


def plot_increment_vs_energy_diff_2(df, output_dir, xlim=None, ylim=None, save_plot=False, imagefile_name=None):

    def increment_vs_energy_diff_plot2(
        df,
        plot_x_label=fr'Incremental change in the Mirror to Screen Distance $d_{{ms}}$ (m)',
        plot_y_label='Difference in Enclosed Energy (fraction)',
        plot_title=str(
            'Difference in Enclosed Energy as a Function of Increment Change in'
            + '\n'
            + fr'Mirror to Screen Distance $d_{{ms}}$ (Energy Width between 0.48 to 0.51) (m)'
        ),
        save_plot=save_plot,
    ):
        # Filter for energy_widths between 0.2 and 0.6
        filtered_df = df[(df['energy_widths'] >= 0.48) & (df['energy_widths'] <= 0.51)]

        plt.figure(figsize=(8, 6))

        # Fit a 3rd-degree polynomial (cubic curve)
        coefficients = np.polyfit(filtered_df['increment'], filtered_df['energy_value_diff'], deg=3)
        polynomial = np.poly1d(coefficients)

        # Generate high-resolution curve
        x_curve = np.linspace(-0.05, 0.05, 200)
        y_curve = polynomial(x_curve)

        # Scatter plot of increment vs energy_value_diff
        plt.scatter(filtered_df['increment'], filtered_df['energy_value_diff'], alpha=0.2)
        plt.plot(x_curve, y_curve, color='red', label='Cubic Polyfit')
        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        plt.xlabel('Increment')
        plt.ylabel('Energy Value Difference')
        plt.title('Energy Value Difference vs Increment (Energy Width between 0.48 to 0.51)')
        plt.xlabel(plot_x_label)
        plt.ylabel(plot_y_label)
        plt.title(plot_title)
        plt.grid(True)
        plt.tight_layout()
        if save_plot == True:
            directory = find_or_create_analysis_folder(output_dir)
            image_file_name = (
                'enclosed_energy_and_increment_diff_fitted_plot' if imagefile_name is None else imagefile_name
            )
            save_path = os.path.join(directory, f'{image_file_name}.png')
            plt.savefig(save_path, dpi=300)
            print(f'Enclosed Energy Difference Plot saved in {directory}')
        plt.show()

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                plot_title_updated = str(
                    'Enclosed Energy as a Function of Reciever Width'
                    + '\n'
                    + fr'and camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                )
                x_label = fr'Incremental change in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                imagefile_name_vectorized = fr'enclosed_energy_and_increment_diff_fitted_plot_${{{vector_dir[0]}}}$'
                if imagefile_name is None:
                    imagefile_name = imagefile_name_vectorized
                else:
                    imagefile_name = f'{imagefile_name}_{vector_dir[0]}'
            df_with_diff = add_energy_value_diff_column(single_df)
            increment_vs_energy_diff_plot2(df_with_diff, plot_x_label=x_label, plot_title=plot_title_updated)

    else:
        df_with_diff = add_energy_value_diff_column(df)
        increment_vs_energy_diff_plot2(df_with_diff)


plot_increment_vs_energy_diff_2(dfs, analysis_folder, ylim=(-0.03, 0.03), save_plot=True)
