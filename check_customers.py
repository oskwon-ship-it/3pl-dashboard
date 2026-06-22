import pandas as pd
import glob

with open('customers.txt', 'w', encoding='utf-8') as f:
    detailed_files = glob.glob('data_detailed/*.xlsx')
    if detailed_files:
        df = pd.read_excel(detailed_files[0])
        if '客户网名' in df.columns:
            f.write(f"Detailed File - Total unique 客户网名: {df['客户网名'].nunique()}\n")
            f.write(df['客户网名'].value_counts().head(5).to_string() + "\n")
            
    history_files = glob.glob('data_history/*.xlsx')
    if history_files:
        df2 = pd.read_excel(history_files[0])
        if '客户网名' in df2.columns:
            f.write(f"History File - Total unique 客户网名: {df2['客户网名'].nunique()}\n")
            f.write(df2['客户网名'].value_counts().head(5).to_string() + "\n")
