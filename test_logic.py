import pandas as pd
import glob
import numpy as np

history_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
detailed_files = [x for x in glob.glob('data_detailed/*.xlsx') if '~$' not in x]

hist_list = [pd.read_excel(f) for f in history_files]
hist_df = pd.concat(hist_list, ignore_index=True) if hist_list else pd.DataFrame()

det_list = [pd.read_excel(f) for f in detailed_files]
det_df = pd.concat(det_list, ignore_index=True) if det_list else pd.DataFrame()

print("Columns in Hist:", hist_df.columns.tolist() if not hist_df.empty else [])
print("Columns in Det:", det_df.columns.tolist() if not det_df.empty else [])

# 1. Clean History dates
if not hist_df.empty:
    hist_df['审核时间'] = pd.to_datetime(hist_df['审核时间'], errors='coerce')
    # Filter by a test date
    may_hist = hist_df[hist_df['审核时间'].dt.month == 5]
    print(f"Total rows in History (May Audit): {len(may_hist)}")
    
    # Shop distribution
    if '店铺' in may_hist.columns:
        print("Shops in History:", may_hist['店铺'].unique())
        
    # Test Cancellation Logic
    if '发货状态' in may_hist.columns and '发货时间' in may_hist.columns:
        # User rule: 发货状态 is empty OR 发货时间 is '0000-00-00'
        # pandas read_excel might load '0000-00-00' as a string or NaT.
        # Let's check how '0000-00-00' looks in pandas
        empty_status = may_hist['发货状态'].isna() | (may_hist['发货状态'].astype(str).str.strip() == '')
        bad_time = may_hist['发货时间'].astype(str).str.contains('0000-00-00', na=False)
        
        cancel_mask = empty_status | bad_time
        print(f"Cancelled Orders: {cancel_mask.sum()}")
        
        # Pending Orders: Not cancelled, but no valid 发货时间
        # Note: if 发货时间 is valid it's a datetime. If it's NaN/NaT, it's pending (if not cancelled).
        dt_time = pd.to_datetime(may_hist['发货时间'], errors='coerce')
        pending_mask = dt_time.isna() & ~cancel_mask
        print(f"Pending Orders: {pending_mask.sum()}")
        
        dispatched_mask = dt_time.notna() & ~cancel_mask
        print(f"Dispatched Orders: {dispatched_mask.sum()}")

    # 2. Merge logic test
    if '出库单号' in hist_df.columns and '出库单号' in det_df.columns:
        # Merge 审核时间, 店铺, etc from History into Detail based on 出库单号
        # Drop duplicates on 出库单号 from History to avoid row explosion
        hist_unique = hist_df.drop_duplicates(subset=['出库单号'])
        merge_cols = ['出库单号', '审核时间']
        if '店铺' in hist_unique.columns and '店铺' not in det_df.columns:
            merge_cols.append('店铺')
            
        det_merged = det_df.merge(hist_unique[merge_cols], on='出库单号', how='left')
        print(f"Detail rows after merge: {len(det_merged)} (was {len(det_df)})")
        det_may = det_merged[pd.to_datetime(det_merged['审核时间'], errors='coerce').dt.month == 5]
        print(f"Detail rows for May Audit: {len(det_may)}")
        
        if '货品简称' in det_may.columns:
            print("Top Products in May:")
            print(det_may.groupby('货品简称')['货品总数量'].sum().nlargest(3))
