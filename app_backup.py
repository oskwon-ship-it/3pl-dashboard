import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os

st.set_page_config(page_title="3PL 맞춤형 대시보드", page_icon="📦", layout="wide")

custom_css = '''
<style>
/* 전역 폰트 및 스타일 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* 커스텀 카드 스타일 */
.custom-card {
    background-color: #161b22;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    border: 1px solid #30363d;
    text-align: center;
    transition: transform 0.2s ease-in-out;
}
.custom-card:hover {
    transform: translateY(-5px);
    border-color: #00E5FF;
    box-shadow: 0 6px 12px rgba(0, 229, 255, 0.1);
}

/* 타이틀 */
.card-title {
    color: #8b949e;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 10px;
}

/* 주요 수치 */
.card-value {
    color: #00E5FF;
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 12px;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
}

/* 증감 뱃지 */
.card-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    background-color: rgba(46, 160, 67, 0.15);
    color: #3fb950;
    border: 1px solid rgba(46, 160, 67, 0.4);
}
.card-badge.negative {
    background-color: rgba(248, 81, 73, 0.15);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.4);
}
.card-badge.neutral {
    background-color: rgba(139, 148, 158, 0.15);
    color: #8b949e;
    border: 1px solid rgba(139, 148, 158, 0.4);
}
</style>
'''
st.markdown(custom_css, unsafe_allow_html=True)



def apply_korean_date_format(fig):
    fig.update_xaxes(
        tickformatstops=[
            dict(dtickrange=[None, 86400000], value="%Y-%m-%d"),
            dict(dtickrange=[86400000, 604800000], value="%Y-%m-%d"),
            dict(dtickrange=[604800000, "M1"], value="%Y-%m-%d"),
            dict(dtickrange=["M1", "M12"], value="%Y년 %m월"),
            dict(dtickrange=["M12", None], value="%Y년")
        ]
    )
    return fig


@st.cache_data
def get_china_geojson():
    import urllib.request
    import json
    url = "https://raw.githubusercontent.com/longwosion/geojson-map-china/master/china.json"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def get_data_hash():
    import os, glob
    files = glob.glob('data_*/*.xlsx') + glob.glob('data_*/*.xls') + glob.glob('data_*/*.csv')
    return sum(os.path.getmtime(f) for f in files)

@st.cache_data(max_entries=1, ttl=600)
def load_data(data_hash):
    def clean_csv_junk(df):
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(r'^="', '', regex=True).str.replace(r'"$', '', regex=True).str.replace(r'^=', '', regex=True).str.replace(r'^"', '', regex=True)
        return df

    detailed_files = glob.glob("data_detailed/*.csv") + glob.glob("data_detailed/*.xlsx") + glob.glob("data_detailed/*.xls")
    history_files = glob.glob("data_history/*.csv") + glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")
    inbound_files = glob.glob("data_inbound/*.csv") + glob.glob("data_inbound/*.xlsx") + glob.glob("data_inbound/*.xls")
    cj_files = glob.glob("data_outbound_cj/*.csv") + glob.glob("data_outbound_cj/*.xlsx") + glob.glob("data_outbound_cj/*.xls")
    quick_files = glob.glob("data_outbound_quick/*.csv") + glob.glob("data_outbound_quick/*.xlsx") + glob.glob("data_outbound_quick/*.xls")
    inv_files = glob.glob("data_inventory/*.csv") + glob.glob("data_inventory/*.xlsx") + glob.glob("data_inventory/*.xls")
    
    # 필수 컬럼만 지정하여 메모리 사용량 80% 이상 절약 (OOM 에러 방지)
    use_cols = [
        '出库单号', '审核时间', '店铺', '客服备注', '发货状态', '发货时间', '货品数量',
        '客户网名', '品牌', '货品简称', '货品总数量', '货品编号', '数量', '绩效箱数', 
        '货主', '入库单号', '入库原因', '省市区'
    ]
    def col_filter(c):
        return c in use_cols

    # 1. 출고 내역(History) 로드
    history_list = []
    for file in history_files:
        if "~$" in file: continue
        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
            
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
                temp_df = temp_df[[c for c in use_cols if c in temp_df.columns]]
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            history_list.append(temp_df)
        except Exception as e:
            st.warning(f"출고내역 '{file}' 오류: {e}")
            
    hist_df = pd.concat(history_list, ignore_index=True) if history_list else pd.DataFrame()
        
    # 2. 상세 출고 내역(Detailed) 로드
    df_list = []
    for file in detailed_files:
        if "~$" in file: continue
        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
            
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
                temp_df = temp_df[[c for c in use_cols if c in temp_df.columns]]
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"상세 파일 '{file}' 오류: {e}")
            
    detail_df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        
    # 3. 마스터 데이터를 상세 내역에 병합
    if not hist_df.empty and not detail_df.empty:
        if '出库单号' in hist_df.columns and '出库单号' in detail_df.columns:
            hist_unique = hist_df.drop_duplicates(subset=['出库单号'])
            merge_cols = ['出库单号']
            for col in ['审核时间', '店铺', '客服备注', '省市区']:
                if col in hist_unique.columns:
                    merge_cols.append(col)
                    if col in detail_df.columns:
                        detail_df = detail_df.drop(columns=[col])
            detail_df = detail_df.merge(hist_unique[merge_cols], on='出库单号', how='left')

    # 4. 상점명 통합 처리
    if not hist_df.empty and '店铺' in hist_df.columns:
        def merge_shop(s):
            s_str = str(s).strip().lower()
            if 'xiaohongshu' in s_str or 'taofenxiao' in s_str or 'haul41' in s_str or '샤오홍수' in s_str:
                return 'B2C'
            if 'wholesale' in s_str:
                return 'BOX_Korea'
            if 'sample' in s_str:
                return 'EA_Sample'
            return str(s).strip()
        hist_df['店铺'] = hist_df['店铺'].apply(merge_shop)
        if not detail_df.empty and '店铺' in detail_df.columns:
            detail_df['店铺'] = detail_df['店铺'].apply(merge_shop)

    # 5. 날짜 전처리
    def clean_date_str(s):
        return s.astype(str).str.replace(r'^[="]+', '', regex=True).str.replace(r'["]+$', '', regex=True).replace('0000-00-00 00:00:00', pd.NaT).replace('0000-00-00', pd.NaT).replace('nan', pd.NaT)

    if not hist_df.empty:
        if '审核时间' in hist_df.columns:
            hist_df['접수시간'] = pd.to_datetime(clean_date_str(hist_df['审核时间']), errors='coerce')
            hist_df['접수일자'] = pd.to_datetime(hist_df['审核时间'], errors='coerce', format='mixed').dt.date
        if '发货时间' in hist_df.columns:
            hist_df['发货시간'] = pd.to_datetime(clean_date_str(hist_df['发货时间']), errors='coerce')
            hist_df['发货일자'] = hist_df['发货시간'].dt.date
            
    if not detail_df.empty:
        if '审核时间' in detail_df.columns:
            detail_df['접수시간'] = pd.to_datetime(clean_date_str(detail_df['审核时间']), errors='coerce')
            detail_df['접수일자'] = pd.to_datetime(detail_df['审核时间'], errors='coerce', format='mixed').dt.date
        if '发货时间' in detail_df.columns:
            detail_df['发货시간'] = pd.to_datetime(clean_date_str(detail_df['发货时间']), errors='coerce')
            detail_df['发货일자'] = detail_df['发货시간'].dt.date
        if '货品总数量' in detail_df.columns:
            detail_df['货品总数量'] = pd.to_numeric(detail_df['货品总数量'], errors='coerce').fillna(0)
        if '货品数量' in detail_df.columns:
            detail_df['货品数量'] = pd.to_numeric(detail_df['货品数量'], errors='coerce').fillna(0)
            
    col_filter = ['入库单号', '仓库', '货主', '货品编号', '货品简称', '申请单号', '数量', '绩效箱数', '审核时间', '入库原因', '品牌']
    inbound_files = glob.glob(os.path.join("data_inbound", "*.csv")) + glob.glob(os.path.join("data_inbound", "*.xlsx"))
    
    # 6. 입고 내역 로드
    # Force cache clear for user's new 2월 file v2
    in_list = []
    import re
    for file in inbound_files:
        if "~$" in file: continue
        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, engine=engine)
            temp_df = temp_df[[c for c in col_filter if c in temp_df.columns]]
            
            # 파일명에서 몇 월 데이터인지 추출 (예: '1월' -> 1)
            match = re.search(r'(\d+)월', file)
            if match and '审核时间' in temp_df.columns:
                file_month = int(match.group(1))
                # 审核时间이 해당 파일의 월과 일치하는 데이터만 남김 (월별 중복 다운로드 방지)
                temp_time = pd.to_datetime(temp_df['审核时间'], errors='coerce')
                temp_df = temp_df[temp_time.dt.month == file_month]
                
            in_list.append(temp_df)
        except Exception as e:
            st.warning(f"입고 파일 '{file}' 오류: {e}")
            
    in_df = pd.concat(in_list, ignore_index=True) if in_list else pd.DataFrame()
    
    if not in_df.empty:
        if '审核时间' in in_df.columns:
            in_df['입고시간'] = pd.to_datetime(in_df['审核时间'], errors='coerce')
            in_df['입고일자'] = pd.to_datetime(in_df['审核时间'], errors='coerce', format='mixed').dt.date
        for col in ['数量', '绩效箱数']:
            if col in in_df.columns:
                in_df[col] = pd.to_numeric(in_df[col], errors='coerce').fillna(0)
                
    cj_list = []
    for file in cj_files:
        if "~$" in file: continue
        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            cj_list.append(temp_df)
        except: pass
        
    cj_df = pd.concat(cj_list, ignore_index=True) if cj_list else pd.DataFrame()
    if not cj_df.empty and '집화일자' in cj_df.columns:
        cj_df['집화일자'] = pd.to_datetime(cj_df['집화일자'], errors='coerce').dt.date
        
    qk_list = []
    for file in quick_files:
        if "~$" in file: continue
        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            qk_list.append(temp_df)
        except: pass
        
    qk_df = pd.concat(qk_list, ignore_index=True) if qk_list else pd.DataFrame()
    if not qk_df.empty and '오더일자' in qk_df.columns:
        qk_df['오더일자'] = pd.to_datetime(qk_df['오더일자'], errors='coerce').dt.date

    # 6. 오출고 내역 로드
    misship_files = glob.glob("data_misship/*.csv") + glob.glob("data_misship/*.xlsx") + glob.glob("data_misship/*.xls")
    ms_list = []
    for file in misship_files:
        if "~$" in file: continue
        try:
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
            else:
                temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            ms_list.append(temp_df)
        except: pass
        
    misship_df = pd.concat(ms_list, ignore_index=True) if ms_list else pd.DataFrame()
    if not misship_df.empty and '접수일' in misship_df.columns:
        misship_df['접수일'] = pd.to_datetime(misship_df['접수일'], errors='coerce').dt.date

    # 6. 재고 현황(Inventory) 로드
    inv_use_cols = ['货位', '货区名称', '货品简称', '品牌', '库存', '库存量', '占用量', '可发库存', '自定义属性3', '自定义属性4', '毛重（kg）', '有效期', '距离到期天数', '距离临期天数', '货位修改时间']
    def inv_col_filter(c):
        return c in inv_use_cols

    inv_list = []
    for file in inv_files:
        if "~$" in file: continue
        try:
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
                temp_df = temp_df[[c for c in inv_use_cols if c in temp_df.columns]]
            else:
                temp_df = pd.read_excel(file, usecols=inv_col_filter, engine='openpyxl' if file.endswith('.xlsx') else None)
            temp_df = clean_csv_junk(temp_df)
            inv_list.append(temp_df)
        except: pass
        
    inv_df = pd.concat(inv_list, ignore_index=True) if inv_list else pd.DataFrame()
    if not inv_df.empty:
        for col in ['库存', '库存量', '占用量', '可发库存', '距离到期天数', '距离临期天数']:
            if col in inv_df.columns:
                inv_df[col] = pd.to_numeric(inv_df[col], errors='coerce').fillna(0)

    return hist_df, detail_df, in_df, cj_df, qk_df, misship_df, inv_df

hist_df, detail_df, in_df, cj_df, qk_df, misship_df, inv_df = load_data(get_data_hash())

if not hist_df.empty or not in_df.empty:
    with st.expander("⚙️ 3PL 대시보드 메뉴 및 설정 (여기를 눌러 필터를 변경하세요)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            dashboard_type = st.radio(
                "📊 조회할 대시보드를 선택하세요:",
                ('📦 출고 대시보드 (Outbound)', '📥 입고 대시보드 (Inbound)')
            )
        with col2:
            view_mode = st.radio(
                "어떤 용도의 대시보드를 보시겠습니까?",
                ('💼 고객사 배포용 (Client View)', '👑 대표님 보고용 (Internal View)')
            )
            
    if view_mode == '👑 대표님 보고용 (Internal View)':
        st.title("👑 3PL 종합 운영 리포트 (Internal View)")
        
        # 1. 날짜 필터
        min_in = in_df['입고일자'].dropna().min() if not in_df.empty and '입고일자' in in_df.columns else None
        max_in = in_df['입고일자'].dropna().max() if not in_df.empty and '입고일자' in in_df.columns else None
        min_out = hist_df['접수일자'].dropna().min() if not hist_df.empty and '접수일자' in hist_df.columns else None
        max_out = hist_df['접수일자'].dropna().max() if not hist_df.empty and '접수일자' in hist_df.columns else None
        
        valid_mins = [d for d in [min_in, min_out] if d is not None]
        valid_maxs = [d for d in [max_in, max_out] if d is not None]
        import datetime
        min_date = min(valid_mins) if valid_mins else datetime.date.today()
        max_date = max(valid_maxs) if valid_maxs else datetime.date.today()
        
        with st.expander("📅 조회 기간 설정", expanded=True):
            date_range = st.date_input("기준 기간을 선택하세요", value=(min_date, max_date), format="YYYY-MM-DD")
            
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
            
        # 데이터 필터링
        curr_in_df = in_df[(in_df['입고일자'] >= start_date) & (in_df['입고일자'] <= end_date)] if not in_df.empty and '입고일자' in in_df.columns else pd.DataFrame()
        curr_hist_df = hist_df[(hist_df['접수일자'] >= start_date) & (hist_df['접수일자'] <= end_date)] if not hist_df.empty and '접수일자' in hist_df.columns else pd.DataFrame()
        curr_detail_df = detail_df[(detail_df['접수일자'] >= start_date) & (detail_df['접수일자'] <= end_date)] if not detail_df.empty and '접수일자' in detail_df.columns else pd.DataFrame()
        
        curr_cj_df = cj_df[(cj_df['집화일자'] >= start_date) & (cj_df['집화일자'] <= end_date)] if not cj_df.empty and '집화일자' in cj_df.columns else pd.DataFrame()
        curr_qk_df = qk_df[(qk_df['오더일자'] >= start_date) & (qk_df['오더일자'] <= end_date)] if not qk_df.empty and '오더일자' in qk_df.columns else pd.DataFrame()
        curr_misship_df = misship_df[(misship_df['접수일'] >= start_date) & (misship_df['접수일'] <= end_date)] if not misship_df.empty and '접수일' in misship_df.columns else pd.DataFrame()

        # 전 기간(비교용) 필터링 (전월 동일 날짜 기준)
        prev_start_date = (pd.to_datetime(start_date) - pd.DateOffset(months=1)).date()
        prev_end_date = (pd.to_datetime(end_date) - pd.DateOffset(months=1)).date()
        
        prev_in_df = in_df[(in_df['입고일자'] >= prev_start_date) & (in_df['입고일자'] <= prev_end_date)] if not in_df.empty and '입고일자' in in_df.columns else pd.DataFrame()
        prev_hist_df = hist_df[(hist_df['접수일자'] >= prev_start_date) & (hist_df['접수일자'] <= prev_end_date)] if not hist_df.empty and '접수일자' in hist_df.columns else pd.DataFrame()
        prev_detail_df = detail_df[(detail_df['접수일자'] >= prev_start_date) & (detail_df['접수일자'] <= prev_end_date)] if not detail_df.empty and '접수일자' in detail_df.columns else pd.DataFrame()
        prev_misship_df = misship_df[(misship_df['접수일'] >= prev_start_date) & (misship_df['접수일'] <= prev_end_date)] if not misship_df.empty and '접수일' in misship_df.columns else pd.DataFrame()

        st.markdown(f"### 📊 센터 핵심 KPI ({start_date.strftime('%y.%m.%d')} ~ {end_date.strftime('%y.%m.%d')})")
        
        # 취소 주문 마스크 계산 (마스터 데이터 기준)
        cancel_mask = pd.Series(False, index=hist_df.index)
        if '发货状态' in hist_df.columns:
            cancel_mask = hist_df['发货状态'].isna() | (hist_df['发货状态'].astype(str).str.strip() == '')
        canceled_orders = set(hist_df[cancel_mask]['出库单号']) if '出库单号' in hist_df.columns else set()
        
        # 취소 주문 제외된 상세 데이터 생성
        valid_curr_detail = curr_detail_df[~curr_detail_df['出库单号'].isin(canceled_orders)] if not curr_detail_df.empty and '出库单号' in curr_detail_df.columns else curr_detail_df
        valid_prev_detail = prev_detail_df[~prev_detail_df['出库单号'].isin(canceled_orders)] if not prev_detail_df.empty and '出库单号' in prev_detail_df.columns else prev_detail_df

        # Calculate KPIs
        total_in_qty = curr_in_df['数量'].sum() if not curr_in_df.empty and '数量' in curr_in_df.columns else 0
        total_in_box = curr_in_df['绩效箱数'].sum() if not curr_in_df.empty and '绩效箱数' in curr_in_df.columns else 0
        total_out_orders = len(curr_hist_df) if not curr_hist_df.empty else 0
        total_out_qty = valid_curr_detail['货品数量'].sum() if not valid_curr_detail.empty and '货品数量' in valid_curr_detail.columns else 0
        
        prev_in_qty = prev_in_df['数量'].sum() if not prev_in_df.empty and '数量' in prev_in_df.columns else 0
        prev_in_box = prev_in_df['绩效箱数'].sum() if not prev_in_df.empty and '绩效箱数' in prev_in_df.columns else 0
        prev_out_orders = len(prev_hist_df) if not prev_hist_df.empty else 0
        prev_out_qty = valid_prev_detail['货品数量'].sum() if not valid_prev_detail.empty and '货品数量' in valid_prev_detail.columns else 0
        
        # 오출고율 계산
        total_misship = len(curr_misship_df) if not curr_misship_df.empty else 0
        misship_rate = (total_misship / total_out_orders * 100) if total_out_orders > 0 else 0.0
        
        prev_misship = len(prev_misship_df) if not prev_misship_df.empty else 0
        prev_misship_rate = (prev_misship / prev_out_orders * 100) if prev_out_orders > 0 else 0.0

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        def make_card(title, val_str, diff_val, unit, inverse=False):
            if diff_val > 0:
                bc = "negative" if inverse else ""
                icon = "📈 +"
            elif diff_val < 0:
                bc = "" if inverse else "negative"
                icon = "📉 "
            else:
                bc = "neutral"
                icon = "➖ "
            return f'''<div class="custom-card">
                <div class="card-title">{title}</div>
                <div class="card-value">{val_str}</div>
                <div class="card-badge {bc}">{icon}{abs(diff_val):,.1f}{unit} (전월대비)</div>
            </div>'''

        with kpi1:
            st.markdown(make_card("📦 총 입고 수량", f"{total_in_qty:,.0f} 개", total_in_qty - prev_in_qty, "개"), unsafe_allow_html=True)
        with kpi2:
            st.markdown(make_card("📦 총 입고 박스", f"{total_in_box:,.1f} Box", total_in_box - prev_in_box, "Box"), unsafe_allow_html=True)
        with kpi3:
            st.markdown(make_card("🚀 총 출고 주문건수", f"{total_out_orders:,.0f} 건", total_out_orders - prev_out_orders, "건"), unsafe_allow_html=True)
        with kpi4:
            st.markdown(make_card("🚀 총 출고 수량", f"{total_out_qty:,.0f} 개", total_out_qty - prev_out_qty, "개"), unsafe_allow_html=True)
        with kpi5:
            st.markdown(make_card("🚨 오출고율", f"{misship_rate:.2f}%", misship_rate - prev_misship_rate, "%p", inverse=True), unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 일별 입/출고 수량 트렌드")
            in_trend = pd.DataFrame()
            if not curr_in_df.empty and '입고일자' in curr_in_df.columns:
                in_trend = curr_in_df.groupby('입고일자')['数量'].sum().reset_index().rename(columns={'입고일자': '일자', '数量': '입고수량'})
            
            out_trend = pd.DataFrame()
            if not valid_curr_detail.empty and '접수일자' in valid_curr_detail.columns and '货品数量' in valid_curr_detail.columns:
                out_trend = valid_curr_detail.groupby('접수일자')['货品数量'].sum().reset_index().rename(columns={'접수일자': '일자', '货品数量': '출고수량'})
            
            if not in_trend.empty and not out_trend.empty:
                trend_df = pd.merge(in_trend, out_trend, on='일자', how='outer').fillna(0).sort_values('일자')
            elif not in_trend.empty:
                trend_df = in_trend.copy()
                trend_df['출고수량'] = 0
            elif not out_trend.empty:
                trend_df = out_trend.copy()
                trend_df['입고수량'] = 0
            else:
                trend_df = pd.DataFrame(columns=['일자', '입고수량', '출고수량'])
                
            if not trend_df.empty:
                import plotly.express as px
                fig_trend = px.line(trend_df, x='일자', y=['입고수량', '출고수량'], markers=True, title="일자별 입/출고 수량 추이")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("데이터가 부족하여 트렌드를 표시할 수 없습니다.")
                
        with col2:
            st.markdown("### 🚚 CJ vs 퀵 출고 비중 (건수)")
            cj_cnt = len(curr_cj_df)
            qk_cnt = len(curr_qk_df)
            
            if cj_cnt > 0 or qk_cnt > 0:
                dist_df = pd.DataFrame({
                    '출고방식': ['CJ 택배', '퀵 출고'],
                    '건수': [cj_cnt, qk_cnt]
                })
                # 건수가 0인 항목은 파이차트에서 제외
                dist_df = dist_df[dist_df['건수'] > 0]
                import plotly.express as px
                fig_courier = px.pie(dist_df, names='출고방식', values='건수', hole=0.3, title="CJ vs 퀵 출고 비중 (건수)", color='출고방식', color_discrete_map={'CJ 택배':'#1f77b4', '퀵 출고':'#ff7f0e'})
                st.plotly_chart(fig_courier, use_container_width=True)
            else:
                st.info("해당 기간의 출고 데이터가 없습니다.")

        st.divider()
        
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("### 🏆 전체 고객사 출고 현황 (주문건수 기준)")
            if not curr_hist_df.empty and '店铺' in curr_hist_df.columns:
                top_shops = curr_hist_df.groupby('店铺').size().reset_index(name='건수').sort_values('건수', ascending=False)
                import plotly.express as px
                fig_top_shops = px.bar(top_shops, x='건수', y='店铺', orientation='h', title="고객사(상점)별 물동량")
                fig_top_shops.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top_shops, use_container_width=True)
            else:
                st.info("고객사(상점) 데이터가 없습니다.")
                
        with col4:
            st.markdown("### 🚨 오출고 현황")
            if not curr_misship_df.empty:
                # 총 오출고 건수 계산 (각 행을 1건으로)
                total_misship = len(curr_misship_df)
                
                if '네트워크' in curr_misship_df.columns:
                    # 빈 값을 '기타/미분류'로 변경
                    ms_summary = curr_misship_df.copy()
                    ms_summary['네트워크'] = ms_summary['네트워크'].fillna('기타/미분류')
                    status_summary = ms_summary.groupby('네트워크').size().reset_index(name='건수')
                    
                    import plotly.express as px
                    fig_status = px.pie(status_summary, names='네트워크', values='건수', hole=0.4)
                    fig_status.update_traces(textposition='inside', textinfo='percent+label')
                    fig_status.update_layout(
                        title=f"오출고 네트워크별 비율 (총 {total_misship}건)",
                        showlegend=False,
                        margin=dict(t=40, b=0, l=0, r=0)
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.metric("총 오출고 건수", f"{total_misship} 건")
            else:
                st.info("해당 기간에 오출고 데이터가 없습니다.")
                
        st.divider()
        
        st.markdown("### 📊 최근 6개월 월별 트렌드 (입출고 통합 비교)")
        # Group all data (unfiltered by date_range, to show historical months) by Month
        in_monthly = in_df.copy() if not in_df.empty else pd.DataFrame()
        out_monthly = detail_df.copy() if not detail_df.empty else pd.DataFrame()
        
        if not in_monthly.empty and '입고일자' in in_monthly.columns:
            in_monthly['월'] = pd.to_datetime(in_monthly['입고일자']).dt.to_period('M').astype(str)
            in_m_trend = in_monthly.groupby('월')['数量'].sum().reset_index().rename(columns={'数量': '입고수량'})
        else:
            in_m_trend = pd.DataFrame(columns=['월', '입고수량'])
            
        if not out_monthly.empty and '접수일자' in out_monthly.columns and '货品数量' in out_monthly.columns:
            valid_out_monthly = out_monthly[~out_monthly['出库单号'].isin(canceled_orders)] if '出库单号' in out_monthly.columns else out_monthly
            valid_out_monthly['월'] = pd.to_datetime(valid_out_monthly['접수일자']).dt.to_period('M').astype(str)
            out_m_trend = valid_out_monthly.groupby('월')['货品数量'].sum().reset_index().rename(columns={'货品数量': '출고수량'})
        else:
            out_m_trend = pd.DataFrame(columns=['월', '출고수량'])
            
        if not in_m_trend.empty and not out_m_trend.empty:
            m_trend_df = pd.merge(in_m_trend, out_m_trend, on='월', how='outer').fillna(0).sort_values('월').tail(6)
        elif not in_m_trend.empty:
            m_trend_df = in_m_trend.sort_values('월').tail(6)
            m_trend_df['출고수량'] = 0
        elif not out_m_trend.empty:
            m_trend_df = out_m_trend.sort_values('월').tail(6)
            m_trend_df['입고수량'] = 0
        else:
            m_trend_df = pd.DataFrame()
            
        if not m_trend_df.empty:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig_mom = make_subplots(specs=[[{"secondary_y": True}]])
            fig_mom.add_trace(go.Bar(x=m_trend_df['월'], y=m_trend_df['입고수량'], name='입고 수량(개)', opacity=0.7), secondary_y=False)
            fig_mom.add_trace(go.Scatter(x=m_trend_df['월'], y=m_trend_df['출고수량'], name='출고 수량(개)', mode='lines+markers+text', text=m_trend_df['출고수량'], textposition='top center', line=dict(color='red', width=3)), secondary_y=True)
            fig_mom.update_layout(title="최근 6개월 입고 수량 및 출고 수량 비교", barmode='group')
            fig_mom.update_yaxes(title_text="입고 수량", secondary_y=False)
            fig_mom.update_yaxes(title_text="출고 수량", secondary_y=True)
            st.plotly_chart(fig_mom, use_container_width=True)
        else:
            st.info("데이터가 부족하여 월별 트렌드를 표시할 수 없습니다.")

        st.divider()
        st.markdown("### 📦 창고 로케이션 및 재고 현황")
        if not inv_df.empty:
            st.markdown("#### 🚨 유통기한 및 재고 회전율 경고 시스템")
            warn_col1, warn_col2 = st.columns(2)
            
            # 1. 유통기한 경고 (Expiration Tracker)
            if '距离到期天数' in inv_df.columns:
                danger_items = inv_df[(inv_df['距离到期天数'] > 0) & (inv_df['距离到期天数'] <= 90)]
                warning_items = inv_df[(inv_df['距离到期天数'] > 90) & (inv_df['距离到期天数'] <= 180)]
                with warn_col1:
                    st.error(f"🔴 90일 이내 만료 상품: {len(danger_items)}건")
                    if not danger_items.empty:
                        show_cols_exp = [c for c in ['货位', '货品简称', '库存', '有效期', '距离到期天数'] if c in danger_items.columns]
                        st.dataframe(danger_items[show_cols_exp].sort_values('距离到期天数'), use_container_width=True, hide_index=True)
                with warn_col2:
                    st.warning(f"🟡 180일 이내 만료 상품: {len(warning_items)}건")
                    if not warning_items.empty:
                        show_cols_exp = [c for c in ['货位', '货品简称', '库存', '有效期', '距离到期天数'] if c in warning_items.columns]
                        st.dataframe(warning_items[show_cols_exp].sort_values('距离到期天数'), use_container_width=True, hide_index=True)
                        
            # 2. 재고 회전율 (Turnover Rate)
            st.markdown("#### 🔄 재고 회전율 분석 (최근 출고량 기반)")
            if not detail_df.empty and '货品简称' in detail_df.columns and '货品数量' in detail_df.columns and '库存' in inv_df.columns:
                # 최근 한 달(또는 전체) 출고량 집계
                valid_out = detail_df[~detail_df['出库单号'].isin(canceled_orders)] if '出库单号' in detail_df.columns else detail_df
                out_sum = valid_out.groupby('货品简称')['货品数量'].sum().reset_index().rename(columns={'货品数量': '최근출고량'})
                # 재고 총합 집계
                inv_sum = inv_df.groupby('货品简称')['库存'].sum().reset_index()
                # 병합
                turnover_df = pd.merge(inv_sum, out_sum, on='货品简称', how='left').fillna(0)
                
                # 악성 재고 (재고 100개 이상인데 출고량 0)
                dead_stock = turnover_df[(turnover_df['库存'] >= 100) & (turnover_df['최근출고량'] == 0)].sort_values('库存', ascending=False)
                # 발주 시급 (재고 100개 미만인데 출고량 100개 이상)
                fast_movers = turnover_df[(turnover_df['库存'] < 100) & (turnover_df['최근출고량'] >= 100)].sort_values('최근출고량', ascending=False)
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.info(f"❄️ 악성 재고 경고 (재고 100+ & 최근 출고 0건): {len(dead_stock)}건")
                    if not dead_stock.empty:
                        st.dataframe(dead_stock, use_container_width=True, hide_index=True)
                with t_col2:
                    st.success(f"🔥 발주 시급 상품 (재고 <100 & 최근 출고 100+): {len(fast_movers)}건")
                    if not fast_movers.empty:
                        st.dataframe(fast_movers, use_container_width=True, hide_index=True)
                        
            st.divider()

            # 3. 복도(Aisle) 열 생성: 로케이션(货位)의 첫 2글자 (예: B1, A2 등)
            if '货位' in inv_df.columns:
                inv_df['복도(Aisle)'] = inv_df['货位'].fillna('미지정').str[:2]
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🔹 구역별 재고 점유율")
                if '货区名称' in inv_df.columns and '库存' in inv_df.columns:
                    zone_dist = inv_df.groupby('货区名称')['库存'].sum().reset_index()
                    import plotly.express as px
                    fig_zone = px.pie(zone_dist, names='货区名称', values='库存', hole=0.4)
                    fig_zone.update_traces(textposition='inside', textinfo='percent+label')
                    fig_zone.update_layout(margin=dict(t=30, b=0, l=0, r=0), showlegend=False)
                    st.plotly_chart(fig_zone, use_container_width=True)
                
            with c2:
                st.markdown("#### 🔹 복도(Aisle)별 보관량 현황")
                if '복도(Aisle)' in inv_df.columns and '库存' in inv_df.columns:
                    aisle_dist = inv_df.groupby('복도(Aisle)')['库存'].sum().reset_index().sort_values('库存', ascending=False).head(10)
                    fig_aisle = px.bar(aisle_dist, x='복도(Aisle)', y='库存', text='库存', color='库存', color_continuous_scale='Blues')
                    fig_aisle.update_layout(margin=dict(t=30, b=0, l=0, r=0), showlegend=False)
                    st.plotly_chart(fig_aisle, use_container_width=True)
            
            st.markdown("#### 🔹 상위 적재 상품 Top 5 (선택 구역)")
            if '货区名称' in inv_df.columns:
                selected_zone = st.selectbox("조회할 구역(Zone)을 선택하세요:", options=inv_df['货区名称'].dropna().unique())
                zone_df = inv_df[inv_df['货区名称'] == selected_zone]
                if '货品简称' in zone_df.columns and '库存' in zone_df.columns:
                    top_items = zone_df.groupby('货品简称')['库存'].sum().reset_index().sort_values('库存', ascending=False).head(5)
                    fig_top = px.bar(top_items, x='库存', y='货品简称', orientation='h', color='库存', color_continuous_scale='Teal')
                    fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=10, b=0, l=0, r=0))
                    st.plotly_chart(fig_top, use_container_width=True)
            
            st.markdown("#### 🔍 로케이션 상세 검색 테이블")
            show_cols = []
            for c in ['货位', '복도(Aisle)', '货区名称', '货品简称', '品牌', '库存', '可发库存', '自定义属性3', '自定义属性4', '毛重（kg）', '有效期', '距离到期天数']:
                if c in inv_df.columns:
                    show_cols.append(c)
            if show_cols:
                st.dataframe(inv_df[show_cols].sort_values('库存', ascending=False), use_container_width=True, hide_index=True)
                
        else:
            st.info("data_inventory 폴더에 재고 현황 데이터 파일이 없습니다.")

        st.stop()
    
    if dashboard_type == '📥 입고 대시보드 (Inbound)':
        st.title("📥 입고(Inbound) 운영 리포트")
        if in_df.empty:
            st.warning("data_inbound 폴더에 입고 데이터 파일이 없습니다. 엑셀 파일을 넣어주세요.")
            st.stop()
            
        with st.expander("📅 입고 데이터 필터", expanded=True):
            if '입고일자' in in_df.columns:
                min_date = in_df['입고일자'].dropna().min()
                max_date = in_df['입고일자'].dropna().max()
                
                date_range = st.date_input("조회할 기간을 선택하세요", value=(min_date, max_date), format="YYYY-MM-DD")
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                    in_df = in_df[(in_df['입고일자'] >= start_date) & (in_df['입고일자'] <= end_date)]
                    selected_period_text = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
                else:
                    selected_period_text = "전체 기간"
            
            if '货主' in in_df.columns:
                shipper_list = ["전체 화주 보기"] + sorted(in_df['货主'].dropna().unique().tolist())
                selected_shipper = st.selectbox("📌 상세 분석을 진행할 화주를 선택해 주세요:", shipper_list)
                
                if selected_shipper != "전체 화주 보기":
                    in_df = in_df[in_df['货主'] == selected_shipper]
                
        # 입고 핵심 KPI
        st.subheader(f"[{selected_shipper if 'selected_shipper' in locals() and selected_shipper != '전체 화주 보기' else '전체'}] 핵심 입고 지표")
        ikpi1, ikpi2 = st.columns(2)
        ikpi3, ikpi4 = st.columns(2)
        
        total_in_skus = len(in_df)
        total_in_qty = in_df['数量'].sum() if '数量' in in_df.columns else 0
        total_in_box = in_df['绩效箱数'].sum() if '绩效箱数' in in_df.columns else 0
        
        ikpi1.metric("총 입고 품목 수", f"{total_in_skus:,.0f} 건")
        ikpi2.metric("총 입고 수량", f"{total_in_qty:,.0f} 개")
        ikpi3.metric("총 입고 박스 수", f"{total_in_box:,.1f} Box")
        st.divider()
        
        # 입고 차트 1: 기간별 트렌드
        if '입고일자' in in_df.columns:
            st.markdown("## 2️⃣ 기간별 입고 트렌드")
            in_trend = in_df.groupby('입고일자')['数量'].sum().reset_index(name='입고수량')
            in_trend['월(Month)'] = pd.to_datetime(in_trend['입고일자']).dt.strftime('%Y년 %m월')
            
            in_month = in_trend.groupby('월(Month)')['입고수량'].sum().reset_index()
            
            t1, t2 = st.tabs(["📅 월별 입고 요약", "📆 일별 입고 상세"])
            with t1:
                fig_in_month = px.bar(in_month, x='월(Month)', y='입고수량', text_auto=True, color='입고수량', color_continuous_scale='Greens')
                st.plotly_chart(fig_in_month, use_container_width=True)
            with t2:
                fig_in_day = px.line(in_trend, x='입고일자', y='입고수량', markers=True)
                fig_in_day = apply_korean_date_format(fig_in_day)
                st.plotly_chart(fig_in_day, use_container_width=True)
            st.divider()
            
        # 입고 차트 2: 입고 사유 및 브랜드
        st.markdown("## 3️⃣ 입고 사유 및 브랜드 현황")
        c_reason, c_brand = st.columns(2)
        with c_reason:
            if '入库原因' in in_df.columns:
                st.markdown("**📝 입고 사유별 비중**")
                
                def map_reason(r):
                    r_str = str(r).strip()
                    mapping = {
                        '采购入库': '발주 입고',
                        '退货入库': '반품 입고',
                        '未知入库': '기타 입고 (미상)',
                        '代入库': '대행 입고',
                        '调拨入库': '재고 이동 입고',
                        '借调入库': '이관 입고 (차용)',
                        '预入库': '가입고 (사전등록)',
                        '盘盈入库': '재고조사 입고 (초과)'
                    }
                    return mapping.get(r_str, r_str)
                    
                in_df['입고사유_한글'] = in_df['入库原因'].apply(map_reason)
                reason_summary = in_df.groupby('입고사유_한글')['数量'].sum().reset_index()
                fig_reason = px.pie(reason_summary, names='입고사유_한글', values='数量', hole=0.4)
                st.plotly_chart(fig_reason, use_container_width=True)
                
        with c_brand:
            if '品牌' in in_df.columns:
                st.markdown("**🏷️ 브랜드별 입고 수량 (Top 10)**")
                brand_summary = in_df.groupby('品牌')['数量'].sum().reset_index()
                top_brands = brand_summary.nlargest(10, '数量')
                fig_brand = px.bar(top_brands, x='数量', y='品牌', orientation='h', labels={'数量':'입고수량'}, color='数量', color_continuous_scale='Purples')
                fig_brand.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_brand, use_container_width=True)
        st.divider()
        
        # 입고 차트 3: 상품별 상세조회
        if '品牌' in in_df.columns and '货品简称' in in_df.columns:
            st.markdown("## 4️⃣ 특정 브랜드 상세 입고 상품 조회")
            
            if '货品编号' in in_df.columns:
                in_df['상품표시명'] = in_df['货品编号'].astype(str) + " - " + in_df['货品简称'].astype(str)
            else:
                in_df['상품표시명'] = in_df['货品简称']
                
            brand_list = ["브랜드를 선택하세요"] + sorted(in_df['品牌'].dropna().unique().tolist())
            selected_brand = st.selectbox("📌 상세 입고 내역을 확인할 브랜드를 선택해 주세요:", brand_list)
            
            if selected_brand != "브랜드를 선택하세요":
                target_prod_df = in_df[in_df['品牌'] == selected_brand]
                st.markdown(f"**📦 '{selected_brand}' 상세 상품별 입고 수량**")
                
                brand_item_summary = target_prod_df.groupby('상품표시명')['数量'].sum().reset_index()
                brand_item_summary = brand_item_summary.sort_values('数量', ascending=False)
                
                fig_brand_item = px.bar(brand_item_summary.head(15), x='数量', y='상품표시명', orientation='h', labels={'상품표시명':'바코드 - 상품명', '数量':'입고수량'}, color='数量', color_continuous_scale='Blues')
                fig_brand_item.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_brand_item, use_container_width=True)
                
                st.dataframe(brand_item_summary.rename(columns={'상품표시명':'상품명', '数量':'입고수량(개)'}), use_container_width=True, hide_index=True)

        st.stop() # 입고 대시보드 렌더링 후 종료 (아래 출고 로직 무시)
        
    # ================== 출고 대시보드 로직 시작 ==================
    if hist_df.empty:
        st.warning("data_history 폴더에 출고 데이터 파일이 없습니다. 엑셀 파일을 넣어주세요.")
        st.stop()
    
    with st.expander("📅 출고 데이터 필터", expanded=True):
        if '접수일자' in hist_df.columns:
            min_date = hist_df['접수일자'].dropna().min()
            max_date = hist_df['접수일자'].dropna().max()
            
            date_range = st.date_input(
                "조회할 기간을 선택하세요", 
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                hist_df = hist_df[(hist_df['접수일자'] >= start_date) & (hist_df['접수일자'] <= end_date)]
                if not detail_df.empty and '접수일자' in detail_df.columns:
                    detail_df = detail_df[(detail_df['접수일자'] >= start_date) & (detail_df['접수일자'] <= end_date)]
                selected_period_text = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
            else:
                selected_period_text = "전체 기간"
                
        if view_mode == '💼 고객사 배포용 (Client View)' and '店铺' in hist_df.columns:
            shop_list = ["상점을 선택하세요 (전체 데이터 유지)"] + sorted(hist_df['店铺'].dropna().unique().tolist())
            selected_shop = st.selectbox("📌 상세 분석을 진행할 상점(店铺)을 선택해 주세요:", shop_list)
    
    if view_mode == '💼 고객사 배포용 (Client View)':
        st.title("💼 고객사 맞춤형 출고 리포트 (드릴다운 뷰)")
        
        # 1. 상점별 데이터 (화주 대신 상점 기준)
        if '店铺' in hist_df.columns:
            if selected_shop == "상점을 선택하세요 (전체 데이터 유지)":
                st.markdown("## 1️⃣ 상점(店铺) 물동량 요약")
                shop_summary = hist_df.groupby('店铺').size().reset_index(name='주문건수')
                fig_shop_pie = px.pie(shop_summary, names='店铺', values='주문건수', hole=0.3, title="전체 상점별 물동량 점유율 (접수 기준)")
                fig_shop_pie.update_layout(margin=dict(l=20, r=20, t=80, b=20), height=550)
                st.plotly_chart(fig_shop_pie, use_container_width=True)
            
            if selected_shop != "상점을 선택하세요 (전체 데이터 유지)":
                shop_hist = hist_df[hist_df['店铺'] == selected_shop]
                shop_detail = detail_df[detail_df['店铺'] == selected_shop] if not detail_df.empty and '店铺' in detail_df.columns else pd.DataFrame()
                
                st.subheader(f"[{selected_shop}] 핵심 출고 지표")
                
                # 모바일 최적화: 2x3 그리드로 배치
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi4, kpi5, kpi6 = st.columns(3)
                
                # --- KPI 산출 로직 (History 마스터 기준) ---
                total_orders = len(shop_hist)
                
                cancel_mask = pd.Series(False, index=shop_hist.index)
                if '发货状态' in shop_hist.columns:
                    cancel_mask = shop_hist['发货状态'].isna() | (shop_hist['发货状态'].astype(str).str.strip() == '')
                
                if '发货时间' in shop_hist.columns:
                    bad_time_mask = shop_hist['发货时间'].astype(str).str.contains('0000-00-00', na=False)
                    cancel_mask = cancel_mask | bad_time_mask
                    
                canceled_count = int(cancel_mask.sum())
                
                pending_mask = pd.Series(False, index=shop_hist.index)
                if '发货시간' in shop_hist.columns:
                    pending_mask = shop_hist['发货시간'].isna() & ~cancel_mask
                    
                pending_count = int(pending_mask.sum())
                
                dispatched_mask = ~cancel_mask & ~pending_mask
                dispatched_count = int(dispatched_mask.sum())
                
                # 지연 출고(Delayed) 판단: 출고는 완료되었으나 접수일자보다 늦게 발송된 경우
                delayed_mask = pd.Series(False, index=shop_hist.index)
                if '发货일자' in shop_hist.columns and '접수일자' in shop_hist.columns:
                    delayed_mask = dispatched_mask & (shop_hist['发货일자'] > shop_hist['접수일자'])
                delayed_count = int(delayed_mask.sum())
                
                if '出库单号' in shop_hist.columns:
                    valid_order_ids = shop_hist.loc[dispatched_mask, '出库单号'].unique()
                    valid_shop_detail = shop_detail[shop_detail['出库单号'].isin(valid_order_ids)] if not shop_detail.empty else shop_detail
                else:
                    valid_shop_detail = shop_detail
                
                if '货品数量' in shop_hist.columns:
                    shop_hist_qty = pd.to_numeric(shop_hist.loc[dispatched_mask, '货品数量'], errors='coerce').fillna(0)
                    total_qty = shop_hist_qty.sum()
                else:
                    total_qty = 0
                
                kpi1.metric("총 접수 건수", f"{total_orders:,.0f} 건")
                kpi2.metric("출고 완료", f"{dispatched_count:,.0f} 건")
                kpi3.metric("총 발송수량", f"{total_qty:,.0f} 개")
                kpi4.metric("주문 취소", f"{canceled_count:,.0f} 건")
                kpi5.metric("미출고 (발송대기)", f"{pending_count:,.0f} 건")
                kpi6.metric("지연 출고 (익일이후)", f"{delayed_count:,.0f} 건")
                
                st.divider()
                
                # --- 차트 시각화 영역 (취소 및 미출고가 제외된 valid_shop_detail 사용) ---
                
                # 1. 월별 및 일별 주문/출고 트렌드
                if '접수일자' in shop_hist.columns and '发货일자' in shop_hist.columns:
                    st.markdown("## 1️⃣ 기간별 주문 및 출고 트렌드")
                    
                    recv_all = shop_hist.groupby('접수일자').size().reset_index(name='접수건수')
                    recv_all.rename(columns={'접수일자': '날짜'}, inplace=True)
                    
                    valid_dispatch = shop_hist[dispatched_mask]
                    disp_all = valid_dispatch.groupby('发货일자').size().reset_index(name='출고건수(완료)')
                    disp_all.rename(columns={'发货일자': '날짜'}, inplace=True)
                    
                    trend_all = pd.merge(recv_all, disp_all, on='날짜', how='outer').fillna(0).sort_values('날짜')
                    trend_all['날짜'] = pd.to_datetime(trend_all['날짜'])
                    trend_all['월(Month)'] = trend_all['날짜'].dt.strftime('%Y년 %m월')
                    
                    monthly_trend = trend_all.groupby('월(Month)')[['접수건수', '출고건수(완료)']].sum().reset_index()
                    
                    t1, t2 = st.tabs(["📅 월별 요약", "📆 일별 상세"])
                    with t1:
                        fig_month = px.bar(monthly_trend, x='월(Month)', y=['접수건수', '출고건수(완료)'], barmode='group', text_auto=True)
                        fig_month.update_xaxes(type='category')
                        st.plotly_chart(fig_month, use_container_width=True)
                    with t2:
                        fig_day = px.bar(trend_all, x='날짜', y=['접수건수', '출고건수(완료)'], barmode='group')
                        fig_day.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                        fig_day = apply_korean_date_format(fig_day)
                        st.plotly_chart(fig_day, use_container_width=True)
                    
                    st.divider()
                
                # 2. 고객 네트워크별 데이터
                if not valid_shop_detail.empty:
                    # 상점별로 네트워크 기준 컬럼을 다르게 적용
                    has_network_data = False
                    
                    if selected_shop == 'BOX_Export' and '客服备注' in valid_shop_detail.columns:
                        valid_shop_detail['고객네트워크'] = valid_shop_detail['客服备注'].fillna('기재안됨')
                        has_network_data = True
                    elif '客户网名' in valid_shop_detail.columns:
                        if selected_shop == 'B2C':
                            def map_network(name):
                                name_str = str(name)
                                if 'Sunmooh韩国直邮' in name_str:
                                    return 'Sunmooh'
                                elif '慧敏欧尼韩国直邮' in name_str:
                                    return '킵텐'
                                elif 'EA_Xiaohongshu' in name_str or 'HAUL41小红书' in name_str or '샤오홍수' in name_str:
                                    return '샤오홍슈'
                                else:
                                    return '대리'
                            valid_shop_detail['고객네트워크'] = valid_shop_detail['客户网名'].apply(map_network)
                        else:
                            valid_shop_detail['고객네트워크'] = valid_shop_detail['客户网名'].fillna('기재안됨')
                        has_network_data = True
                        
                    if has_network_data:
                        st.markdown("## 2️⃣ 고객 네트워크별 데이터 (출고 완료 기준)")
                        network_summary = valid_shop_detail.drop_duplicates(subset=['出库单号']).groupby('고객네트워크').size().reset_index(name='주문건수')
                        top_networks = network_summary.nlargest(10, '주문건수')
                        fig_network = px.bar(top_networks, x='주문건수', y='고객네트워크', orientation='h', color='주문건수', color_continuous_scale='Teal')
                        fig_network.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig_network, use_container_width=True)
                        st.divider()

                # 3. 브랜드별 출고 순위
                if not valid_shop_detail.empty and '品牌' in valid_shop_detail.columns:
                    st.markdown("## 3️⃣ 브랜드별 출고 순위 (출고 완료 기준)")
                    brand_summary = valid_shop_detail.groupby('品牌')['货品总数量'].sum().reset_index(name='총출고수량')
                    brand_summary = brand_summary.sort_values('총출고수량', ascending=False)
                    fig_brand = px.bar(brand_summary.head(15), x='品牌', y='총출고수량', color='총출고수량', color_continuous_scale='Magma', text_auto=True)
                    fig_brand.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_brand, use_container_width=True)
                    st.divider()
                    
                # 4. 상품별 출고
                if not valid_shop_detail.empty and '货品简称' in valid_shop_detail.columns and '货品总数量' in valid_shop_detail.columns:
                    st.markdown("## 4️⃣ 상품별 출고 현황 (베스트셀러 Top 15)")
                    
                    if '货品编号' in valid_shop_detail.columns:
                        valid_shop_detail['상품표시명'] = valid_shop_detail['货品编号'].astype(str) + " - " + valid_shop_detail['货品简称'].astype(str)
                    else:
                        valid_shop_detail['상품표시명'] = valid_shop_detail['货品简称']
                        
                    item_summary = valid_shop_detail.groupby('상품표시명')['货品总数量'].sum().reset_index()
                    top_items = item_summary.nlargest(15, '货品总数量')
                    fig_item = px.bar(top_items, x='货品总数量', y='상품표시명', orientation='h', labels={'상품표시명':'바코드 - 상품명'})
                    fig_item.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_item, use_container_width=True)
                    st.divider()
                    
                # 5. 특정 브랜드 상세 조회 (드롭다운)
                if not valid_shop_detail.empty and '品牌' in valid_shop_detail.columns and '货品简称' in valid_shop_detail.columns:
                    st.markdown("## 5️⃣ 특정 브랜드 상세 상품 조회")
                    brand_list = ["브랜드를 선택하세요"] + sorted(valid_shop_detail['品牌'].dropna().unique().tolist())
                    selected_brand = st.selectbox("📌 상세 상품 내역을 확인할 브랜드를 선택해 주세요:", brand_list)
                    
                    if selected_brand != "브랜드를 선택하세요":
                        target_prod_df = valid_shop_detail[valid_shop_detail['品牌'] == selected_brand]
                        st.markdown(f"**📦 '{selected_brand}' 상세 상품별 출고 수량**")
                        
                        brand_item_summary = target_prod_df.groupby('상품표시명')['货品总数量'].sum().reset_index()
                        brand_item_summary = brand_item_summary.sort_values('货品总数量', ascending=False)
                        
                        fig_brand_item = px.bar(brand_item_summary, x='货品总数量', y='상품표시명', orientation='h', labels={'상품표시명':'바코드 - 상품명', '货品总数量':'출고수량'}, color='货品总数量', color_continuous_scale='Blues')
                        fig_brand_item.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig_brand_item, use_container_width=True)
                        
                        # 표 형태로도 데이터 제공
                        st.dataframe(brand_item_summary.rename(columns={'상품표시명':'상품명', '货品总数量':'출고수량(개)'}), use_container_width=True, hide_index=True)
                        st.divider()

                # 6. 지역별 배송 목적지 현황 (중국 지도 히트맵)
                if not valid_shop_detail.empty and '省市区' in valid_shop_detail.columns:
                    st.markdown("## 6️⃣ 지역별 배송 현황 (지도)")
                    
                    # '广东省 深圳市 남산구' 형태에서 첫 번째 '广东省'만 추출
                    valid_shop_detail['지역(省)'] = valid_shop_detail['省市区'].apply(lambda x: str(x).split()[0] if pd.notna(x) and str(x).strip() != '' else '미상')
                    
                    region_summary = valid_shop_detail.drop_duplicates(subset=['出库单号']).groupby('지역(省)').size().reset_index(name='주문건수')
                    
                    china_geojson = get_china_geojson()
                    
                    fig_region = px.choropleth_mapbox(
                        region_summary,
                        geojson=china_geojson,
                        locations="지역(省)",
                        featureidkey="properties.name",
                        color="주문건수",
                        color_continuous_scale="Sunset",
                        mapbox_style="carto-positron",
                        zoom=3,
                        center={"lat": 35.8617, "lon": 104.1954},
                        opacity=0.6
                    )
                    fig_region.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                    
                    # 클릭 이벤트를 받아서 연동 (Streamlit 1.35 이상)
                    region_event = st.plotly_chart(fig_region, use_container_width=True, on_select="rerun")
                    st.divider()

                    st.markdown("### 🔍 클릭한 지역의 인기 상품 분석")
                    unique_regions = sorted([r for r in valid_shop_detail['지역(省)'].unique() if pd.notna(r) and r != '미상'])
                    
                    if unique_regions:
                        # 1순위: 사용자가 차트에서 클릭한 지역
                        clicked_region = None
                        if region_event and len(region_event.selection.points) > 0:
                            clicked_region = region_event.selection.points[0].get('location') or region_event.selection.points[0].get('y')
                        
                        # 2순위: 기본 지역 (가장 주문이 많은 지역)
                        top_regions = region_summary.sort_values(by='주문건수', ascending=False)
                        default_region = top_regions.iloc[0]['지역(省)'] if not top_regions.empty and top_regions.iloc[0]['지역(省)'] != '미상' else unique_regions[0]
                        
                        # 클릭된 지역이 있으면 그 지역을 현재 선택된 지역으로 지정
                        current_region = clicked_region if clicked_region in unique_regions else default_region
                        current_index = unique_regions.index(current_region)
                        
                        selected_region = st.selectbox("👆 위 차트에서 막대를 클릭하거나 아래에서 지역을 선택하세요:", unique_regions, index=current_index)
                        
                        region_data = valid_shop_detail[valid_shop_detail['지역(省)'] == selected_region]
                        
                        if not region_data.empty and '货品简称' in region_data.columns:
                            region_data['상품명'] = region_data.apply(
                                lambda row: str(row['货品简称']) if pd.notna(row['货品简称']) and str(row['货品简称']).strip() != '' else str(row.get('货品编号', '이름없음')),
                                axis=1
                            )
                            qty_col = '数量' if '数量' in region_data.columns else '货品总数量'
                            
                            region_prod_summary = region_data.groupby('상품명')[qty_col].sum().reset_index(name='출고수량')
                            top_reg_prods = region_prod_summary.nlargest(10, '출고수량')
                            
                            fig_reg_prod = px.bar(top_reg_prods, x='출고수량', y='상품명', orientation='h', color='출고수량', color_continuous_scale='Teal', text_auto=True)
                            fig_reg_prod.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig_reg_prod, use_container_width=True)
                            
                            st.dataframe(top_reg_prods, use_container_width=True, hide_index=True)
                        else:
                            st.info("해당 지역의 상세 상품 데이터가 없습니다.")
                
            else:
                st.write("👆 **위 드롭다운 메뉴에서 상점을 선택하시면 세부 데이터(브랜드, 상품 등)가 나타납니다.**")

else:
    st.warning("데이터 폴더에 파일이 없습니다. 안내에 따라 엑셀 파일을 넣어주세요.")
    st.info("💡 **데이터 폴더 구조 안내**\n"
            "1. `data_detailed` 폴더 안에 기존에 쓰시던 **상세 출고 내역** 파일들을 넣어주세요.\n"
            "2. `data_history` 폴더 안에 접수시간이 포함된 **일반 출고 내역** 파일들을 넣어주세요.")