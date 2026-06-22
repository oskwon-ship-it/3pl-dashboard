import os
import glob
import pandas as pd

folders = [
    "data_detailed",
    "data_history",
    "data_inbound",
    "data_outbound_cj",
    "data_outbound_quick"
]

for folder in folders:
    files = glob.glob(f"{folder}/*.xlsx") + glob.glob(f"{folder}/*.xls")
    for file in files:
        if "~$" in file: 
            continue
        print(f"Converting {file}...")
        try:
            # Read excel
            df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            
            # Create CSV path
            csv_path = os.path.splitext(file)[0] + '.csv'
            
            # Save to CSV with utf-8-sig for Excel compatibility
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # Remove original file
            os.remove(file)
            print(f"Successfully converted and deleted original for {file}")
        except Exception as e:
            print(f"Failed to convert {file}: {e}")

print("All done!")
