import sys
import pandas as pd

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find("if view_mode == '👑 대표님 보고용 (Internal View)':")
end_idx = content.find("st.stop()", start_idx) + len("st.stop()")

if start_idx == -1 or end_idx == -1:
    print("Could not find the block")
    sys.exit(1)

new_block = """if view_mode == '👑 대표님 보고용 (Internal View)':
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

        # 전 기간(비교용) 필터링
        duration = (end_date - start_date).days + 1
        prev_end_date = start_date - datetime.timedelta(days=1)
        prev_start_date = prev_end_date - datetime.timedelta(days=duration - 1)
        
        prev_in_df = in_df[(in_df['입고일자'] >= prev_start_date) & (in_df['입고일자'] <= prev_end_date)] if not in_df.empty and '입고일자' in in_df.columns else pd.DataFrame()
        prev_hist_df = hist_df[(hist_df['접수일자'] >= prev_start_date) & (hist_df['접수일자'] <= prev_end_date)] if not hist_df.empty and '접수일자' in hist_df.columns else pd.DataFrame()
        prev_detail_df = detail_df[(detail_df['접수일자'] >= prev_start_date) & (detail_df['접수일자'] <= prev_end_date)] if not detail_df.empty and '접수일자' in detail_df.columns else pd.DataFrame()

        st.markdown(f"### 📊 센터 핵심 KPI ({start_date.strftime('%y.%m.%d')} ~ {end_date.strftime('%y.%m.%d')})")
        
        # Calculate KPIs
        total_in_qty = curr_in_df['数量'].sum() if not curr_in_df.empty and '数量' in curr_in_df.columns else 0
        total_in_box = curr_in_df['绩效箱数'].sum() if not curr_in_df.empty and '绩效箱数' in curr_in_df.columns else 0
        total_out_orders = len(curr_hist_df) if not curr_hist_df.empty else 0
        total_out_qty = curr_detail_df['货品总数量'].sum() if not curr_detail_df.empty and '货品总数量' in curr_detail_df.columns else 0
        
        prev_in_qty = prev_in_df['数量'].sum() if not prev_in_df.empty and '数量' in prev_in_df.columns else 0
        prev_in_box = prev_in_df['绩效箱数'].sum() if not prev_in_df.empty and '绩效箱数' in prev_in_df.columns else 0
        prev_out_orders = len(prev_hist_df) if not prev_hist_df.empty else 0
        prev_out_qty = prev_detail_df['货品总数量'].sum() if not prev_detail_df.empty and '货品总数量' in prev_detail_df.columns else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("📦 총 입고 수량", f"{total_in_qty:,.0f} 개", f"{total_in_qty - prev_in_qty:,.0f} 개 (직전 동기간 대비)")
        kpi2.metric("📦 총 입고 박스", f"{total_in_box:,.1f} Box", f"{total_in_box - prev_in_box:,.1f} Box (직전 동기간 대비)")
        kpi3.metric("🚀 총 출고 주문건수", f"{total_out_orders:,.0f} 건", f"{total_out_orders - prev_out_orders:,.0f} 건 (직전 동기간 대비)")
        kpi4.metric("🚀 총 출고 수량", f"{total_out_qty:,.0f} 개", f"{total_out_qty - prev_out_qty:,.0f} 개 (직전 동기간 대비)")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 일별 입/출고 수량 트렌드")
            in_trend = pd.DataFrame()
            if not curr_in_df.empty and '입고일자' in curr_in_df.columns:
                in_trend = curr_in_df.groupby('입고일자')['数量'].sum().reset_index().rename(columns={'입고일자': '일자', '数量': '입고수량'})
            
            out_trend = pd.DataFrame()
            if not curr_hist_df.empty and '접수일자' in curr_hist_df.columns:
                out_trend = curr_hist_df.groupby('접수일자').size().reset_index(name='출고주문건수').rename(columns={'접수일자': '일자'})
            
            if not in_trend.empty and not out_trend.empty:
                trend_df = pd.merge(in_trend, out_trend, on='일자', how='outer').fillna(0).sort_values('일자')
            elif not in_trend.empty:
                trend_df = in_trend.copy()
                trend_df['출고주문건수'] = 0
            elif not out_trend.empty:
                trend_df = out_trend.copy()
                trend_df['입고수량'] = 0
            else:
                trend_df = pd.DataFrame(columns=['일자', '입고수량', '출고주문건수'])
                
            if not trend_df.empty:
                import plotly.express as px
                fig_trend = px.line(trend_df, x='일자', y=['입고수량', '출고주문건수'], markers=True, title="일자별 물동량 추이")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("데이터가 부족하여 트렌드를 표시할 수 없습니다.")
                
        with col2:
            st.markdown("### 🚚 택배사별 출고 점유율")
            if not curr_hist_df.empty and '快递公司' in curr_hist_df.columns:
                courier_summary = curr_hist_df.groupby('快递公司').size().reset_index(name='건수')
                import plotly.express as px
                fig_courier = px.pie(courier_summary, names='快递公司', values='건수', hole=0.3, title="택배사 배분 현황 (주문건 기준)")
                st.plotly_chart(fig_courier, use_container_width=True)
            else:
                st.info("택배사 데이터가 없습니다.")

        st.divider()
        
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("### 🏆 Top 5 고객사 (주문건수 기준)")
            if not curr_hist_df.empty and '店铺' in curr_hist_df.columns:
                top_shops = curr_hist_df.groupby('店铺').size().reset_index(name='건수').sort_values('건수', ascending=False).head(5)
                import plotly.express as px
                fig_top_shops = px.bar(top_shops, x='건수', y='店铺', orientation='h', title="상점(고객사)별 상위 물동량")
                fig_top_shops.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top_shops, use_container_width=True)
            else:
                st.info("고객사(상점) 데이터가 없습니다.")
                
        with col4:
            st.markdown("### 🚨 출고 예외 상태 현황 (지연/취소)")
            if not curr_hist_df.empty and '发货状态' in curr_hist_df.columns:
                status_summary = curr_hist_df.groupby('发货状态').size().reset_index(name='건수')
                import plotly.express as px
                fig_status = px.pie(status_summary, names='发货状态', values='건수', title="출고 진행 상태 분류")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("발송 상태 데이터가 없습니다.")
                
        st.divider()
        
        st.markdown("### 📊 최근 6개월 월별 트렌드 (입출고 통합 비교)")
        # Group all data (unfiltered by date_range, to show historical months) by Month
        in_monthly = in_df.copy() if not in_df.empty else pd.DataFrame()
        out_monthly = hist_df.copy() if not hist_df.empty else pd.DataFrame()
        
        if not in_monthly.empty and '입고일자' in in_monthly.columns:
            in_monthly['월'] = pd.to_datetime(in_monthly['입고일자']).dt.to_period('M').astype(str)
            in_m_trend = in_monthly.groupby('월')['数量'].sum().reset_index().rename(columns={'数量': '입고수량'})
        else:
            in_m_trend = pd.DataFrame(columns=['월', '입고수량'])
            
        if not out_monthly.empty and '접수일자' in out_monthly.columns:
            out_monthly['월'] = pd.to_datetime(out_monthly['접수일자']).dt.to_period('M').astype(str)
            out_m_trend = out_monthly.groupby('월').size().reset_index(name='출고주문건수')
        else:
            out_m_trend = pd.DataFrame(columns=['월', '출고주문건수'])
            
        if not in_m_trend.empty and not out_m_trend.empty:
            m_trend_df = pd.merge(in_m_trend, out_m_trend, on='월', how='outer').fillna(0).sort_values('월').tail(6)
        elif not in_m_trend.empty:
            m_trend_df = in_m_trend.sort_values('월').tail(6)
            m_trend_df['출고주문건수'] = 0
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
            fig_mom.add_trace(go.Scatter(x=m_trend_df['월'], y=m_trend_df['출고주문건수'], name='출고 주문(건)', mode='lines+markers+text', text=m_trend_df['출고주문건수'], textposition='top center', line=dict(color='red', width=3)), secondary_y=True)
            fig_mom.update_layout(title="최근 6개월 입고 수량 및 출고 주문건수 비교", barmode='group')
            fig_mom.update_yaxes(title_text="입고 수량", secondary_y=False)
            fig_mom.update_yaxes(title_text="출고 주문건수", secondary_y=True)
            st.plotly_chart(fig_mom, use_container_width=True)
        else:
            st.info("데이터가 부족하여 월별 트렌드를 표시할 수 없습니다.")

        st.stop()"""

new_content = content[:start_idx] + new_block + content[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully replaced.")
