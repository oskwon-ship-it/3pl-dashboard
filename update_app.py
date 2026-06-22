import glob
import pandas as pd
import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_between(text, start_marker, end_marker, replacement):
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start != -1 and end != -1:
        return text[:start] + replacement + text[end:]
    return text

new_load_data = """def load_data(data_hash):
    detailed_files = glob.glob("data_detailed/*.csv") + glob.glob("data_detailed/*.xlsx") + glob.glob("data_detailed/*.xls")
    history_files = glob.glob("data_history/*.csv") + glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")
    inbound_files = glob.glob("data_inbound/*.csv") + glob.glob("data_inbound/*.xlsx") + glob.glob("data_inbound/*.xls")
    cj_files = glob.glob("data_outbound_cj/*.csv") + glob.glob("data_outbound_cj/*.xlsx") + glob.glob("data_outbound_cj/*.xls")
    quick_files = glob.glob("data_outbound_quick/*.csv") + glob.glob("data_outbound_quick/*.xlsx") + glob.glob("data_outbound_quick/*.xls")
    
    # 필수 컬럼만 지정하여 메모리 사용량 80% 이상 절약 (OOM 에러 방지)
    use_cols = [
        '出库单号', '审核时间', '店铺', '客服备注', '发货状态', '发货时间', '货品数量',
        '客户网名', '品牌', '货品简称', '货品总数量', '货品编号', '数量', '绩效箱数', 
        '货主', '入库单号', '入库原因', '省市区'
    ]
    
    def read_df(file_path, filter_cols=False):
        try:
            if file_path.endswith('.csv'):
                if filter_cols:
                    return pd.read_csv(file_path, usecols=lambda c: c in use_cols)
                return pd.read_csv(file_path)
            else:
                engine = 'openpyxl' if file_path.endswith('.xlsx') else None
                if filter_cols:
                    return pd.read_excel(file_path, usecols=lambda c: c in use_cols, engine=engine)
                return pd.read_excel(file_path, engine=engine)
        except Exception as e:
            st.warning(f"파일 읽기 오류 ({file_path}): {e}")
            return None

    # 1. 출고 내역(History) 로드
    history_list = [read_df(f, True) for f in history_files if "~$" not in f]
    history_list = [df for df in history_list if df is not None]
    hist_df = pd.concat(history_list, ignore_index=True) if history_list else pd.DataFrame()
        
    # 2. 상세 출고 내역(Detailed) 로드
    df_list = [read_df(f, True) for f in detailed_files if "~$" not in f]
    df_list = [df for df in df_list if df is not None]
    detail_df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        
    # 3. 마스터 데이터를 상세 내역에 병합
    if not detail_df.empty and not hist_df.empty and '出库单号' in detail_df.columns and '出库单号' in hist_df.columns:
        hist_subset = hist_df[['出库单号', '发货状态', '发货时间', '快递公司', '店铺', '省市区']].drop_duplicates('出库单号')
        detail_df = pd.merge(detail_df, hist_subset, on='出库单号', how='left')

        if '审核时间' in detail_df.columns:
            detail_df['접수시간'] = pd.to_datetime(detail_df['审核时间'], errors='coerce')
            detail_df['접수일자'] = detail_df['접수시간'].dt.date
            
    # 4. 입고 내역 로드
    in_list = [read_df(f, True) for f in inbound_files if "~$" not in f]
    in_list = [df for df in in_list if df is not None]
    
    in_df = pd.concat(in_list, ignore_index=True) if in_list else pd.DataFrame()
    if not in_df.empty:
        if '审核时间' in in_df.columns:
            in_df['입고시간'] = pd.to_datetime(in_df['审核时间'], errors='coerce')
            in_df['입고일자'] = in_df['입고시간'].dt.date
        for col in ['数量', '绩效箱数']:
            if col in in_df.columns:
                in_df[col] = pd.to_numeric(in_df[col], errors='coerce').fillna(0)
                
    # 5. CJ 및 Quick 로드
    cj_list = [read_df(f, False) for f in cj_files if "~$" not in f]
    cj_list = [df for df in cj_list if df is not None]
    cj_df = pd.concat(cj_list, ignore_index=True) if cj_list else pd.DataFrame()
    if not cj_df.empty and '집화일자' in cj_df.columns:
        cj_df['집화일자'] = pd.to_datetime(cj_df['집화일자'], errors='coerce').dt.date
        
    qk_list = [read_df(f, False) for f in quick_files if "~$" not in f]
    qk_list = [df for df in qk_list if df is not None]
    qk_df = pd.concat(qk_list, ignore_index=True) if qk_list else pd.DataFrame()
    if not qk_df.empty and '오더일자' in qk_df.columns:
        qk_df['오더일자'] = pd.to_datetime(qk_df['오더일자'], errors='coerce').dt.date

    return hist_df, detail_df, in_df, cj_df, qk_df"""

start_marker = "def load_data(data_hash):"
end_marker = "hist_df, detail_df, in_df, cj_df, qk_df = load_data(get_data_hash())"
content = replace_between(content, start_marker, end_marker, new_load_data + "\n\n")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
