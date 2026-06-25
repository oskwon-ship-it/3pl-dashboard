import pandas as pd
import glob

# Try to read the first history file
history_files = glob.glob('data_history/*.csv')
if history_files:
    df = pd.read_csv(history_files[0], low_memory=False)
    print("Columns:", list(df.columns))
    if '发货时间' in df.columns:
        print("Raw 发货时间 sample:")
        print(df['发货时间'].dropna().head())
        
        parsed = pd.to_datetime(df['发货时间'], errors='coerce')
        parsed_mixed = pd.to_datetime(df['发货时间'], errors='coerce', format='mixed')
        
        print("NaT without mixed:", parsed.isna().sum())
        print("NaT with mixed:", parsed_mixed.isna().sum())
