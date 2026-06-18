import streamlit as st
import pandas as pd
import plotly.express as px
import glob

st.set_page_config(page_title="3PL 맞춤형 대시보드", page_icon="📦", layout="wide")

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

@st.cache_data(ttl=3600)  # 1시간 단위 캐시 갱신 추가
def load_data():
    detailed_files = glob.glob("data_detailed/*.xlsx") + glob.glob("data_detailed/*.xls")
    history_files = glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")
    inbound_files = glob.glob("data_inbound/*.xlsx") + glob.glob("data_inbound/*.xls")
    
    # 1. 출고 내역(History) 로드 - 메인 마스터 데이터
    history_list = []
    for file in history_files:
        if "~$" in file: continue
        try:
            temp_df = pd.read_excel(file)
            history_list.append(temp_df)
        except Exception as e:
            st.warning(f"출고내역 파일 '{file}' 읽기 오류: {e}")
            
    hist_df = pd.concat(history_list, ignore_index=True) if history_list else pd.DataFrame()
        
    # 2. 상세 출고 내역(Detailed) 로드 - 상품 분석 데이터
    df_list = []
    for file in detailed_files:
        if "~$" in file: continue
        try:
            temp_df = pd.read_excel(file)
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"상세 파일 '{file}' 읽기 오류: {e}")
            
    detail_df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        
    # 3. 마스터 데이터를 상세 내역에 병합 (매칭 기준: 출고단호(주문번호))
    if not hist_df.empty and not detail_df.empty:
        if '出库单号' in hist_df.columns and '出库单号' in detail_df.columns:
            hist_unique = hist_df.drop_duplicates(subset=['出库单号'])
            
            # 병합할 핵심 열 (접수시간, 상점 등)
            merge_cols = ['出库单号']
            for col in ['审核时间', '店铺', '客服备注']:
                if col in hist_unique.columns:
                    merge_cols.append(col)
                    # 상세 내역에 이미 있는 경우 충돌 방지를 위해 삭제
                    if col in detail_df.columns:
                        detail_df = detail_df.drop(columns=[col])
                        
            detail_df = detail_df.merge(hist_unique[merge_cols], on='出库单号', how='left')

    # 4. 상점명(店铺) 통합 처리
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

    # 5. 날짜 전처리 (마스터 테이블 기준)
    if not hist_df.empty:
        if '审核时间' in hist_df.columns:
            hist_df['접수시간'] = pd.to_datetime(hist_df['审核时间'], errors='coerce')
            hist_df['접수일자'] = hist_df['접수시간'].dt.date
            
        if '发货时间' in hist_df.columns:
            temp_time = hist_df['发货时间'].astype(str).replace('0000-00-00 00:00:00', pd.NaT).replace('0000-00-00', pd.NaT)
            hist_df['发货시간'] = pd.to_datetime(temp_time, errors='coerce')
            hist_df['发货일자'] = hist_df['发货시간'].dt.date
            
    if not detail_df.empty:
        if '审核时间' in detail_df.columns:
            detail_df['접수시간'] = pd.to_datetime(detail_df['审核时间'], errors='coerce')
            detail_df['접수일자'] = detail_df['접수시간'].dt.date
            
        if '发货时间' in detail_df.columns:
            detail_df['发货시간'] = pd.to_datetime(detail_df['发货时间'], errors='coerce')
            detail_df['发货일자'] = detail_df['发货시간'].dt.date
            
        if '货品总数量' in detail_df.columns:
            detail_df['货品总数量'] = pd.to_numeric(detail_df['货品总数量'], errors='coerce').fillna(0)
            
    # 6. 입고 내역 로드
    in_list = []
    for file in inbound_files:
        if "~$" in file: continue
        try:
            temp_df = pd.read_excel(file)
            in_list.append(temp_df)
        except Exception as e:
            st.warning(f"입고 파일 '{file}' 읽기 오류: {e}")
            
    in_df = pd.concat(in_list, ignore_index=True) if in_list else pd.DataFrame()
    
    # 입고 날짜 전처리
    if not in_df.empty:
        if '审核时间' in in_df.columns:
            in_df['입고시간'] = pd.to_datetime(in_df['审核时间'], errors='coerce')
            in_df['입고일자'] = in_df['입고시간'].dt.date
        for col in ['数量', '绩效箱数']:
            if col in in_df.columns:
                in_df[col] = pd.to_numeric(in_df[col], errors='coerce').fillna(0)
                
    return hist_df, detail_df, in_df

hist_df, detail_df, in_df = load_data()

if not hist_df.empty or not in_df.empty:
    st.sidebar.title("🔍 보기 모드 설정")
    
    dashboard_type = st.sidebar.radio(
        "📊 조회할 대시보드를 선택하세요:",
        ('📦 출고 대시보드 (Outbound)', '📥 입고 대시보드 (Inbound)')
    )
    st.sidebar.divider()
    
    view_mode = st.sidebar.radio(
        "어떤 용도의 대시보드를 보시겠습니까?",
        ('💼 고객사 배포용 (Client View)', '👑 대표님 보고용 (Internal View)')
    )
    st.sidebar.divider()
    
    if dashboard_type == '📥 입고 대시보드 (Inbound)':
        st.title("📥 입고(Inbound) 운영 리포트")
        if in_df.empty:
            st.warning("data_inbound 폴더에 입고 데이터 파일이 없습니다. 엑셀 파일을 넣어주세요.")
            st.stop()
            
        st.sidebar.subheader("📅 공통 필터 (입고일 기준)")
        if '입고일자' in in_df.columns:
            min_date = in_df['입고일자'].dropna().min()
            max_date = in_df['입고일자'].dropna().max()
            
            date_range = st.sidebar.date_input("조회할 기간을 선택하세요", value=(min_date, max_date), format="YYYY-MM-DD")
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                in_df = in_df[(in_df['입고일자'] >= start_date) & (in_df['입고일자'] <= end_date)]
                selected_period_text = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
            else:
                selected_period_text = "전체 기간"
        
        st.markdown("## 1️⃣ 화주(货主) 선택 및 데이터 요약")
        if '货主' in in_df.columns:
            shipper_list = ["전체 화주 보기"] + sorted(in_df['货主'].dropna().unique().tolist())
            selected_shipper = st.selectbox("📌 상세 분석을 진행할 화주를 선택해 주세요:", shipper_list)
            
            if selected_shipper != "전체 화주 보기":
                in_df = in_df[in_df['货主'] == selected_shipper]
                
        # 입고 핵심 KPI
        st.subheader(f"[{selected_shipper if 'selected_shipper' in locals() and selected_shipper != '전체 화주 보기' else '전체'}] 핵심 입고 지표")
        ikpi1, ikpi2, ikpi3 = st.columns(3)
        
        total_in_orders = in_df['入库单号'].nunique() if '入库单号' in in_df.columns else 0
        total_in_qty = in_df['数量'].sum() if '数量' in in_df.columns else 0
        total_in_box = in_df['绩效箱数'].sum() if '绩效箱数' in in_df.columns else 0
        
        ikpi1.metric("총 입고 건수 (단호 기준)", f"{total_in_orders:,.0f} 건")
        ikpi2.metric("총 입고 상품 수량", f"{total_in_qty:,.0f} 개")
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
                fig_brand_item.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_brand_item, use_container_width=True)
                
                st.dataframe(brand_item_summary.rename(columns={'상품표시명':'상품명', '数量':'입고수량(개)'}), use_container_width=True)

        st.stop() # 입고 대시보드 렌더링 후 종료 (아래 출고 로직 무시)
        
    # ================== 출고 대시보드 로직 시작 ==================
    if hist_df.empty:
        st.warning("data_history 폴더에 출고 데이터 파일이 없습니다. 엑셀 파일을 넣어주세요.")
        st.stop()
    
    st.sidebar.subheader("📅 공통 필터 (접수일 기준)")
    if '접수일자' in hist_df.columns:
        min_date = hist_df['접수일자'].dropna().min()
        max_date = hist_df['접수일자'].dropna().max()
        
        date_range = st.sidebar.date_input(
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
    st.sidebar.divider()
    
    if view_mode == '💼 고객사 배포용 (Client View)':
        st.title("💼 고객사 맞춤형 출고 리포트 (드릴다운 뷰)")
        
        # 1. 상점별 데이터 (화주 대신 상점 기준)
        st.markdown("## 1️⃣ 상점(店铺) 선택 및 데이터 요약")
        if '店铺' in hist_df.columns:
            shop_summary = hist_df.groupby('店铺').size().reset_index(name='주문건수')
            fig_shop_pie = px.pie(shop_summary, names='店铺', values='주문건수', hole=0.3, title="전체 상점별 물동량 점유율 (접수 기준)")
            st.plotly_chart(fig_shop_pie, use_container_width=True)
            
            shop_list = ["상점을 선택하세요 (전체 데이터 유지)"] + sorted(hist_df['店铺'].dropna().unique().tolist())
            selected_shop = st.selectbox("📌 상세 분석을 진행할 상점(店铺)을 선택해 주세요:", shop_list)
            
            if selected_shop != "상점을 선택하세요 (전체 데이터 유지)":
                shop_hist = hist_df[hist_df['店铺'] == selected_shop]
                shop_detail = detail_df[detail_df['店铺'] == selected_shop] if not detail_df.empty and '店铺' in detail_df.columns else pd.DataFrame()
                
                st.subheader(f"[{selected_shop}] 핵심 출고 지표")
                kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
                
                # --- KPI 산출 로직 (History 마스터 기준) ---
                # 1. 총 주문 접수 건수 (해당 상점의 전체 행 개수)
                total_orders = len(shop_hist)
                
                # 2. 주문 취소 건수 판단 (发货状态가 비어있거나, 发货时间이 '0000-00-00'인 경우)
                cancel_mask = pd.Series(False, index=shop_hist.index)
                if '发货状态' in shop_hist.columns:
                    # NaN이거나 공백인 경우
                    cancel_mask = shop_hist['发货状态'].isna() | (shop_hist['发货状态'].astype(str).str.strip() == '')
                
                if '发货时间' in shop_hist.columns:
                    # '0000-00-00' 문자열 포함 여부
                    bad_time_mask = shop_hist['发货时间'].astype(str).str.contains('0000-00-00', na=False)
                    cancel_mask = cancel_mask | bad_time_mask
                    
                canceled_count = int(cancel_mask.sum())
                
                # 3. 미출고(발송 대기) 판단 (취소가 아닌 유효 건 중 실제 发货时间이 비어있는 경우)
                pending_mask = pd.Series(False, index=shop_hist.index)
                if '发货时间' in shop_hist.columns:
                    valid_time_series = pd.to_datetime(shop_hist['发货时间'], errors='coerce')
                    pending_mask = valid_time_series.isna() & ~cancel_mask
                    
                pending_count = int(pending_mask.sum())
                
                # 4. 출고 완료 건수 및 주문번호 추출
                dispatched_mask = ~cancel_mask & ~pending_mask
                dispatched_count = int(dispatched_mask.sum())
                
                # 취소 및 미출고 건을 제외한 "실제 출고 완료된" 주문번호 리스트 추출
                if '出库单号' in shop_hist.columns:
                    valid_order_ids = shop_hist.loc[dispatched_mask, '出库单号'].unique()
                    valid_shop_detail = shop_detail[shop_detail['出库单号'].isin(valid_order_ids)] if not shop_detail.empty else shop_detail
                else:
                    valid_shop_detail = shop_detail
                
                # 5. 총 발송 수량 (출고 내역 파일의 货品数量 합계, 취소/미출고 제외)
                if '货品数量' in shop_hist.columns:
                    shop_hist_qty = pd.to_numeric(shop_hist.loc[dispatched_mask, '货品数量'], errors='coerce').fillna(0)
                    total_qty = shop_hist_qty.sum()
                else:
                    total_qty = 0
                
                kpi1.metric("총 접수 건수", f"{total_orders:,.0f} 건", "심사시간(审核时间) 기준")
                kpi2.metric("출고 완료 건수", f"{dispatched_count:,.0f} 건", "발송시간(发货时间) 기준")
                kpi3.metric("총 발송 수량", f"{total_qty:,.0f} 개", "출고 내역(History) 기준")
                kpi4.metric("주문 취소 건수", f"{canceled_count:,.0f} 건", delta="-", delta_color="off")
                kpi5.metric("미출고(발송 대기)", f"{pending_count:,.0f} 건", delta="지연/미출고", delta_color="inverse")
                
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
                        fig_day = px.line(trend_all, x='날짜', y=['접수건수', '출고건수(완료)'], markers=True)
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
                        fig_network.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_network, use_container_width=True)
                        st.divider()

                # 3. 브랜드별 출고 순위
                if not valid_shop_detail.empty and '品牌' in valid_shop_detail.columns:
                    st.markdown("## 3️⃣ 브랜드별 출고 순위 (출고 완료 기준)")
                    brand_summary = valid_shop_detail.groupby('品牌')['货品总数量'].sum().reset_index(name='총출고수량')
                    brand_summary = brand_summary.sort_values('총출고수량', ascending=False)
                    fig_brand = px.bar(brand_summary.head(15), x='品牌', y='총출고수량', color='총출고수량', color_continuous_scale='Magma', text_auto=True)
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
                        fig_brand_item.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_brand_item, use_container_width=True)
                        
                        # 표 형태로도 데이터 제공
                        st.dataframe(brand_item_summary.rename(columns={'상품표시명':'상품명', '货品总数量':'출고수량(개)'}), use_container_width=True)
                
            else:
                st.write("👆 **위 드롭다운 메뉴에서 상점을 선택하시면 세부 데이터(브랜드, 상품 등)가 나타납니다.**")

    else:
        st.title("👑 3PL 종합 운영 리포트 (Internal View)")
        st.info("개편 중: 고객사 배포용 뷰를 우선 확인해 주세요.")

else:
    st.warning("데이터 폴더에 파일이 없습니다. 안내에 따라 엑셀 파일을 넣어주세요.")
    st.info("💡 **데이터 폴더 구조 안내**\n"
            "1. `data_detailed` 폴더 안에 기존에 쓰시던 **상세 출고 내역** 파일들을 넣어주세요.\n"
            "2. `data_history` 폴더 안에 접수시간이 포함된 **일반 출고 내역** 파일들을 넣어주세요.")
