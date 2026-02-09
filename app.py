import streamlit as st
import pandas as pd
import datetime
import os.path
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- 1. 페이지 설정 및 디자인(CSS) ---
st.set_page_config(page_title="드라이버 지출 관리", layout="centered")
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; background-color: #f0f2f6; }
    
    /* 헤더 스타일 */
    .header-container {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); /* 운전/차량 느낌의 딥 블루 */
        padding: 24px; border-radius: 16px; color: white; text-align: center; margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .header-title { font-size: 26px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .header-subtitle { font-size: 15px; opacity: 0.85; margin-top: 6px; font-weight: 400; }

    /* 카드 스타일 */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background-color: white; padding: 24px; border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 16px; border: 1px solid #eef0f3;
    }
    
    /* 버튼 스타일 */
    div.stButton > button {
        width: 100%; border-radius: 12px; height: 56px; font-weight: 700; font-size: 16px;
        border: none; background-color: #1e3c72; color: white;
        box-shadow: 0 4px 10px rgba(30, 60, 114, 0.3); transition: all 0.2s ease;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(30, 60, 114, 0.4); }
    div.stButton > button[kind="secondary"] {
        background-color: #f8f9fa; color: #495057; box-shadow: none; border: 1px solid #dee2e6; height: 42px; font-size: 14px;
    }
    div.stButton > button[kind="secondary"]:hover { background-color: #e9ecef; }
    
    /* 탭 및 메트릭 */
    button[data-baseweb="tab"] { font-size: 16px; font-weight: 700; border-radius: 8px; }
    div[data-testid="stMetricValue"] { color: #1e3c72; font-weight: 800; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #666; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 스프레드시트 연결 설정 ---
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ZnYUAyHhPIJMSlVQ369sj6ybInwPnFmeuNnp3a-V6G4/edit?gid=0#gid=0'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# 구글 연결 함수
# 구글 연결 함수 (캐시 제거: 토큰 만료 문제 방지)
def get_worksheet():
    creds = None
    
    # 1. Streamlit Cloud Secrets 확인 (배포 환경)
    try:
        from streamlit.runtime.secrets import Secrets
        # secrets가 존재하는지 안전하게 확인
        if "google_oauth" in st.secrets:
            try:
                token_info = st.secrets["google_oauth"]
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except Exception as e:
                pass # Secrets 형식이 안 맞으면 로컬 파일 시도
    except (FileNotFoundError, Exception):
        # 로컬 환경(secrets.toml 없음)이면 무시하고 로컬 파일 확인으로 넘어감
        pass

    # 2. 로컬 파일 확인 (개발 환경)
    if not creds and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # 3. 인증 정보가 없거나 만료된 경우 (로컬 재인증 로직)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 로컬에서만 실행 (Cloud에서는 실행 불가)
            if not os.path.exists('client_secret.json'):
                # Cloud 환경에서 client_secret도 없고 secrets도 없으면 에러
                return None 
            
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 로컬일 때만 토큰 저장
        if os.path.exists('client_secret.json'): 
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    gc = gspread.authorize(creds)
    sh = gc.open_by_url(SHEET_URL)
    return sh.get_worksheet(0)

# --- 데이터 로드 함수 ---
def load_data():
    try:
        ws = get_worksheet()
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=['날짜', '기사님', '카테고리', '금액', '내역'])
        
        df = pd.DataFrame(data)
        # 금액 전처리
        if '금액' in df.columns:
            df['금액'] = df['금액'].astype(str).str.replace(',', '').replace('', '0').astype(float)
            
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    except Exception as e:
        # 에러 발생 시 알림 표시 (디버깅용)
        st.error(f"데이터 로드 에러: {e}") 
        return pd.DataFrame(columns=['날짜', '기사님', '카테고리', '금액', '내역'])

# --- 데이터 저장 함수 ---
def save_data(df):
    ws = get_worksheet()
    save_df = df.copy()
    save_df['날짜'] = save_df['날짜'].astype(str)
    
    ws.clear()
    ws.update([save_df.columns.values.tolist()] + save_df.values.tolist())

# --- [기능] 저장 콜백 함수 ---
def save_expense_callback():
    date = st.session_state.input_date
    driver = st.session_state.input_driver
    category = st.session_state.input_category
    amount = st.session_state.input_amount
    desc = st.session_state.input_desc

    if amount is None or amount == 0:
        st.session_state['msg_error'] = "금액을 입력해주세요!"
        return

    df = load_data()
    new_data = pd.DataFrame({
        '날짜': [date], '기사님': [driver], '카테고리': [category],
        '금액': [amount], '내역': [desc] 
    })
    
    final_df = pd.concat([new_data, df], ignore_index=True)
    save_data(final_df)

    st.session_state.input_amount = None
    st.session_state.input_desc = ""
    st.session_state['msg_success'] = True
    st.session_state['msg_error'] = None

# --- 메인 앱 ---
    # --- 메인 앱 ---
def main():
    st.markdown("""
        <div class="header-container">
            <p class="header-title">Driver Expenses</p>
            <p class="header-subtitle">기사님 비용 관리 (존 & 조셉)</p>
        </div>
    """, unsafe_allow_html=True)

    df = load_data()
    if not df.empty:
        df = df.sort_values(by='날짜', ascending=False)
    today = datetime.date.today()

    # --- 탭 구성 (최상단 이동) ---
    tab_input, tab_month, tab_range, tab_stat = st.tabs(["📝 지출 입력", "📆 월별 조회", "🗓 기간 조회", "📊 통계"])

    # [탭 1] 지출 입력 및 최근 내역
    with tab_input:
        st.markdown("### 📝 지출 입력")
        with st.container(border=True):
            if st.session_state.get('msg_success'):
                st.success("✅ 등록되었습니다!")
                st.session_state['msg_success'] = False
            if st.session_state.get('msg_error'):
                st.error(st.session_state['msg_error'])
                st.session_state['msg_error'] = None
            
            # 삭제 메시지 표시 기능 추가
            if st.session_state.get('msg_delete'):
                st.success("🗑 삭제되었습니다!")
                st.session_state['msg_delete'] = False

            if 'input_amount' not in st.session_state: st.session_state['input_amount'] = None
            if 'input_desc' not in st.session_state: st.session_state['input_desc'] = ""
            if 'input_date' not in st.session_state: st.session_state['input_date'] = today

            col1, col2 = st.columns(2)
            col1.date_input("날짜", key='input_date')
            col2.selectbox("기사님", ["존", "조셉"], key='input_driver')
            
            col3, col4 = st.columns(2)
            col3.selectbox("항목", ["급여", "식비", "보너스", "기타"], key='input_category')
            col4.number_input("금액 (₱)", min_value=0, step=100, key='input_amount')
            
            st.text_input("상세 내역 (선택)", placeholder="예: 2월 급여, 점심값", key='input_desc')
            
            st.write("")
            st.button("저장하기", on_click=save_expense_callback, type="primary")

        st.write("---")
        st.markdown("### 📋 최근 내역")
        
        if not df.empty:
            st.caption("최근 등록된 순서대로 보여집니다.")
            # 필터링
            col_filter1, col_filter2 = st.columns(2)
            filter_driver = col_filter1.multiselect("기사님 필터 (비워두면 전체)", df['기사님'].unique(), key="filter_driver_recent")
            
            if filter_driver:
                show_df = df[df['기사님'].isin(filter_driver)].copy()
            else:
                show_df = df.copy()
            
            st.markdown(f"**총 {len(show_df)}건**")
            
            show_df['금액'] = show_df['금액'].apply(lambda x: f"{x:,.0f}")
            if 'select_all' not in st.session_state: st.session_state.select_all = False
            show_df.insert(0, "선택", st.session_state.select_all)
            
            edited_df = st.data_editor(
                show_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "선택": st.column_config.CheckboxColumn("", width="small"),
                    "날짜": st.column_config.DateColumn("날짜", width="small", format="MM-DD"),
                    "기사님": st.column_config.TextColumn("기사님", width="small"),
                    "금액": st.column_config.TextColumn("금액 (₱)", width="small"),
                },
                disabled=["날짜", "기사님", "카테고리", "금액", "내역"],
                key="editor_list"
            )

            if st.button("🗑 선택 항목 삭제", type="secondary", key="btn_del_recent"):
                indices_to_delete = sorted(show_df[edited_df['선택']].index, reverse=True)
                if indices_to_delete:
                    new_df = df.drop(indices_to_delete)
                    save_data(new_df)
                    st.session_state['msg_delete'] = True
                    st.rerun()
        else:
            st.info("아직 등록된 지출 내역이 없습니다.")

    # [탭 2] 월별 조회
    with tab_month:
        if not df.empty:
            st.markdown("### 📆 월별 지출 조회")
            df['연-월'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m')
            month_list = sorted(df['연-월'].unique(), reverse=True)
            
            if month_list:
                col_m1, col_m2 = st.columns([1, 2])
                selected_month = col_m1.selectbox("조회할 월 선택", month_list, key="sel_month")
                
                month_df = df[df['연-월'] == selected_month].copy()
                
                # 기사님 필터 (계산 전 먼저 적용)
                filter_driver_month = st.multiselect("기사님 필터 (비워두면 전체)", month_df['기사님'].unique(), key="filter_driver_month")
                
                if filter_driver_month:
                    month_df_filtered = month_df[month_df['기사님'].isin(filter_driver_month)]
                else:
                    month_df_filtered = month_df.copy()

                # 합계 계산 (필터 된 데이터 기준)
                total_month_query = month_df_filtered['금액'].sum()
                col_m2.metric(f"{selected_month} 총 지출", f"₱ {total_month_query:,.0f}")

                # 데이터 에디터로 변경 (삭제 기능 추가)
                if 'select_all_month' not in st.session_state: st.session_state.select_all_month = False
                month_df_filtered.insert(0, "선택", st.session_state.select_all_month)

                edited_month_df = st.data_editor(
                    month_df_filtered,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "선택": st.column_config.CheckboxColumn("", width="small"),
                        "날짜": st.column_config.DateColumn("날짜", width="small", format="MM-DD"),
                        "기사님": st.column_config.TextColumn("기사님", width="small"),
                        "금액": st.column_config.TextColumn("금액 (₱)", width="small"),
                        "연-월": None,
                    },
                    disabled=["날짜", "기사님", "카테고리", "금액", "내역", "연-월"],
                    key="editor_month"
                )
                
                if st.button("🗑 선택 항목 삭제", type="secondary", key="btn_del_month"):
                    indices_to_delete = sorted(edited_month_df[edited_month_df['선택']].index, reverse=True)
                    if indices_to_delete:
                        new_df = df.drop(indices_to_delete)
                        save_data(new_df)
                        st.session_state['msg_delete'] = True
                        st.rerun()
            else:
                st.info("데이터가 없습니다.")
        else:
            st.info("데이터가 없습니다.")

    # [탭 3] 기간 조회
    with tab_range:
        if not df.empty:
            st.markdown("### 🗓 기간별 지출 조회")
            col_r1, col_r2 = st.columns([2, 1])
            date_range = col_r1.date_input(
                "기간 선택", 
                (today - datetime.timedelta(days=7), today),
                key="date_range_picker"
            )
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                # 날짜 비교를 위해 date 타입 통일
                mask = (pd.to_datetime(df['날짜']).dt.date >= start_date) & (pd.to_datetime(df['날짜']).dt.date <= end_date)
                range_df = df.loc[mask].copy()
                
                # 기사님 필터 (계산 전 먼저 적용)
                filter_driver_range = st.multiselect("기사님 필터 (비워두면 전체)", range_df['기사님'].unique(), key="filter_driver_range")
                
                if filter_driver_range:
                    range_df_filtered = range_df[range_df['기사님'].isin(filter_driver_range)]
                else:
                    range_df_filtered = range_df.copy()

                # 합계 계산 (필터 된 데이터 기준)
                total_range = range_df_filtered['금액'].sum()
                col_r2.metric("기간 총 지출", f"₱ {total_range:,.0f}")

                # 데이터 에디터로 변경 (삭제 기능 추가)
                if 'select_all_range' not in st.session_state: st.session_state.select_all_range = False
                range_df_filtered.insert(0, "선택", st.session_state.select_all_range)

                edited_range_df = st.data_editor(
                    range_df_filtered,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "선택": st.column_config.CheckboxColumn("", width="small"),
                        "날짜": st.column_config.DateColumn("날짜", width="small", format="MM-DD"),
                        "기사님": st.column_config.TextColumn("기사님", width="small"),
                        "금액": st.column_config.TextColumn("금액 (₱)", width="small"),
                    },
                    disabled=["날짜", "기사님", "카테고리", "금액", "내역"],
                    key="editor_range"
                )
                
                if st.button("🗑 선택 항목 삭제", type="secondary", key="btn_del_range"):
                    indices_to_delete = sorted(edited_range_df[edited_range_df['선택']].index, reverse=True)
                    if indices_to_delete:
                        new_df = df.drop(indices_to_delete)
                        save_data(new_df)
                        st.session_state['msg_delete'] = True
                        st.rerun()
            else:
                st.info("시작일과 종료일을 모두 선택해주세요.")
        else:
            st.info("데이터가 없습니다.")

    # [탭 4] 통계
    with tab_stat:
        if not df.empty:
            st.markdown("### 💰 이번 달 지출 요약")
            this_month = today.strftime('%Y-%m')
            # '연-월' 컬럼이 없을 수 있으므로 다시 생성 (탭 간 데이터 공유 문제 안전장치)
            df['연-월'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m')
            month_df_stat = df[df['연-월'] == this_month]
            
            total_month_stat = month_df_stat['금액'].sum()
            st.metric(f"{this_month} 총 지출", f"₱ {total_month_stat:,.0f}")
            
            st.markdown("### 👨‍✈️ 기사님별 지출 (전체 기간)")
            driver_group = df.groupby('기사님')['금액'].sum().sort_values(ascending=False)
            st.bar_chart(driver_group)
            
            # 상세 테이블
            st.dataframe(
                driver_group.apply(lambda x: f"₱ {x:,.0f}"), 
                use_container_width=True
            )
            
            st.markdown("### 📊 카테고리별 지출 비중 (전체 기간)")
            category_group = df.groupby('카테고리')['금액'].sum()
            st.bar_chart(category_group)
        else:
            st.info("데이터가 충분하지 않습니다.")

if __name__ == "__main__":
    main()
