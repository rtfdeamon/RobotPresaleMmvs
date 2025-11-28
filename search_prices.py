
import pandas as pd
import sys
import os

def search_price_list(query, search_file):
    """
    Searches for a query in the aggregated price list.

    Args:
        query (str): The search term.
        search_file (str): The path to the aggregated Excel file.
    """
    if not os.path.exists(search_file):
        print(f"Error: The aggregated price list file '{search_file}' was not found.")
        print("Please run the 'aggregate_prices.py' script first.")
        sys.exit(1)

    print(f"Searching for '{query}' in '{search_file}'...")
    
    try:
        df = pd.read_excel(search_file)
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        sys.exit(1)

    # Perform a case-insensitive search across all columns
    # We create a boolean mask for rows that contain the query in any cell
    # NaNs are filled with empty strings to make them searchable
    mask = df.apply(lambda col: col.astype(str).str.contains(query, case=False, na=False))
    
    # The result of the above is a DataFrame of booleans. We want rows where *any* column is True.
    results_df = df[mask.any(axis=1)]

    if results_df.empty:
        print("No results found.")
    else:
        print(f"Found {len(results_df)} matching rows:")
        
        # Determine which columns to display.
        # We'll show the source columns and any column that contains the match.
        source_cols = ['source_file', 'sheet_name', 'row_number']
        display_cols = set(source_cols)
        
        # Find columns that have the query string
        for col in results_df.columns:
            if results_df[col].astype(str).str.contains(query, case=False, na=False).any():
                display_cols.add(col)
        
        # Ensure the columns are in a logical order
        final_display_cols = source_cols + sorted(list(display_cols - set(source_cols)))
        
        # To avoid printing a very wide dataframe, let's just print the relevant info
        # in a more readable, non-tabular format for each row.
        for index, row in results_df.iterrows():
            print("-" * 50)
            print(f"Match found in: {row['source_file']}, Sheet: '{row['sheet_name']}', Row: {row['row_number']}")
            print("Details:")
            for col in final_display_cols:
                # Don't print the source info again
                if col in source_cols:
                    continue
                
                # Check if the value is not null/empty
                if pd.notna(row[col]):
                    print(f"  - {col}: {row[col]}")
            print("-" * 50)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python search_prices.py \"<your search query>\"")
        sys.exit(1)
        
    search_query = sys.argv[1]
    AGGREGATED_FILE = 'aggregated_pricelist.xlsx'
    
    search_price_list(search_query, AGGREGATED_FILE)
