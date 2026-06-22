content = """@echo off
echo ========================================================
echo        3PL 대시보드 데이터 자동 업데이트 프로그램
echo ========================================================
echo.
echo 엑셀 파일을 깃허브(클라우드)로 전송을 시작합니다...
echo.

cd /d "%~dp0"

echo [1/3] 변경된 데이터를 확인하는 중...
git add data_inbound/ data_history/ data_detailed/

echo [2/3] 변경 사항을 저장하는 중...
git commit -m "Auto-update dashboard data" > nul 2>&1
if errorlevel 1 (
    echo (변경된 파일이 없거나 이미 최신 상태입니다.^)
) else (
    echo 성공적으로 저장되었습니다.
)

echo.
echo [3/3] 클라우드로 전송하는 중...
git push origin main

echo.
echo ========================================================
echo    전송이 완료되었습니다! (인터넷 화면은 약 10초 뒤 갱신됩니다)
echo ========================================================
echo.
pause
"""

with open('대시보드_데이터_업데이트.bat', 'w', encoding='cp949') as f:
    f.write(content)
