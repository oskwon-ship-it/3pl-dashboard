import pandas as pd
import glob
files = glob.glob('data_history/*.csv')
df = pd.read_csv(files[0], on_bad_lines='skip', low_memory=False)
s = df['审核时间'].astype(str).str.replace(r'^[=\"]+', '', regex=True).str.replace(r'[\"]+$', '', regex=True)
s1 = pd.to_datetime(s, errors='coerce')
m = (s1 >= '2026-06-01') & (s1 < '2026-07-01')
df_june = df[m]
with open('june_shops.txt', 'w', encoding='utf-8') as f:
    f.write(f'June 2026 shape: {df_june.shape}\n')
    if '店铺' in df_june.columns:
        f.write(f"Unique shops in June: {df_june['店铺'].dropna().unique().tolist()}\n")
