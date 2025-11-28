import pandas as pd
import glob
import os
import sys

def check_dependencies():
    """Checks for required libraries and provides installation instructions."""
    try:
        import openpyxl
        import xlrd
    except ImportError as e:
        print(f"Error: Missing required library. Please install it.")
        print(f"Details: {e}")
        print("\nPlease run the following command to install the necessary libraries:")
        print("pip install pandas openpyxl xlrd")
        sys.exit(1)

def aggregate_price_lists(price_dir, output_file):
    """
    Aggregates all Excel price lists from a directory into a single Excel file.

    Args:
        price_dir (str): The directory containing the price list files.
        output_file (str): The path to the output aggregated Excel file.
    """
    check_dependencies()

    # Find all Excel files (xlsx, xls, XLS)
    file_patterns = [
        os.path.join(price_dir, '*.xlsx'),
        os.path.join(price_dir, '*.xls'),
        os.path.join(price_dir, '*.XLS')
    ]
    
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(pattern))

    if not all_files:
        print(f"No Excel files found in the directory: {price_dir}")
        return

    print(f"Found {len(all_files)} price list files to process...")

    all_data = []

    for f in all_files:
        print(f"Processing file: {os.path.basename(f)}...")
        try:
            # Load the Excel file without assuming any sheet names
            xls = pd.ExcelFile(f)
            for sheet_name in xls.sheet_names:
                print(f"  - Reading sheet: '{sheet_name}'")
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                    if df.empty:
                        print(f"    ...Sheet is empty. Skipping.")
                        continue
                    
                    # Add the source information
                    df['source_file'] = os.path.basename(f)
                    df['sheet_name'] = sheet_name
                    # Use the index as the original row number (plus 2 for header and 0-based index)
                    df['row_number'] = df.index + 2 

                    all_data.append(df)
                except Exception as e:
                    print(f"    ...Could not read sheet '{sheet_name}'. Error: {e}")
        except Exception as e:
            print(f"Could not process file {os.path.basename(f)}. Error: {e}")

    if not all_data:
        print("No data was extracted from any of the files.")
        return

    print("Combining all dataframes...")
    # Concatenate all dataframes, trying to align columns
    # Using outer join to keep all columns from all files
    aggregated_df = pd.concat(all_data, ignore_index=True, sort=False)
    
    # Reorder columns to have the source info first, as per methodology
    cols = aggregated_df.columns.tolist()
    source_cols = ['source_file', 'sheet_name', 'row_number']
    
    # Remove the source columns from their current position
    for col in source_cols:
        if col in cols:
            cols.remove(col)
            
    # Add them to the beginning
    final_cols = source_cols + cols
    aggregated_df = aggregated_df[final_cols]
    
    print(f"Writing aggregated data to '{output_file}'...")
    try:
        aggregated_df.to_excel(output_file, index=False)
        print("Aggregation complete!")
        print(f"A total of {len(aggregated_df)} rows have been written.")
    except Exception as e:
        print(f"Failed to write to Excel file. Error: {e}")


if __name__ == '__main__':
    PRICE_DIR = 'Прайсы'
    OUTPUT_FILE = 'aggregated_pricelist.xlsx'
    
    if not os.path.isdir(PRICE_DIR):
        print(f"Error: The price directory '{PRICE_DIR}' does not exist.")
        sys.exit(1)
        
    aggregate_price_lists(PRICE_DIR, OUTPUT_FILE)