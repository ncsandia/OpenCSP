import csv


def csv_reader(input_file_path):
    with open(input_file_path, mode='r', newline='', encoding='utf-8') as filepaths_csv:
        reader = csv.reader(filepaths_csv)
        next(reader)  # Skip the header row if necessary
        # Extract only the first column (index 0)
        files = [row[0] for row in reader]
    print('focal length comparison performed on provided filepaths:', '\n', files)
    return files


def remove_prefix_suffix(df, column, prefix='', suffix=''):
    """
    Remove specified prefix and suffix from each string in a DataFrame column.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Name of the column to process.
        prefix (str): Prefix string to remove (if present).
        suffix (str): Suffix string to remove (if present).

    Returns:
        pd.DataFrame: DataFrame with the processed column.
    """

    def strip_affixes(s):
        if not isinstance(s, str):
            return s  # Return as is if not a string
        if prefix and s.startswith(prefix):
            s = s[len(prefix) :]
        if suffix and s.endswith(suffix):
            s = s[: -len(suffix)]
        return s

    df = df.copy()
    df[column] = df[column].apply(strip_affixes)
    return df


# df_shortened_names = remove_prefix_suffix(df1, column='settings',prefix='', suffix='_test1234',)
# print(df_shortened_names)


def normalize_split_key(split_key):
    if split_key is None:
        return None  # or return [] if you prefer empty list
    if isinstance(split_key, (list, tuple)):
        return list(split_key)  # ensure it's a list, not tuple
    # Otherwise, assume it's a single item and wrap it in a list
    return [split_key]


def split_dataframes_by_substrings(df, split_substrings, include_unmatched=False, unmatched_in_all=False):
    """
    Split DataFrame into multiple DataFrames, each containing rows where 'settings' contains one of the substrings.

    Args:
        df (pd.DataFrame): The DataFrame to split.
        split_substrings (list): List of substrings to filter by.

    Returns:
        list of pd.DataFrame: List of DataFrames corresponding to each substring.
    """
    matched_mask = pd.Series(False, index=df.index)
    dfs = []
    for sub in split_substrings:
        subset_df = df[df['settings'].str.contains(sub, na=False)].copy()
        dfs.append(subset_df)
        matched_mask |= df.index.isin(subset_df.index)
    unmatched_df = df[~matched_mask].copy()

    if include_unmatched and not unmatched_df.empty:
        if unmatched_in_all:
            dfs = [pd.concat([subset, unmatched_df]).drop_duplicates() for subset in dfs]
        else:
            dfs.append(unmatched_df)
        return dfs
    else:
        return dfs


# check if dataframe can be split using substrings

# df1, df2, df3 = split_dataframes_by_substrings(df, split_substrings=['row0', 'row1', 'row2'], include_unmatched=True, unmatched_in_all=True)
# print(df1)
# print(df2)
# print(df3)


# df1a, df1b = split_dataframes_by_substrings(
#     df1, split_substrings=['n', 'p'], include_unmatched=True, unmatched_in_all=True
# )
# print(df1a)
# print(df1b)
