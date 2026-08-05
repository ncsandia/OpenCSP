"""

Summary
-------

This module is for tabulating and visualizing focal length differences during sensitivity analysis of SOFAST input parameters.

This script performs the following steps:

1. Finds and compiles a list of all JSON output filepaths from SOFAST analysis in the output directory
2. Extracts and tabulates all focal length data from JSON output files in the output directory.
3. If desired, saves tabulated data as a csv file in the parent directory under analysis folder.
4. Generates a tornado plot of all focal length differences for x, y, or both and stores it in analysis folder in the parent directory.


Libraries
---------
os
json
pandas

Examples
--------
To run the script, simply update the output directory file path and run the execution function:

            output_directory = "C:/Users/nichowd/Desktop/single_parameter_SA/002_output/"

            focal_length_comparison(
                                    output_dir
                                    file_end_key='_measurement_statistics.json',
                                    key='focal_lengths_parabolic_xy',
                                    variable_compared = 'x',
                                    default_data = None,
                                    save_data=False,
                                    save_plot=False)

Notes
-----
    - The argument 'default_data = ' will find the differences of x or y from the desired row value.
        - by default this argument is set to None
        - the argument should be a string of the value that will match a value in the settings column.
    - The argument save_data and save_plot will save data and or images in an analysis folder in the parent directory.


Expected Outputs
----------------
This code can save the resulting dataset and images files to an analysis folder in the parent directory in the following subfolders:

    focal_length_data_filepaths - csv file that contains all filepaths for focal length data in the output directory.
    focal_length_comparison.csv - csv file that contains a compiled dataset of all focal length data from output directory.
    tornado_plot_focal_length_xxx.png - png image of torando plot(s)

    Note: xxx is the image file name suffix which refers to whether the tornado plot is a plot of x, y, delta_x, or delta_y

AI Acknowledgement
------------------
SandiaAI was used to faciliate code development and docstring documentation.

"""

####### IMPORT LIBRARIES ######


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


# ## check if find_files function is working

# test_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_21_single_param_sa_m_dist_optic_screen/002_output"
# # files = find_files(
# #     test_directory, file_end_key='_measurement_statistics.json', save_json_filepath=True)
# # print(files)
# files, file_paths_test = find_files(
#     test_directory, file_end_key='_measurement_statistics.json', save_json_filepath=True
# )
# print(files)
# print(file_paths_test)


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


# # # check if tabulate_data_from_files function is working without excluding substrings
# # key_to_extract = 'focal_lengths_parabolic_xy'  # Replace with your key
# # df = tabulate_data_from_files(files, key_to_extract, name_end = '')
# # print(df)

# # check if tabulate_data_from_files function is working excluding substrings
# key_to_extract = 'focal_lengths_parabolic_xy'  # Replace with your key
# df = tabulate_data_from_files(files, key_to_extract, name_end='_d', exclude_substrings=None)
# print(df)


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


# dfs = extend_settings_column(df, 'settings')
# print(dfs)

# df = extend_settings_column(df, 'settings')
# print(df)


def focal_length_line_plot(
    df,
    directory,
    variable_compared='x',
    default_data=None,
    xlabel=None,
    save_plot=False,
    plot_title_assigned=None,
    imagefile_name=None,
):
    def plot_focal_length(
        x, y, legend_y, xlabel, ylabel, title, imagefile_name, y2=None, legend_y2=None, save_plot=save_plot
    ):
        fig, ax = plt.subplots()
        ax.plot(x, y, color='tab:blue')
        ax.tick_params(axis='x', labelrotation=45, labelsize=9)
        ax.tick_params(axis='x', labelsize=10)
        if y2 is not None:
            ax.plot(x, y2, color='tab:green')
            ax.legend([legend_y, legend_y2])
        else:
            ax.legend([legend_y])
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
        ax.grid()
        plt.tight_layout()
        if save_plot == True:
            fig.savefig(f'{imagefile_name}.png')
            save_path = os.path.join(directory, f'{imagefile_name}.png')
            plt.savefig(save_path, dpi=300)
            print(f'Tornado plot of Y of focal length saved in {directory}')
        plt.show()

    def process_focal_length_plot(
        single_df, variable_compared, xlabel, default_data, imagefile_name, plot_title_assigned
    ):
        sorted_df = single_df.sort_values(by='increment')
        print(sorted_df.to_string())
        # Data for plotting
        increment = sorted_df['increment']
        focal_length_x = sorted_df['x']
        focal_length_y = sorted_df['y']

        plot_x_label = 'incremental change (m)' if xlabel is None else xlabel
        plot_title_given = 'Focal Length Variation (m)' if plot_title_assigned is None else plot_title_assigned

        if variable_compared == 'x':
            y = focal_length_x
            plot_y_label = fr'$f_x$ (m)'
            plot_imagefile_name = 'focal_length_line_plot_x'
            plot_legend_y = fr'$f_x$'
            plot_legend_y2 = None
        elif variable_compared == 'y':
            y = focal_length_y
            plot_y_label = fr'$f_y$ (m)'
            plot_imagefile_name = 'focal_length_line_plot_y'
            plot_legend_y = fr'$f_y$'
            plot_legend_y2 = None
        elif variable_compared == 'both':
            y = focal_length_x
            y2 = focal_length_y
            plot_y_label = fr'$f_x$ (m)'
            plot_y2_label = fr'$f_y$ (m)'
            plot_imagefile_name = 'focal_length_line_plot_x_and_y'
            plot_legend_y = fr'$f_x$'
            plot_legend_y2 = fr'$f_y$'
        else:
            if default_data is not None:
                default_row = sorted_df[sorted_df['settings'].str.contains(default_data)].iloc[0]
                print("default row: \n", default_row)

                # Calculate deltas relative to default x and y
                sorted_df['delta_x'] = sorted_df['x'] - default_row['x']
                sorted_df['delta_y'] = sorted_df['y'] - default_row['y']

                focal_length_delta_x = sorted_df['delta_x']
                focal_length_delta_y = sorted_df['delta_y']
                print(sorted_df)

                if variable_compared == 'delta_x':
                    y = focal_length_delta_x
                    plot_y_label = fr"$\Delta$$f_x$ (m)"
                    plot_imagefile_name = 'focal_length_line_plot_delta_x'
                    plot_legend_y = fr'$\Delta$$f_x$'
                    plot_legend_y2 = None
                elif variable_compared == 'delta_y':
                    y = focal_length_delta_y
                    plot_y_label = fr'$\Delta$$f_y$ (m)'
                    plot_imagefile_name = 'focal_length_line_plot_delta_y'
                    plot_legend_y = fr'$\Delta$$f_y$'
                    plot_legend_y2 = None
                elif variable_compared == 'delta':
                    y = focal_length_delta_x
                    y2 = focal_length_delta_y
                    plot_y_label = fr'$\Delta$$f_{{xy}}$ (m)'
                    # plot_y2_label = fr'$f_\Deltay$'
                    plot_imagefile_name = 'focal_length_line_plot_delta_x_and_y'
                    plot_legend_y = fr'$\Delta$$f_x$'
                    plot_legend_y2 = fr'$\Delta$$f_y$'
                else:
                    raise ValueError('incorrect argument for variable_compared.')
            else:
                raise ValueError('must include default_data')

        if imagefile_name != None:
            plot_imagefile_name = f'{imagefile_name}_{plot_imagefile_name}'
        else:
            plot_imagefile_name = plot_imagefile_name

        if variable_compared == 'both' or variable_compared == 'delta':
            plot_focal_length(
                increment,
                y,
                y2=y2,
                xlabel=plot_x_label,
                ylabel=plot_y_label,
                title=plot_title_given,
                imagefile_name=plot_imagefile_name,
                legend_y=plot_legend_y,
                legend_y2=plot_legend_y2,
            )
        else:
            plot_focal_length(
                increment,
                y,
                xlabel=plot_x_label,
                ylabel=plot_y_label,
                title=plot_title_given,
                imagefile_name=plot_imagefile_name,
                legend_y=plot_legend_y,
            )

    if isinstance(df, list):
        for i, single_df in enumerate(df):
            if 'vector_direction' in single_df.columns:
                vector_dir = single_df['vector_direction'].dropna().unique()
                x_label = (
                    fr'incremental change in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                    if len(vector_dir) == 1
                    else 'incremental change (m)'
                )
                if plot_title_assigned is None:
                    plot_title_assigned_updated = str(
                        'Focal Length Variation as a function of change '
                        + '\n'
                        + fr'in the camera to screen origin $\vec{{v}}_{{{vector_dir[0]}}}$ (m)'
                    )

                print(f"plotting with vector direction for DataFrame {i}/{len(df)}")

                process_focal_length_plot(
                    single_df,
                    variable_compared,
                    xlabel=x_label,
                    plot_title_assigned=plot_title_assigned_updated,
                    imagefile_name=f'Focal_Length_Comparison_{vector_dir[0]}',
                    default_data=default_data,
                )
    else:
        process_focal_length_plot(df, variable_compared, default_data=default_data)


# analysis_dir = find_or_create_analysis_folder(test_directory)
# focal_length_line_plot(
#     df,
#     directory=analysis_dir,
#     variable_compared='delta',
#     default_data='0b00',
#     xlabel=fr'incremental change in distance from optic to screen $d_{{ms}}$ (m)',
#     plot_title_assigned=fr'Focal Length Variation (m)',
#     save_plot=True,
# )


########################################## MAIN FUNCTION ##########################################
#### DO NOT MODIFY


def focal_length_comparison(
    output_dir,
    input_file_path=None,
    save_json_filepath=False,
    file_end_key='_measurement_statistics.json',
    key='focal_lengths_parabolic_xy',
    name_start='sa_',
    name_end=None,
    variable_compared='x',
    default_data=None,
    save_data=False,
    save_plot=False,
):

    analysis_dir = find_or_create_analysis_folder(output_dir)

    if input_file_path is None:
        files = find_files(output_dir, file_end_key, save_json_filepath, file_name=None)
        df = tabulate_data_from_files(files, key, name_start, name_end)
        df = extend_settings_column(df)
        print(df)

    else:
        with open(input_file_path, mode='r', newline='', encoding='utf-8') as filepaths_csv:
            reader = csv.reader(filepaths_csv)
            next(reader)  # Skip the header row if necessary
            # Extract only the first column (index 0)
            files = [row[0] for row in reader]
        print('focal length comparison performed on provided filepaths:', '\n', files)
        df = tabulate_data_from_files(files, key, name_start, name_end)
        df = extend_settings_column(df)
        print(df)

    if save_data:
        if isinstance(df, list):
            for i, single_df in enumerate(df):
                if 'vector_direction' in single_df.columns:
                    vector_dir = single_df['vector_direction'].dropna().unique()
                if save_data:
                    csv_file_name = f'focal_length_comparison_subset_{vector_dir}.csv'
                    csv_path = os.path.join(analysis_dir, csv_file_name)
                    single_df.to_csv(csv_path, index=False)
                    print(f"focal length data saved to {csv_path}")
        else:
            csv_path = os.path.join(analysis_dir, 'focal_length_comparison.csv')
            df.to_csv(csv_path, index=False)
            print(f"focal length data saved to {csv_path}")

    focal_length_line_plot(
        df,
        directory=analysis_dir,
        variable_compared=variable_compared,
        default_data=default_data,
        plot_title_assigned=None,
        save_plot=save_plot,
    )


########################################## EXECUTION OF MAIN FUNCTION ##########################################
##### Update filepaths for the following variables #####

# if focal length comparison is assessed for all focal length ouput data in output data, update output directory
# update output directory below in which all JSON files for the SOFAST focal length output are stored.
output_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"


# after updating the directory, run the focal_length_comparisons with updated arguments.
# See focal_length_comparisons() docstring for arguments

focal_length_comparison(
    output_dir=output_directory,
    input_file_path=None,
    file_end_key='_measurement_statistics.json',
    key='focal_lengths_parabolic_xy',
    name_end='_d',
    variable_compared='delta',
    default_data='0b00',
    save_data=False,
    save_plot=True,
    save_json_filepath=False,
)

########################################## ALTERNATIVE APPROACH ##########################################
# # uncomment lines here and below if running alternative approach (use ctrl + /)
# # if focal length comparison is assessed for a subset of focal length filepaths--not all outputs in output directory
#     # then first run the helper function below to compile your filepaths and
#         # delete any rows of filepaths you do not want to analyze - do not change file name.

# allfilepaths, pathlist_csvpath = find_files(output_dir= output_directory, file_end_key='_measurement_statistics.json', save_json_filepath=True, file_name= "subsetted_focal_length_file_paths")

#         #make the changes you want to make to the subsetted_focal_length_file_paths.csv file in the analysis folder in your parent directory.
#         ### note: do not change the name of the file.
#         ##### after deleting file paths you are not interested in analyzing proceed to use the following execution program:
# Note: you can change the default_data argument to either None or to the settings referring to a desired baseline measurement

# focal_length_comparison(output_dir=output_directory, input_file_path= pathlist_csvpath, default_data= 'mdAAAn32')
