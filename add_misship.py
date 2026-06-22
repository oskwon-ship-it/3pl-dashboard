import os
import glob

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add misship_files glob and loading logic
load_data_end_old = """    qk_df = pd.concat(qk_list, ignore_index=True) if qk_list else pd.DataFrame()
    if not qk_df.empty and '오더일자' in qk_df.columns:
        qk_df['오더일자'] = pd.to_datetime(qk_df['오더일자'], errors='coerce').dt.date

    return hist_df, detail_df, in_df, cj_df, qk_df"""

load_data_end_new = """    qk_df = pd.concat(qk_list, ignore_index=True) if qk_list else pd.DataFrame()
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

    return hist_df, detail_df, in_df, cj_df, qk_df, misship_df"""

code = code.replace(load_data_end_old, load_data_end_new)

# 2. Update the load_data call
load_data_call_old = "hist_df, detail_df, in_df, cj_df, qk_df = load_data(get_data_hash())"
load_data_call_new = "hist_df, detail_df, in_df, cj_df, qk_df, misship_df = load_data(get_data_hash())"
code = code.replace(load_data_call_old, load_data_call_new)

# 3. Add date filter for misship_df
date_filter_old = "curr_qk_df = qk_df[(qk_df['오더일자'] >= start_date) & (qk_df['오더일자'] <= end_date)] if not qk_df.empty and '오더일자' in qk_df.columns else pd.DataFrame()"
date_filter_new = "curr_qk_df = qk_df[(qk_df['오더일자'] >= start_date) & (qk_df['오더일자'] <= end_date)] if not qk_df.empty and '오더일자' in qk_df.columns else pd.DataFrame()\n        curr_misship_df = misship_df[(misship_df['접수일'] >= start_date) & (misship_df['접수일'] <= end_date)] if not misship_df.empty and '접수일' in misship_df.columns else pd.DataFrame()"
code = code.replace(date_filter_old, date_filter_new)

# 4. Replace the old pie chart
old_pie = """        with col4:
            st.markdown("### 🚨 출고 예외 상태 현황 (지연/취소)")
            if not curr_hist_df.empty and '发货状态' in curr_hist_df.columns:
                status_summary = curr_hist_df.groupby('发货状态').size().reset_index(name='건수')
                import plotly.express as px
                fig_status = px.pie(status_summary, names='发货状态', values='건수', title="출고 진행 상태 분류")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("발송 상태 데이터가 없습니다.")"""

new_pie = """        with col4:
            st.markdown("### 🚨 오출고 현황")
            if not curr_misship_df.empty:
                # 총 오출고 건수 계산 (각 행을 1건으로)
                total_misship = len(curr_misship_df)
                
                if '비고' in curr_misship_df.columns:
                    # 빈 값을 '기타/미분류'로 변경
                    ms_summary = curr_misship_df.copy()
                    ms_summary['비고'] = ms_summary['비고'].fillna('기타/미분류')
                    status_summary = ms_summary.groupby('비고').size().reset_index(name='건수')
                    
                    import plotly.express as px
                    fig_status = px.pie(status_summary, names='비고', values='건수', hole=0.4)
                    fig_status.update_traces(textposition='inside', textinfo='percent+label')
                    fig_status.update_layout(
                        title=f"오출고 사유별 비율 (총 {total_misship}건)",
                        showlegend=False,
                        margin=dict(t=40, b=0, l=0, r=0)
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.metric("총 오출고 건수", f"{total_misship} 건")
            else:
                st.info("해당 기간에 오출고 데이터가 없습니다.")"""
code = code.replace(old_pie, new_pie)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
