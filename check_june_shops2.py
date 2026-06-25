import pandas as pd
import glob
files = glob.glob('data_history/*.csv') + glob.glob('data_history/*.xlsx') + glob.glob('data_history/*.xls')
dfs = []
for f in files:
    if '~$' in f: continue
    if f.endswith('.csv'): dfs.append(pd.read_csv(f, on_bad_lines='skip', low_memory=False))
    else: dfs.append(pd.read_excel(f, engine='openpyxl'))
if dfs:
    df = pd.concat(dfs, ignore_index=True)
    if '审核时间' in df.columns:
        s = df['审核时间'].astype(str).str.replace(r'^[=\"]+', '', regex=True).str.replace(r'[\"]+$', '', regex=True)
        s1 = pd.to_datetime(s, errors='coerce')
        m = (s1 >= '2026-06-01') & (s1 < '2026-07-01')
        df_june = df[m]
        
        with open('june_shops.txt', 'w', encoding='utf-8') as f_out:
            f_out.write(f'June 2026 shape: {df_june.shape}\n')
            if '店铺' in df_june.columns:
                shops = df_june['店铺'].dropna().unique().tolist()
                f_out.write(f'Shops in June 2026: {shops}\n')
