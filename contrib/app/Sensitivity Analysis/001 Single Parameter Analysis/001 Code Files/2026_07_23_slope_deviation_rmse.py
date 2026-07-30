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


# # check if find_files function is working

test_directory = "C:/Users/nichowd/Desktop/Experiments/2026_07_22_single_param_sa_o_v_cam_screen_cam/002_output"

files, file_paths_test = find_files(
    test_directory,
    file_end_key='slope_deviation_image_x.h5',
    save_json_filepath=True,
    file_name="pathlist_slope_deviation_x",
)
print(files)

print(file_paths_test)


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


def process_hdf5_files(file_path_list, keyword, name_start, name_end=None, compare_to_baseline=True):
    results = []
    for file_path in file_path_list:
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
    return rmse_df


df = process_hdf5_files(file_path_list=files, keyword='image_x', name_start='sa_')
print(df)


#############################################################################################################################################

import matplotlib.pyplot as plt
import seaborn as sns

# Assuming your DataFrame is named df
# Example: df = your DataFrame with columns: settings, RMSE, row, sign, increment, vector_direction

# Set plot style
sns.set(style="whitegrid")

df = pd.DataFrame(df)
df2 = df.sort_values(by='increment')
df2

fig, axes = plt.subplots(3, 2, figsize=(14, 18))

# 1. Bar plot: Mean RMSE by sign
sns.barplot(x='sign', y='RMSE', data=df2, ax=axes[0, 0], ci='sd', palette='muted')
axes[0, 0].set_title('Mean RMSE by Sign')
axes[0, 0].set_xlabel('Sign')
axes[0, 0].set_ylabel('Mean RMSE')

# plt.tight_layout()
# plt.show()

# 2. Dot plot: RMSE by sign
sns.stripplot(x='sign', y='RMSE', data=df2, ax=axes[0, 1], jitter=True, palette='muted', edgecolor='gray', size=5)
axes[0, 1].set_title('RMSE Distribution by Sign')
axes[0, 1].set_xlabel('Sign')
axes[0, 1].set_ylabel('RMSE')

plt.tight_layout()
plt.show()

# 3. Bar plot: Mean RMSE by increment
# Convert increment to float if not already
df2['increment'] = df2['increment'].astype(float)

sns.barplot(x='increment', y='RMSE', data=df2, ax=axes[1, 0], ci='sd', palette='coolwarm')
axes[1, 0].set_title('Mean RMSE by Increment')
axes[1, 0].set_xlabel('Increment')
axes[1, 0].set_ylabel('Mean RMSE')
axes[1, 0].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# 4. Dot plot: RMSE by increment
sns.stripplot(
    x='increment', y='RMSE', data=df2, ax=axes[1, 1], jitter=True, palette='coolwarm', edgecolor='gray', size=5
)
axes[1, 1].set_title('RMSE Distribution by Increment')
axes[1, 1].set_xlabel('Increment')
axes[1, 1].set_ylabel('RMSE')
axes[1, 1].tick_params(axis='x', rotation=45)


plt.tight_layout()
plt.show()

# 5. Bar plot: Mean RMSE by vector_direction
sns.barplot(x='vector_direction', y='RMSE', data=df2, ax=axes[2, 0], ci='sd', palette='pastel')
axes[2, 0].set_title('Mean RMSE by Vector Direction')
axes[2, 0].set_xlabel('Vector Direction')
axes[2, 0].set_ylabel('Mean RMSE')

plt.tight_layout()
plt.show()

# 6. Dot plot: RMSE by vector_direction
sns.stripplot(
    x='vector_direction', y='RMSE', data=df2, ax=axes[2, 1], jitter=True, palette='pastel', edgecolor='gray', size=5
)
axes[2, 1].set_title('RMSE Distribution by Vector Direction')
axes[2, 1].set_xlabel('Vector Direction')
axes[2, 1].set_ylabel('RMSE')

plt.tight_layout()
plt.show()
##################################################################################################################################################

import matplotlib.pyplot as plt
import numpy as np

# Assuming your DataFrame is named df

# Prepare figure and axes
fig, axes = plt.subplots(3, 2, figsize=(14, 18))


# Helper function to get mean and std for groups
def group_stats(df, group_col):
    groups = df[group_col].unique()
    means = []
    stds = []
    for g in groups:
        vals = df.loc[df[group_col] == g, 'RMSE']
        means.append(vals.mean())
        stds.append(vals.std())
    return groups, means, stds


# 1. Bar plot: Mean RMSE by sign
groups, means, stds = group_stats(df, 'sign')
x = np.arange(len(groups))
axes[0, 0].bar(x, means, yerr=stds, capsize=5, color='skyblue')
axes[0, 0].set_xticks(x)
axes[0, 0].set_xticklabels(groups)
axes[0, 0].set_title('Mean RMSE by Sign')
axes[0, 0].set_xlabel('Sign')
axes[0, 0].set_ylabel('Mean RMSE')

# 2. Dot plot: RMSE by sign
for i, g in enumerate(groups):
    y = df.loc[df['sign'] == g, 'RMSE']
    x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
    axes[0, 1].plot(x_vals, y, 'o', alpha=0.6)
axes[0, 1].set_xticks(x)
axes[0, 1].set_xticklabels(groups)
axes[0, 1].set_title('RMSE Distribution by Sign')
axes[0, 1].set_xlabel('Sign')
axes[0, 1].set_ylabel('RMSE')

# 3. Bar plot: Mean RMSE by increment
# Sort increments for better visualization
df['increment'] = df['increment'].astype(float)
groups, means, stds = group_stats(df, 'increment')
sorted_idx = np.argsort(groups)
groups_sorted = groups[sorted_idx]
means_sorted = np.array(means)[sorted_idx]
stds_sorted = np.array(stds)[sorted_idx]
x = np.arange(len(groups_sorted))
axes[1, 0].bar(x, means_sorted, yerr=stds_sorted, capsize=5, color='salmon')
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels([f"{g:.3f}" for g in groups_sorted], rotation=45)
axes[1, 0].set_title('Mean RMSE by Increment')
axes[1, 0].set_xlabel('Increment')
axes[1, 0].set_ylabel('Mean RMSE')

# 4. Dot plot: RMSE by increment
for i, g in enumerate(groups_sorted):
    y = df.loc[df['increment'] == g, 'RMSE']
    x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
    axes[1, 1].plot(x_vals, y, 'o', alpha=0.6)
axes[1, 1].set_xticks(x)
axes[1, 1].set_xticklabels([f"{g:.3f}" for g in groups_sorted], rotation=45)
axes[1, 1].set_title('RMSE Distribution by Increment')
axes[1, 1].set_xlabel('Increment')
axes[1, 1].set_ylabel('RMSE')

# 5. Bar plot: Mean RMSE by vector_direction
groups, means, stds = group_stats(df, 'vector_direction')
x = np.arange(len(groups))
axes[2, 0].bar(x, means, yerr=stds, capsize=5, color='lightgreen')
axes[2, 0].set_xticks(x)
axes[2, 0].set_xticklabels(groups)
axes[2, 0].set_title('Mean RMSE by Vector Direction')
axes[2, 0].set_xlabel('Vector Direction')
axes[2, 0].set_ylabel('Mean RMSE')

# 6. Dot plot: RMSE by vector_direction
for i, g in enumerate(groups):
    y = df.loc[df['vector_direction'] == g, 'RMSE']
    x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
    axes[2, 1].plot(x_vals, y, 'o', alpha=0.6)
axes[2, 1].set_xticks(x)
axes[2, 1].set_xticklabels(groups)
axes[2, 1].set_title('RMSE Distribution by Vector Direction')
axes[2, 1].set_xlabel('Vector Direction')
axes[2, 1].set_ylabel('RMSE')

plt.tight_layout()
plt.show()

#########################

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

# Ensure increment is float
df['increment'] = df['increment'].astype(float)

fig, axes = plt.subplots(3, 1, figsize=(10, 18))

# 1. Dot plot: RMSE by sign
groups_sign = df['sign'].dropna().unique()
groups_sign = sorted(groups_sign)
x_sign = np.arange(len(groups_sign))

for i, g in enumerate(groups_sign):
    y = df.loc[df['sign'] == g, 'RMSE']
    x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
    axes[0].plot(x_vals, y, 'o', alpha=0.6, label=str(g))

axes[0].set_xticks(x_sign)
axes[0].set_xticklabels(groups_sign)
axes[0].set_title('RMSE Distribution by Sign', loc='left')
axes[0].set_xlabel('Sign')
axes[0].set_ylabel('RMSE')
axes[0].legend(title='Sign')

# 2. Dot plot: RMSE by increment, grouped by row and sign with legend

# Sort increments
increments_sorted = np.sort(df['increment'].dropna().unique())
x_inc = np.arange(len(increments_sorted))

# Create a color map for combinations of (row, sign)
unique_rows = sorted(df['row'].dropna().unique())
unique_signs = sorted(df['sign'].dropna().unique())

# Generate distinct colors for each (row, sign) pair
colors = cm.get_cmap('tab20')
color_map = {}
color_idx = 0
for r in unique_rows:
    for s in unique_signs:
        color_map[(r, s)] = colors(color_idx)
        color_idx += 1

for i, inc in enumerate(increments_sorted):
    subset = df[df['increment'] == inc]
    for (r, s), color in color_map.items():
        subsub = subset[(subset['row'] == r) & (subset['sign'] == s)]
        if not subsub.empty:
            y = subsub['RMSE']
            x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
            label = f"row={r}, sign={s}"
            # To avoid duplicate labels in legend, only label first time
            if not axes[1].get_legend_handles_labels()[1].count(label):
                axes[1].plot(x_vals, y, 'o', alpha=0.7, color=color, label=label)
            else:
                axes[1].plot(x_vals, y, 'o', alpha=0.7, color=color)

axes[1].set_xticks(x_inc)
axes[1].set_xticklabels([f"{inc:.3f}" for inc in increments_sorted], rotation=45)
axes[1].set_title('RMSE Distribution by Increment grouped by Row and Sign', loc='left')
axes[1].set_xlabel('Increment')
axes[1].set_ylabel('RMSE')
axes[1].legend(title='Row and Sign', bbox_to_anchor=(1.05, 1), loc='upper left')

# 3. Dot plot: RMSE by vector_direction
groups_vec = df['vector_direction'].dropna().unique()
groups_vec = sorted(groups_vec)
x_vec = np.arange(len(groups_vec))

for i, g in enumerate(groups_vec):
    y = df.loc[df['vector_direction'] == g, 'RMSE']
    x_vals = np.random.normal(i, 0.05, size=len(y))  # jitter
    axes[2].plot(x_vals, y, 'o', alpha=0.6, label=str(g))

axes[2].set_xticks(x_vec)
axes[2].set_xticklabels(groups_vec)
axes[2].set_title('RMSE Distribution by Vector Direction', loc='left')
axes[2].set_xlabel('Vector Direction')
axes[2].set_ylabel('RMSE')
axes[2].legend(title='Vector Direction')

plt.tight_layout()
plt.show()

#################

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Assuming df is your DataFrame and group_stats is defined as:
def group_stats(df, group_col):
    groups = df[group_col].unique()
    means = []
    stds = []
    for g in groups:
        vals = df.loc[df[group_col] == g, 'RMSE']
        means.append(vals.mean())
        stds.append(vals.std())
    return groups, means, stds


# Prepare figure with 2 columns: left for plots, right for table
fig = plt.figure(figsize=(14, 12))
grid = fig.add_gridspec(3, 2, width_ratios=[3, 2], wspace=0.3, hspace=0.5)

# Plot 1: Mean RMSE by sign (top-left)
ax1 = fig.add_subplot(grid[0, 0])
groups, means, stds = group_stats(df, 'sign')
x = np.arange(len(groups))
ax1.bar(x, means, yerr=stds, capsize=5, color='skyblue')
ax1.set_xticks(x)
ax1.set_xticklabels(groups)
ax1.set_title('Mean RMSE by Sign', loc='left')
ax1.set_xlabel('Sign')
ax1.set_ylabel('Mean RMSE')

# Plot 3: Mean RMSE by increment (middle-left)
ax2 = fig.add_subplot(grid[1, 0])
df['increment'] = df['increment'].astype(float)
groups, means, stds = group_stats(df, 'increment')
sorted_idx = np.argsort(groups)
groups_sorted = groups[sorted_idx]
means_sorted = np.array(means)[sorted_idx]
stds_sorted = np.array(stds)[sorted_idx]
x = np.arange(len(groups_sorted))
ax2.bar(x, means_sorted, yerr=stds_sorted, capsize=5, color='salmon')
ax2.set_xticks(x)
ax2.set_xticklabels([f"{g:.3f}" for g in groups_sorted], rotation=45)
ax2.set_title('Mean RMSE by Increment', loc='left')
ax2.set_xlabel('Increment')
ax2.set_ylabel('Mean RMSE')

# Plot 5: Mean RMSE by vector_direction (bottom-left)
ax3 = fig.add_subplot(grid[2, 0])
groups, means, stds = group_stats(df, 'vector_direction')
x = np.arange(len(groups))
ax3.bar(x, means, yerr=stds, capsize=5, color='lightgreen')
ax3.set_xticks(x)
ax3.set_xticklabels(groups)
ax3.set_title('Mean RMSE by Vector Direction', loc='left')
ax3.set_xlabel('Vector Direction')
ax3.set_ylabel('Mean RMSE')

# Prepare statistical summary table data
summary_sign = df.groupby('sign')['RMSE'].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()
summary_increment = df.groupby('increment')['RMSE'].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()
summary_vector = df.groupby('vector_direction')['RMSE'].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()


# Format summary tables as strings for display
def format_summary(df_summary, group_col):
    df_summary = df_summary.copy()
    df_summary[group_col] = df_summary[group_col].astype(str)
    df_summary['mean'] = df_summary['mean'].round(4)
    df_summary['std'] = df_summary['std'].round(4)
    df_summary['min'] = df_summary['min'].round(4)
    df_summary['max'] = df_summary['max'].round(4)
    df_summary['count'] = df_summary['count'].astype(int)
    return df_summary


summary_sign = format_summary(summary_sign, 'sign')
summary_increment = format_summary(summary_increment, 'increment')
summary_vector = format_summary(summary_vector, 'vector_direction')

# Combine summaries into one DataFrame with section headers
table_data = []


def add_section_header(title, ncols):
    return [title] + [''] * (ncols - 1)


ncols = 6  # group_col + 5 stats columns

# Add Sign summary
table_data.append(add_section_header('Sign Summary', ncols))
table_data.append(summary_sign.columns.tolist())
table_data.extend(summary_sign.values.tolist())

# Add a blank row
table_data.append([''] * ncols)

# Add Increment summary
table_data.append(add_section_header('Increment Summary', ncols))
table_data.append(summary_increment.columns.tolist())
table_data.extend(summary_increment.values.tolist())

# Add a blank row
table_data.append([''] * ncols)

# Add Vector Direction summary
table_data.append(add_section_header('Vector Direction Summary', ncols))
table_data.append(summary_vector.columns.tolist())
table_data.extend(summary_vector.values.tolist())

# Create table subplot (right column spanning all rows)
ax_table = fig.add_subplot(grid[:, 1])
ax_table.axis('off')  # Hide axes

# Create table
table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=[0.15] * ncols)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

plt.show()
