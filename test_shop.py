import pandas as pd
import glob

history_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
hist_list = [pd.read_excel(f) for f in history_files]
hist_df = pd.concat(hist_list, ignore_index=True) if hist_list else pd.DataFrame()

if not hist_df.empty and '店铺' in hist_df.columns:
    print("Original Shop counts:")
    print(hist_df['店铺'].value_counts())
    
    hist_df['店铺_merged'] = hist_df['店铺'].replace(['EA_Xiaohongshu', 'EA_Taofenxiao'], 'B2C')
    print("\nMerged Shop counts:")
    print(hist_df['店铺_merged'].value_counts())
    
    # Check by month to match the dashboard (May)
    hist_df['审核时间'] = pd.to_datetime(hist_df['审核时间'], errors='coerce')
    may_df = hist_df[hist_df['审核时间'].dt.month == 5]
    print("\nMay Shop counts:")
    print(may_df['店铺_merged'].value_counts())
    
    b2c_may = may_df[may_df['店铺_merged'] == 'B2C']
    print(f"\nB2C Total in May: {len(b2c_may)}")
    
    cancel_mask = b2c_may['发货状态'].isna() | (b2c_may['发货状态'].astype(str).str.strip() == '')
    bad_time_mask = b2c_may['发货时间'].astype(str).str.contains('0000-00-00', na=False)
    cancel_mask = cancel_mask | bad_time_mask
    print(f"B2C Cancelled in May: {cancel_mask.sum()}")
