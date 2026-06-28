import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject raw backups
old_client_start = """    if view_mode == '💼 고객사 배포용 (Client View)':
        with st.expander("📅 출고 데이터 필터", expanded=True):"""

new_client_start = """    if view_mode == '💼 고객사 배포용 (Client View)':
        raw_client_hist_df = hist_df.copy()
        raw_client_detail_df = detail_df.copy()
        
        with st.expander("📅 출고 데이터 필터", expanded=True):"""

# 2. Modify Turnover Analysis
old_turnover = """            st.markdown("#### 🔄 재고 회전율 분석 (최근 출고량 기반)")
            if not detail_df.empty and '货品简称' in detail_df.columns and '货品数量' in detail_df.columns and '库存' in inv_df.columns:
                cancel_mask = pd.Series(False, index=hist_df.index)
                if '发货状态' in hist_df.columns:
                    cancel_mask = hist_df['发货状态'].isna() | (hist_df['发货状态'].astype(str).str.strip() == '')
                canceled_orders = set(hist_df[cancel_mask]['出库单号']) if '出库单号' in hist_df.columns else set()
                
                valid_out = detail_df[~detail_df['出库单号'].isin(canceled_orders)] if '出库单号' in detail_df.columns else detail_df
                out_sum = valid_out.groupby('货品简称')['货品数量'].sum().reset_index().rename(columns={'货品数量': '최근출고량'})"""

new_turnover = """            st.markdown("#### 🔄 재고 회전율 분석 (선택 상자 및 지정 기간 기반)")
            
            # 독립적인 출고 기간 필터 (기본값: 상단 글로벌 필터 기간)
            t_min = raw_client_hist_df['접수일자'].dropna().min() if 'raw_client_hist_df' in locals() and not raw_client_hist_df.empty and '접수일자' in raw_client_hist_df.columns else None
            t_max = raw_client_hist_df['접수일자'].dropna().max() if 'raw_client_hist_df' in locals() and not raw_client_hist_df.empty and '접수일자' in raw_client_hist_df.columns else None
            
            t_def_start = start_date if 'start_date' in locals() else t_min
            t_def_end = end_date if 'end_date' in locals() else t_max
            
            if t_min and t_max:
                t_date_range = st.date_input("📊 재고 회전율 산출을 위한 출고 기간을 선택하세요", value=(t_def_start, t_def_end), format="YYYY-MM-DD", key="turn_date")
            else:
                t_date_range = None
                
            if t_date_range and isinstance(t_date_range, tuple) and len(t_date_range) == 2:
                t_start, t_end = t_date_range
                t_hist = raw_client_hist_df[(raw_client_hist_df['접수일자'] >= t_start) & (raw_client_hist_df['접수일자'] <= t_end)] if 'raw_client_hist_df' in locals() else hist_df
                t_detail = raw_client_detail_df[(raw_client_detail_df['접수일자'] >= t_start) & (raw_client_detail_df['접수일자'] <= t_end)] if 'raw_client_detail_df' in locals() else detail_df
            else:
                t_hist = raw_client_hist_df if 'raw_client_hist_df' in locals() else hist_df
                t_detail = raw_client_detail_df if 'raw_client_detail_df' in locals() else detail_df
                
            # 상점 연동 필터 적용
            if 'selected_shop' in locals() and selected_shop != "상점을 선택하세요 (전체 데이터 유지)":
                if '店铺' in t_hist.columns:
                    t_hist = t_hist[t_hist['店铺'] == selected_shop]
                if '店铺' in t_detail.columns:
                    t_detail = t_detail[t_detail['店铺'] == selected_shop]

            if not t_detail.empty and '货品简称' in t_detail.columns and '货品数量' in t_detail.columns and '库存' in inv_df.columns:
                cancel_mask = pd.Series(False, index=t_hist.index)
                if '发货状态' in t_hist.columns:
                    cancel_mask = t_hist['发货状态'].isna() | (t_hist['发货状态'].astype(str).str.strip() == '')
                canceled_orders = set(t_hist[cancel_mask]['出库单号']) if '出库单号' in t_hist.columns else set()
                
                valid_out = t_detail[~t_detail['出库单号'].isin(canceled_orders)] if '出库单号' in t_detail.columns else t_detail
                out_sum = valid_out.groupby('货品简称')['货品数量'].sum().reset_index().rename(columns={'货品数量': '최근출고량'})"""

if old_client_start in content and old_turnover in content:
    content = content.replace(old_client_start, new_client_start)
    content = content.replace(old_turnover, new_turnover)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success: UI modifications applied.")
else:
    print("Error: Could not find target strings for replacement.")
