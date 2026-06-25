import sys
import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

inv_load_code = """
    # 6. 재고 현황(Inventory) 로드 (로케이션 제외, 최소 컬럼만 로드)
    import glob
    inv_files = glob.glob("data_inventory/*.csv") + glob.glob("data_inventory/*.xlsx") + glob.glob("data_inventory/*.xls")
    inv_use_cols = ['货品简称', '库存', '有效期', '距离到期天数']
    
    inv_list = []
    for file in inv_files:
        if "~$" in file: continue
        try:
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
                temp_df = temp_df[[c for c in inv_use_cols if c in temp_df.columns]]
            else:
                def inv_col_filter(c): return c in inv_use_cols
                temp_df = pd.read_excel(file, usecols=inv_col_filter, engine='openpyxl' if file.endswith('.xlsx') else None)
            
            if 'clean_csv_junk' in globals():
                temp_df = clean_csv_junk(temp_df)
            inv_list.append(temp_df)
        except: pass
        
    inv_df = pd.concat(inv_list, ignore_index=True) if inv_list else pd.DataFrame()
    if not inv_df.empty:
        for col in ['库存', '距离到期天数']:
            if col in inv_df.columns:
                inv_df[col] = pd.to_numeric(inv_df[col], errors='coerce').fillna(0)
"""

new_lines = []
for line in lines:
    if 'return hist_df, detail_df, in_df, cj_df, qk_df, misship_df' in line:
        new_lines.append(inv_load_code)
        line = line.replace('misship_df', 'misship_df, inv_df')
    if 'hist_df, detail_df, in_df, cj_df, qk_df, misship_df = load_data' in line:
        line = line.replace('misship_df =', 'misship_df, inv_df =')
        
    new_lines.append(line)

ui_code = """
        st.divider()
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
                        st.dataframe(fast_movers, use_container_width=True, hide_index=True)
        else:
            st.info("data_inventory 폴더에 재고 데이터가 없습니다.")
"""

final_lines = []
for i, line in enumerate(new_lines):
    if line.startswith('else:') and '데이터 폴더에 파일이 없습니다' in new_lines[i+1]:
        final_lines.append(ui_code + "\n")
    final_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("Inventory logic inserted.")
