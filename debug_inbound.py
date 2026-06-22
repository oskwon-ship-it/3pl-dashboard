import pandas as pd
import glob
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = glob.glob("data_inbound/*.xlsx") + glob.glob("data_inbound/*.xls")
df_list = []
for f in files:
    if "~$" in f: continue
    df_list.append(pd.read_excel(f))
df = pd.concat(df_list, ignore_index=True)

df['입고시간'] = pd.to_datetime(df['入库时间'], errors='coerce')
df['입고일자'] = df['입고시간'].dt.date

jan_df = df[(df['입고일자'] >= pd.to_datetime('2026-01-01').date()) & 
            (df['입고일자'] <= pd.to_datetime('2026-01-31').date())]

print(f"Total rows in Jan: {len(jan_df)}")
print(f"Total unique orders (入库单号): {jan_df['入库单号'].nunique()}")
print(f"Sum of 绩效箱数 directly: {jan_df['绩效箱数'].sum()}")

unique_orders_df = jan_df.drop_duplicates(subset=['入库单号'])
print(f"Sum of 绩效箱数 after drop duplicates: {unique_orders_df['绩效箱数'].sum()}")

# Print first few rows to see if 绩效箱数 is repeated per order
print(jan_df[['入库单号', '货品编号', '数量', '绩效箱数']].head(10).to_string())
