import pandas as pd
import glob
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")
df_list = []
for f in files:
    if "~$" in f: continue
    df_list.append(pd.read_excel(f))
df = pd.concat(df_list, ignore_index=True)

def merge_shop(s):
    s_str = str(s).strip().lower()
    if 'xiaohongshu' in s_str or 'taofenxiao' in s_str or 'haul41' in s_str or '샤오홍수' in s_str:
        return 'B2C'
    return str(s).strip()

df['店铺'] = df['店铺'].apply(merge_shop)

df['审核时间'] = pd.to_datetime(df['审核时间'], errors='coerce')
df['发货时间'] = pd.to_datetime(df['发货时间'].astype(str).replace('0000-00-00 00:00:00', pd.NaT).replace('0000-00-00', pd.NaT), errors='coerce')

df['접수일자'] = df['审核时间'].dt.date
df['发货일자'] = df['发货时间'].dt.date

may_df = df[(df['접수일자'] >= pd.to_datetime('2026-05-01').date()) & 
            (df['접수일자'] <= pd.to_datetime('2026-05-31').date()) & 
            (df['店铺'] == 'B2C')]

cancel_mask = may_df['发货状态'].isna() | (may_df['发货状态'].astype(str).str.strip() == '') | may_df['发货时间'].astype(str).str.contains('0000-00-00', na=False)
pending_mask = may_df['发货时间'].isna() & ~cancel_mask
dispatched_mask = ~cancel_mask & ~pending_mask

delayed = may_df[dispatched_mask & (may_df['发货일자'] > may_df['접수일자'])]

delayed[['出库单号', '店铺', '审核时间', '发货时间', '접수일자', '发货일자']].head(20).to_csv('delayed_debug.csv', index=False, encoding='utf-8-sig')
print("done")
