import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update inv_use_cols
old_cols = "inv_use_cols = ['货品简称', '库存', '有效期', '距离到期天数']"
new_cols = "inv_use_cols = ['货品编号', '货品简称', '库存', '有效期', '距离到期天数']"
content = content.replace(old_cols, new_cols)

# 2. Update UI block
old_ui = """        st.divider()
        st.markdown("### 📦 재고 현황 데이터")
        if not inv_df.empty:
            st.markdown("#### 🚨 유통기한 및 재고 회전율 경고 시스템")
            warn_col1, warn_col2 = st.columns(2)
            
            if '距离到期天数' in inv_df.columns:
                danger_items = inv_df[(inv_df['距离到期天数'] > 0) & (inv_df['距离到期天数'] <= 90)]
                warning_items = inv_df[(inv_df['距离到期天数'] > 90) & (inv_df['距离到期天数'] <= 180)]
                with warn_col1:
                    st.error(f"🔴 90일 이내 만료 상품: {len(danger_items)}건")
                    if not danger_items.empty:
                        show_cols_exp = [c for c in ['货品简称', '库存', '有效期', '距离到期天数'] if c in danger_items.columns]
                        st.dataframe(danger_items[show_cols_exp].sort_values('距离到期天数'), use_container_width=True, hide_index=True)
                with warn_col2:
                    st.warning(f"🟡 180일 이내 만료 상품: {len(warning_items)}건")
                    if not warning_items.empty:
                        show_cols_exp = [c for c in ['货品简称', '库存', '有效期', '距离到期天数'] if c in warning_items.columns]
                        st.dataframe(warning_items[show_cols_exp].sort_values('距离到期天数'), use_container_width=True, hide_index=True)
                        
            st.markdown("#### 🔄 재고 회전율 분석 (최근 출고량 기반)")
            if not detail_df.empty and '货品简称' in detail_df.columns and '货品数量' in detail_df.columns and '库存' in inv_df.columns:
                cancel_mask = pd.Series(False, index=hist_df.index)
                if '发货状态' in hist_df.columns:
                    cancel_mask = hist_df['发货状态'].isna() | (hist_df['发货状态'].astype(str).str.strip() == '')
                canceled_orders = set(hist_df[cancel_mask]['出库单号']) if '出库单号' in hist_df.columns else set()
                
                valid_out = detail_df[~detail_df['出库单号'].isin(canceled_orders)] if '出库单号' in detail_df.columns else detail_df
                out_sum = valid_out.groupby('货品简称')['货品数量'].sum().reset_index().rename(columns={'货品数量': '최근출고량'})
                inv_sum = inv_df.groupby('货品简称')['库存'].sum().reset_index()
                turnover_df = pd.merge(inv_sum, out_sum, on='货品简称', how='left').fillna(0)
                
                dead_stock = turnover_df[(turnover_df['库存'] >= 100) & (turnover_df['최근출고량'] == 0)].sort_values('库存', ascending=False)
                fast_movers = turnover_df[(turnover_df['库存'] < 100) & (turnover_df['최근출고량'] >= 100)].sort_values('최근출고량', ascending=False)
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.info(f"❄️ 악성 재고 경고 (재고 100+ & 최근 출고 0건): {len(dead_stock)}건")
                    if not dead_stock.empty:
                        st.dataframe(dead_stock, use_container_width=True, hide_index=True)
                with t_col2:
                    st.success(f"🔥 발주 시급 상품 (재고 <100 & 최근 출고 100+): {len(fast_movers)}건")
                    if not fast_movers.empty:
                        st.dataframe(fast_movers, use_container_width=True, hide_index=True)"""

new_ui = """        st.divider()
        st.markdown("### 📦 재고 현황 데이터")
        if not inv_df.empty:
            st.markdown("#### 🚨 유통기한 및 재고 회전율 경고 시스템")
            
            # 여기서 바코드 - 상품명 통합 (100% 한글화)
            if '货品编号' in inv_df.columns and '货品简称' in inv_df.columns:
                inv_df['바코드 - 상품명'] = inv_df['货品编号'].astype(str) + " - " + inv_df['货品简称'].astype(str)
            elif '货品简称' in inv_df.columns:
                inv_df['바코드 - 상품명'] = inv_df['货品简称']
                
            rename_dict = {
                '바코드 - 상품명': '바코드 - 상품명',
                '库存': '현재고(개)',
                '有效期': '유통기한',
                '距离到期天数': '잔여일수(일)'
            }
            
            warn_col1, warn_col2 = st.columns(2)
            
            if '距离到期天数' in inv_df.columns:
                danger_items = inv_df[(inv_df['距离到期天数'] > 0) & (inv_df['距离到期天数'] <= 90)]
                warning_items = inv_df[(inv_df['距离到期天数'] > 90) & (inv_df['距离到期天数'] <= 180)]
                with warn_col1:
                    st.error(f"🔴 90일 이내 만료 상품: {len(danger_items)}건")
                    if not danger_items.empty:
                        show_cols_exp = [c for c in ['바코드 - 상품명', '库存', '有效期', '距离到期天数'] if c in danger_items.columns]
                        st.dataframe(danger_items[show_cols_exp].sort_values('距离到期天数').rename(columns=rename_dict), use_container_width=True, hide_index=True)
                with warn_col2:
                    st.warning(f"🟡 180일 이내 만료 상품: {len(warning_items)}건")
                    if not warning_items.empty:
                        show_cols_exp = [c for c in ['바코드 - 상품명', '库存', '有效期', '距离到期天数'] if c in warning_items.columns]
                        st.dataframe(warning_items[show_cols_exp].sort_values('距离到期天数').rename(columns=rename_dict), use_container_width=True, hide_index=True)
                        
            st.markdown("#### 🔄 재고 회전율 분석 (최근 출고량 기반)")
            if not detail_df.empty and '货品简称' in detail_df.columns and '货品数量' in detail_df.columns and '库存' in inv_df.columns:
                cancel_mask = pd.Series(False, index=hist_df.index)
                if '发货状态' in hist_df.columns:
                    cancel_mask = hist_df['发货状态'].isna() | (hist_df['发货状态'].astype(str).str.strip() == '')
                canceled_orders = set(hist_df[cancel_mask]['出库单号']) if '出库单号' in hist_df.columns else set()
                
                valid_out = detail_df[~detail_df['出库单号'].isin(canceled_orders)] if '出库单号' in detail_df.columns else detail_df
                out_sum = valid_out.groupby('货品简称')['货品数量'].sum().reset_index().rename(columns={'货品数量': '최근출고량'})
                inv_sum = inv_df.groupby('货品简称')['库存'].sum().reset_index()
                turnover_df = pd.merge(inv_sum, out_sum, on='货品简称', how='left').fillna(0)
                
                if '바코드 - 상품명' in inv_df.columns:
                    name_map = inv_df.drop_duplicates('货品简称').set_index('货品简称')['바코드 - 상품명']
                    turnover_df['바코드 - 상품명'] = turnover_df['货品简称'].map(name_map)
                else:
                    turnover_df['바코드 - 상품명'] = turnover_df['货品简称']
                    
                dead_stock = turnover_df[(turnover_df['库存'] >= 100) & (turnover_df['최근출고량'] == 0)].sort_values('库存', ascending=False)
                fast_movers = turnover_df[(turnover_df['库存'] < 100) & (turnover_df['최근출고량'] >= 100)].sort_values('최근출고량', ascending=False)
                
                t_rename = {
                    '바코드 - 상품명': '바코드 - 상품명',
                    '库存': '현재고(개)',
                    '최근출고량': '최근출고량(개)'
                }
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.info(f"❄️ 악성 재고 경고 (재고 100+ & 최근 출고 0건): {len(dead_stock)}건")
                    if not dead_stock.empty:
                        show_cols = [c for c in ['바코드 - 상품명', '库存', '최근출고량'] if c in dead_stock.columns]
                        st.dataframe(dead_stock[show_cols].rename(columns=t_rename), use_container_width=True, hide_index=True)
                with t_col2:
                    st.success(f"🔥 발주 시급 상품 (재고 <100 & 최근 출고 100+): {len(fast_movers)}건")
                    if not fast_movers.empty:
                        show_cols = [c for c in ['바코드 - 상품명', '库存', '최근출고량'] if c in fast_movers.columns]
                        st.dataframe(fast_movers[show_cols].rename(columns=t_rename), use_container_width=True, hide_index=True)"""

if old_ui in content:
    content = content.replace(old_ui, new_ui)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Failed to find old UI block")
