import re

import pandas as pd
import os # Optional: Used for more robust file path handling

def reformat_row(compiler, row):
    """
    This is the core function where you define HOW to reformat each row.
    It receives a pandas Series object representing a single row.
    You access columns by their header name (e.g., row['Column Name']).
    It should return the reformatted data, typically as a dictionary
    where keys are the new/updated column names and values are the processed data.
    """
    # --- Start: Example Reformatting Logic ---
    # Replace this with your actual reformatting rules!

    reformatted = {}
    date_regex = r'(\d{2}-\d{2}-\d{2,4})'
    tranx_regex = r'([a-zA-z]\d+)'
    ref_num_regex = r'^(\d+|[a-zA-Z]{3}\s+\w+)'
    exit_loop = False
    is_debit = False
    try:
        if _date := re.compile(date_regex).search(compiler.group(0)):
            reformatted['Date'] = _date.group(0).strip()

        if _tranx := re.compile(tranx_regex).search(compiler.group(0)):
            reformatted['Transaction'] = _tranx.group(0).strip()

        if _cap_data := row.get('Date'):
            if re.search(r'\s+', compiler.group(0)):
                _cap_data = _cap_data.replace(compiler.group(0), ''.join(compiler.group(0).split()))

            if 0 < _cap_data.split(" ", 1)[-1].strip().count(" ") < 37:
                is_debit = True
            _data_ls = _cap_data.split(" ", 1)
            _cap_data = _data_ls[-1].strip().split() if len(_data_ls) > 1 else []
            del _data_ls

            if _cap_data:
                if re.compile(ref_num_regex).search(_cap_data[0]):
                    reformatted["Ref Num"], *_cap_data = _cap_data

                debit_amt = credit_amt = "0.00"
                while not exit_loop and _cap_data:
                    if _val := re.compile(r'^(\d|\,)+\.\d{2}$').match(_cap_data[-1]):
                        _val, _ = _val.group(0), _cap_data.pop(-1)
                        if credit_amt != '0.00':
                            credit_amt, debit_amt = _val, credit_amt
                        else:
                            if is_debit:
                                debit_amt = _val
                                break
                            else:
                                credit_amt = _val

                    else:
                        exit_loop = True

                _particulars = " ".join(_cap_data)
                _cap_data = []
                _cap_data = [_particulars, debit_amt, credit_amt]
                del _particulars, credit_amt, debit_amt

                match len(_cap_data):
                    case 1:
                        reformatted["Particulars"] = _cap_data[0] if row.get('Particulars') == "None" else row.get('Particulars')

                    case 2:
                        reformatted['Particulars'] = _cap_data[0] if row.get('Particulars') == "None" else row.get('Particulars')
                        reformatted['Debit Amount'] = _cap_data[1] if row.get('Debit Amount') == "None" else row.get('Debit Amount')

                    case 3:
                        reformatted['Particulars'] = _cap_data[0] if row.get('Particulars') == "None" else row.get('Particulars')
                        reformatted['Debit Amount'] = _cap_data[1] if row.get('Debit Amount') == "None" else row.get('Debit Amount')
                        reformatted['Credit Amount'] = _cap_data[2] if row.get('Credit Amount') == "None" else row.get('Credit Amount')

        if 'Ref Num' not in reformatted:
            reformatted["Ref Num"] = "" if row.get('Ref Num') == "None" else row.get('Ref Num')

        if 'Particulars' not in reformatted:
            reformatted["Particulars"] = "" if row.get('Particulars') == "None" else row.get('Particulars')

        if 'Debit Amount' not in reformatted:
            reformatted["Debit Amount"] = '0.00' if row.get('Debit Amount') == "None" else row.get('Debit Amount')

        if 'Credit Amount' not in reformatted:
            reformatted["Credit Amount"] = '0.00' if row.get('Credit Amount') == "None" else row.get('Credit Amount')

        if 'Balance Amount' not in reformatted:
            reformatted["Balance Amount"] = '0.00' if row.get('Balance Amount') == "None" else row.get('Balance Amount')

    except Exception as e:
        print(f"Error processing row: {row}")
        print(f"Error message: {e}")
        # Decide how to handle errors in a row, e.g., return None or a dict with an error flag
        return {'Error': str(e)}

    return reformatted


def read_and_reformat_excel(input_file_path, output_file_path=None, sheet_name=0):
    """
    Reads an Excel file, reformats each row using the reformat_row function,
    and optionally saves the result to a new Excel file.

    Args:
        input_file_path (str): Path to the input Excel file (.xlsx or .xls).
        output_file_path (str, optional): Path to save the reformatted data.
                                           If None, data is not saved but returned. Defaults to None.
        sheet_name (str or int, optional): Name or index of the sheet to read.
                                            Defaults to 0 (the first sheet).
    Returns:
        pandas.DataFrame: The DataFrame containing the reformatted data.
                          Returns None if the input file cannot be read.
    """
    try:
        # Read the specified sheet from the Excel file into a pandas DataFrame
        print(f"Reading Excel file: {input_file_path}, Sheet: {sheet_name}")
        df = pd.read_excel(input_file_path, sheet_name=sheet_name)
        print(f"Successfully read {len(df)} rows.")

    except FileNotFoundError as err:
        print(f"Error: Input file not found at {input_file_path}")
        raise Exception from err

    except Exception as err:
        # Catch other potential errors during reading (e.g., invalid sheet name, corrupted file)
        print(f"Error reading Excel file: {err}")
        raise Exception from err

    # List to hold the reformatted data (each element will be a dictionary)
    reformatted_data_list = []

    # drop the redundant column of df
    df = df.drop(columns=['Unnamed: 3', 'Unnamed: 8'], axis=1)

    # renameing the dataframe columns
    df.rename(columns={
        "30-01-2025 12:05:42                             BANK OF INDIA, MOHALI C & P BANKING                                            Page 1 REP27": 'Date',
        'Unnamed: 1': 'Transaction',
        'Unnamed: 2': 'Ref Num',
        'Unnamed: 4': 'Particulars',
        'Unnamed: 5': 'Debit Amount',
        'Unnamed: 6': 'Credit Amount',
        'Unnamed: 7': 'Balance Amount',
    }, inplace=True)

    df.fillna("None", inplace=True)
    # df = df.loc[65:]

    print("Reformatting rows...")
    # Iterate through each row of the DataFrame
    for index, row in df.iterrows():
        # match the regex pattern to perform row reformatting
        regex_pattern = r'\b\d{2}-\d{2}-\d{2,4}\s?[a-zA-Z]\d+?\b'
        # data = '03-04-2024S19502186            UPI/409470144865/DR/RANI/                                     1.00'
        if _compile := re.compile(regex_pattern).search(row['Date']):
            # Apply the reformatting logic to the current row
            reformatted_row_dict = reformat_row(_compile, row)

            # Append the result (dictionary) to our list
            if reformatted_row_dict is not None:
                reformatted_data_list.append(reformatted_row_dict)

    # Convert the list of dictionaries back into a pandas DataFrame
    reformatted_df = pd.DataFrame(reformatted_data_list)
    # drop the redundant column of df
    if "error" in reformatted_df.columns:
        reformatted_df = reformatted_df.drop(columns=['error'], axis=1)
    print("Reformatting complete.")

    # --- Optional: Save the reformatted data to a new Excel file ---
    if output_file_path:
        try:
            print(f"Saving reformatted data to: {output_file_path}")
            # Use index=False to avoid writing the DataFrame index as a column
            reformatted_df.to_excel(output_file_path, index=False, engine='openpyxl')
            print("File saved successfully.")
        except Exception as e:
            print(f"Error saving file to {output_file_path}: {e}")

    return reformatted_df

input_excel = r"file_1_data_xlsx.xlsx"
# Specify the path for the output Excel file (optional)
output_excel = r"file_1_response.xlsx"

# Specify the sheet name or index (optional, defaults to the first sheet)
sheet_to_read = "Table 1"  # Example using sheet name
# sheet_to_read = 0         # Example using sheet index (0 for the first sheet)

reformatted_dataframe = read_and_reformat_excel(input_excel, output_excel, sheet_to_read)
# Display the first few rows of the reformatted data (optional)
if reformatted_dataframe is not None:
    print("\n--- First 5 Rows of Reformatted Data ---")
    print(reformatted_dataframe.head())
    print("\n--- Reformatted Data Info ---")
    reformatted_dataframe.info()
