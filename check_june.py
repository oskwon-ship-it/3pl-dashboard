import pandas as pd
import glob
files = glob.glob('data_history/*.csv')
if files:
    df = pd.read_csv(files[0], on_bad_lines='skip', low_memory=False)
    if '审核时间' in df.columns:
        s = df['审核时间'].astype(str).str.replace(r'^[=\"]+', '', regex=True).str.replace(r'[\"]+$', '', regex=True)
        s1 = pd.to_datetime(s, errors='coerce')
        s2 = pd.to_datetime(s, errors='coerce', format='mixed')
        
        print("Sample raw strings:")
        print(s.dropna().head(10).tolist())
        
        m1 = (s1 >= '2026-06-01') & (s1 < '2026-07-01')
        m2 = (s2 >= '2026-06-01') & (s2 < '2026-07-01')
        print(f"June 2026 without mixed: {m1.sum()}")
        print(f"June 2026 with mixed: {m2.sum()}")
        
        # What dates are there?
        if m2.sum() > 0:
            print("With mixed parsed values:")
            print(s2[m2].head())
            print("Raw strings for these:")
            print(s[m2].head())
        
        # Check June 2026 for s1
        if m1.sum() > 0:
            print("Without mixed parsed values:")
            print(s1[m1].head())
            
        # Check Dayfirst vs Monthfirst
        print("s1 value counts by month:")
        print(s1.dt.month.value_counts())
        print("s2 value counts by month:")
        print(s2.dt.month.value_counts())
