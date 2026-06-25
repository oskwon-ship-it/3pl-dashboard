import pandas as pd
import glob
files = glob.glob('data_history/*.csv') + glob.glob('data_history/*.xlsx') + glob.glob('data_history/*.xls')
df_list = []
for file in files:
    if '~$' in file: continue
    if file.endswith('.csv'):
        temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
    else:
        temp_df = pd.read_excel(file, engine='openpyxl')
    df_list.append(temp_df)

if df_list:
    df = pd.concat(df_list, ignore_index=True)
    if '审核时间' in df.columns:
        s = df['审核时间'].astype(str).str.replace(r'^[=\"]+', '', regex=True).str.replace(r'[\"]+$', '', regex=True)
        s1 = pd.to_datetime(s, errors='coerce')
        s2 = pd.to_datetime(s, errors='coerce', format='mixed')
        
        df_test = pd.DataFrame({'raw': s, 's1_nomixed': s1, 's2_mixed': s2})
        diff = df_test[df_test['s1_nomixed'] != df_test['s2_mixed']].dropna()
        
        print("Dates that parsed differently:")
        print(diff.head(20))
        
        m1 = (s1 >= '2026-06-01') & (s1 < '2026-07-01')
        m2 = (s2 >= '2026-06-01') & (s2 < '2026-07-01')
        print(f"\nJune 2026 without mixed count: {m1.sum()}")
        print(f"June 2026 with mixed count: {m2.sum()}")
        
        with open('date_diff.txt', 'w', encoding='utf-8') as f:
            f.write(diff.head(50).to_string())
            f.write(f"\nJune 2026 without mixed count: {m1.sum()}\n")
            f.write(f"June 2026 with mixed count: {m2.sum()}\n")
