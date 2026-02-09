# 🚗 드라이버 지출 관리 앱

이 프로젝트는 기사님(존, 조셉)의 지출 내역을 관리하고 구글 스프레드시트에 저장하는 웹 애플리케이션입니다.

## 🚀 Streamlit Cloud 배포 방법

이 앱을 언제 어디서나 접속하려면 **Streamlit Cloud**에 배포해야 합니다.

### 1단계: GitHub에 파일 올리기
1. GitHub에 로그인하고 **New Repository**를 눌러 새 저장소를 만듭니다. (Public 또는 Private 상관없음)
2. 아래 파일들을 드래그해서 업로드합니다:
   - `app.py` (메인 코드)
   - `requirements.txt` (필수 라이브러리 목록)
   - `README.md` (이 설명 파일)
   - **주의**: `token.json`이나 `client_secret.json` 파일은 올리지 마세요! (보안 위험)

### 2단계: Streamlit Cloud 연결
1. [Streamlit Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다.
2. **New app** 버튼을 누릅니다.
3. 방금 만든 GitHub 저장소, 브랜치(main), 파일 경로(`app.py`)를 선택합니다.
4. **Deploy!** 버튼을 누르기 전에 **Advanced settings**를 엽니다.

### 3단계: 비밀번호(Secrets) 설정
**Advanced settings** -> **Secrets** 입력창에 제가 채팅 창에 따로 보내드린 비밀번호 내용을 복사해서 붙여넣으세요.

(보안을 위해 이곳에는 비밀번호를 적지 않았습니다.)

5. **Save**를 누르고 **Deploy!**를 클릭합니다.
6. 잠시 기다리면 배포가 완료되고, 인터넷 주소가 생성됩니다!
