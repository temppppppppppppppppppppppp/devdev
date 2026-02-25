

import ctypes
from ctypes import wintypes
import time
import os
import glob
import shutil
import threading
import tkinter as tk
import pyautogui
import re
import zipfile  # [추가] ZIP 압축을 위한 모듈
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # [추가] 키 입력(Enter 등)을 위해 필요
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ==============================================================================
# [설정] 사용자 환경 및 메일 설정
# ==============================================================================

# 1. 파일 경로 설정
PDF_DIR = r"C:\Users\User\Desktop\gemini\3_pdf"
BASE_DIR = r"C:\Users\User\Desktop\gemini"
SAVE_DIR = os.path.join(BASE_DIR, "결과_저장소")
BACKUP_DIR = os.path.join(BASE_DIR, "백업")

# 2. 메일 발송 정보 설정 (사용자 입력 필요)
# [주의] 보내는 사람(ID/PW)과 받는 사람 이메일을 정확히 확인하세요.
MAIL_ID = "wjjo"
MAIL_PW = "63jd72961!A!"
MAIL_TO = "wjjo@kidaristudio.com"   # [수정 필요] mail_guni 변수 대체

# [설정] PDF 1개당 1화
EP_PER_PDF = 1

# ==============================================================================
# 1. 시스템 유틸리티 (IME, 로깅, 압축)
# ==============================================================================

# 폴더 자동 생성
for path in [SAVE_DIR, BACKUP_DIR]:
    if not os.path.exists(path):
        try: os.makedirs(path)
        except: pass

user32 = ctypes.WinDLL('user32', use_last_error=True)
imm32 = ctypes.WinDLL('imm32', use_last_error=True)
HIMC = wintypes.HANDLE
GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = wintypes.HWND
ImmGetContext = imm32.ImmGetContext
ImmGetContext.argtypes = [wintypes.HWND]
ImmGetContext.restype = HIMC
ImmGetOpenStatus = imm32.ImmGetOpenStatus
ImmGetOpenStatus.argtypes = [HIMC]
ImmGetOpenStatus.restype = wintypes.BOOL
ImmSetOpenStatus = imm32.ImmSetOpenStatus
ImmSetOpenStatus.argtypes = [HIMC, wintypes.BOOL]
ImmSetOpenStatus.restype = wintypes.BOOL

def force_english_ime():
    hwnd = GetForegroundWindow()
    if not hwnd: return
    himc = ImmGetContext(hwnd)
    if not himc: return
    if ImmGetOpenStatus(himc):
        ImmSetOpenStatus(himc, False)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def start_keep_awake_thread():
    def keep_awake():
        while True:
            pyautogui.press("numlock")
            time.sleep(60)
    t = threading.Thread(target=keep_awake, daemon=True)
    t.start()

def scroll_to_bottom():
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
    except: pass

def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag_name in ['source-footnote', 'sources-carousel-inline', 'source-inline-chips', 'mat-icon', 'share-button', 'more-button']:
        for t in soup.select(tag_name):
            t.decompose()
    text = soup.get_text("\n\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)

def compress_results_to_zip():
    """
    SAVE_DIR에 있는 모든 txt 파일을 zip으로 압축합니다.
    """
    log("📦 결과 파일 압축 시작...")
    
    # 오늘 날짜로 zip 파일명 생성 (예: 20251205_Gemini결과.zip)
    today_str = datetime.now().strftime("%Y%m%d")
    zip_filename = f"{today_str}_Gemini결과.zip"
    zip_path = os.path.join(BASE_DIR, zip_filename) # 바탕화면/gemini 폴더 바로 아래에 생성

    try:
        txt_files = glob.glob(os.path.join(SAVE_DIR, "*.txt"))
        if not txt_files:
            log("⚠ 압축할 txt 파일이 없습니다.")
            return None

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as myzip:
            for txt_file in txt_files:
                # zip 안에는 파일명만 들어가도록 arcname 설정
                myzip.write(txt_file, arcname=os.path.basename(txt_file))
        
        log(f"✅ 압축 완료: {zip_path}")
        return zip_path
    except Exception as e:
        log(f"❌ 압축 실패: {e}")
        return None

# ==============================================================================
# 2. 프롬프트 생성
# ==============================================================================

def make_prompt_text(ep_num):
    return f"""
다음은 <축구 천재가 돌아왔다> **제 {ep_num}화**의 회차별 줄거리가 담긴 파일이야.

★★★ [매우 중요] ★★★
Canvas나 문서 편집기를 열지 마. 
채팅창에 텍스트로 바로 출력해.

**[작업 목표]**
업로드된 파일의 회차 줄거리에 맞게 문피아 20~30대 독자들의 입맛에 맞을 웹소설의 원고를 집필해줘.
분량은 공백 포함 최소 7000자 이상이 되도록 원고를 써줘. 

**[필수 제약 사항]**
1. **화수 표기:** 반드시 맨 윗줄에 **'제 {ep_num}화'**라고 적고 시작해.
2. **출력:** 사족(인사말, 설명) 없이 **소설 본문만** 출력해.
3. **형식 제한:** 불필요한 html 요소나 진한 글자(**) 사용 금지.
4. **마무리:** 각 화 마지막에는 끝났다는 표시로 '* * *'를 넣어 줘.
5. **시점:** 3인칭을 사용해 줘.
6. **내용** 줄거리에 없는 내용은 만들지 말고, 부족하면 호흡을 늘려줘.


★★★ [매우 중요] ★★★
Canvas나 문서 편집기를 열지 마. 
채팅창에 텍스트로 바로 출력해.

"""

# ==============================================================================
# 3. Gemini 자동화 (Selenium)
# ==============================================================================

# Gemini용 드라이버 설정 (디버깅 포트 사용)
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
except:
    print("크롬 디버깅 모드가 실행되지 않았습니다!")
    raise

wait = WebDriverWait(driver, 10)

def upload_pdf(pdf_path):
    log(f"📄 PDF 업로드 시작: {os.path.basename(pdf_path)}")
    
    def type_path_thread():
        time.sleep(4) 
        pyautogui.hotkey('alt', 'n')
        time.sleep(0.5)
        force_english_ime()
        pyautogui.write(pdf_path, interval=0.01) 
        time.sleep(0.5) 
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('enter')

    try:
        t = threading.Thread(target=type_path_thread)
        t.start()
        
        menu_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='파일 업로드 메뉴']")))
        menu_btn.click()
        time.sleep(1)
        
        upload_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'menu-text') and contains(text(), '파일 업로드')]")))
        upload_option.click()
        
        t.join()
        
        full_filename = os.path.basename(pdf_path)
        base_filename = os.path.splitext(full_filename)[0] 
        log(f"✅ 파일 경로 입력 완료. 업로드 대기. (검색 파일명: '{base_filename}')")
        
        file_name_div_locator = (By.XPATH, f"//div[@data-test-id='file-name' and contains(text(), ' {base_filename} ')]")
        wait.until(EC.presence_of_element_located(file_name_div_locator))

        log("✅ 업로드 완료 (data-test-id 확인)")
        time.sleep(2) 
        
    except Exception as e:
        log(f"⚠ 업로드 에러: {e}")
        raise

def send_text_to_input(text):
    try:
        input_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
        )
        driver.execute_script("arguments[0].focus();", input_box)
        time.sleep(0.2)
        driver.execute_script(
            """
            arguments[0].innerText = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """,
            input_box, text
        )
        time.sleep(0.5)
        input_box.send_keys(" ")
        input_box.send_keys(u'\ue003') # Backspace
    except Exception as e:
        log(f"⚠ 입력창 에러: {e}")

def click_send_button():
    try:
        send_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[aria-label*='전송'], button[aria-label*='Send'], button[aria-label*='보내기']")
        ))
        send_btn.click()
        log("🚀 전송 버튼 클릭")
        time.sleep(2)
    except:
        log("⚠ 엔터키 강제 전송 시도")
        try:
            driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']").send_keys(u'\ue007')
        except: pass

def wait_for_ai_completion():
    log("⏳ AI 응답 생성 대기...")
    scroll_to_bottom()
    try:
        WebDriverWait(driver, 1200).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label*='중지'], button[aria-label*='Stop']"))
        )
        log("✅ 생성 완료")
    except TimeoutException:
        log("⚠ 생성 시간 초과 (타임아웃)")
    time.sleep(2)
    scroll_to_bottom()

def save_result(pdf_filename):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".model-response, .message-content, .markdown")
        if not elements: return None
        
        last_msg = elements[-1]
        text = extract_text(last_msg.get_attribute("innerHTML"))

        if len(text) < 100: 
            try: text = extract_text(last_msg.find_element(By.XPATH, "./..").get_attribute("innerHTML"))
            except: pass

        txt_name = os.path.splitext(pdf_filename)[0] + ".txt"
        file_path = os.path.join(SAVE_DIR, txt_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        log(f"💾 저장 완료: {txt_name} ({len(text)}자)")
        return file_path
    except Exception as e:
        log(f"⚠ 저장 실패: {e}")
        return None

# ==============================================================================
# 4. 메일 발송 로직 (새로운 Selenium 인스턴스 사용)
# ==============================================================================

def send_result_email(zip_filepath):
    """
    키다리스튜디오 포털에 로그인하여 zip 파일을 메일로 전송합니다.
    Gemini 작업용 드라이버와 섞이지 않도록 새로운 드라이버를 생성하여 처리합니다.
    """
    if not zip_filepath or not os.path.exists(zip_filepath):
        log("❌ 메일 발송 실패: 첨부할 ZIP 파일이 없습니다.")
        return

    log("📧 메일 발송 프로세스 시작...")

    # 메일 발송용 독립적인 드라이버 설정
    mail_options = webdriver.ChromeOptions()
    mail_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    # 창 위치와 크기 설정 (화면 밖으로 나가지 않게 조정)
    mail_options.add_argument("--window-size=1200,900") 
    
    mail_driver = webdriver.Chrome(options=mail_options)
    mail_driver.implicitly_wait(15) # 대기 시간 넉넉하게
    
    try:
        # 1. 로그인 페이지 접속
        log("🔑 포털 로그인 시도...")
        mail_driver.get("https://portal.kidaristudio.com/login?returnUrl=%2Fapp%2Fmail")
        
        # ID / PW 입력
        mail_driver.find_element(By.XPATH, '//*[@id="username"]').send_keys(MAIL_ID)
        mail_driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(MAIL_PW, Keys.ENTER)
        
        time.sleep(3) # 로그인 처리 및 리다이렉트 대기

        # 2. 메일 쓰기 프레임 진입
        # 포털 구조상 메일 뷰어가 iframe일 수 있으므로 전환
        try:
            mail_driver.switch_to.frame("mail-viewer")
        except:
            log("ℹ 'mail-viewer' 프레임을 찾을 수 없어 메인 컨텐츠에서 진행합니다.")

        # 메일 쓰기 버튼 클릭
        log("📝 메일 작성 시작...")
        write_btn = mail_driver.find_element(By.XPATH, '//*[@id="mailLeftMenuWrap"]/section[2]/a')
        write_btn.click()
        time.sleep(2)

        # 3. 수신자 및 제목 입력
        put_adress = mail_driver.find_element(By.XPATH, '//*[@id="to"]')
        put_cc = mail_driver.find_element(By.XPATH, '//*[@id="cc"]')
        put_title = mail_driver.find_element(By.XPATH, '//*[@id="subject"]')

        put_title.send_keys(f"[완료] Gemini 리라이팅 작업 결과 ({datetime.now().strftime('%Y-%m-%d')})")
        time.sleep(0.5)
        
        # 수신자 입력 (엔터로 확정)
        put_adress.send_keys(MAIL_TO, Keys.ENTER)
        time.sleep(0.5)
        
        # 참조자 입력
        time.sleep(1)

        # 4. 파일 첨부
        log(f"📎 파일 첨부 중: {os.path.basename(zip_filepath)}")
        file_input = mail_driver.find_element(By.XPATH, '//*[@id="mailSimpleUpload"]')
        file_input.send_keys(zip_filepath)
        
        time.sleep(5) # 업로드 대기 (파일 크기에 따라 조절 필요)

        # 5. 전송 버튼 클릭
        # 혹시 프레임이 풀렸을 수 있으니 다시 확인 (필요시)
        try:
            mail_driver.switch_to.default_content() # 일단 밖으로 나갔다가
            mail_driver.switch_to.frame("mail-viewer") # 다시 진입
        except: pass
        
        log("🚀 메일 전송 버튼 클릭")
        send_btn_toolbar = mail_driver.find_element(By.XPATH, '//*[@id="write_toolbar_wrap"]/div[1]/a[1]/span[1]')
        send_btn_toolbar.click()
        time.sleep(1)
        
        # 팝업 확인창 ('보내기' 확인)
        confirm_btn = mail_driver.find_element(By.XPATH, '//*[@id="gpopupLayer"]/footer/a[1]')
        confirm_btn.click()
        
        log("✅ 메일 전송 명령 완료. (완료 대기 중)")
        time.sleep(5) # 전송 완료 대기

    except Exception as e:
        log(f"❌ 메일 발송 중 오류 발생: {e}")
    finally:
        log("🔒 메일 드라이버 종료")
        mail_driver.quit()


# ==============================================================================
# 5. 메인 실행 로직
# ==============================================================================

def main():
    start_keep_awake_thread()
    
    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    
    if not pdf_files:
        print(f"❌ 오류: {PDF_DIR} 폴더에 PDF 파일이 없습니다.")
        return

    print(f"📂 총 {len(pdf_files)}개의 PDF 파일을 발견했습니다.")
    
    root = tk.Tk()
    root.title("Gemini 1화 1파일 모드")
    root.geometry("400x200")
    root.attributes('-topmost', True)
    tk.Label(root, text="[1화 1파일 모드]\nPDF 작업 완료 후\n자동으로 압축하여 메일을 발송합니다.", font=("맑은 고딕", 11)).pack(pady=20)
    tk.Button(root, text="작업 시작", command=root.destroy, bg="red", fg="white", width=20).pack()
    root.mainloop()

    # --- Gemini 작업 루프 ---
    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        
        try:
            ep_num = int(re.search(r'\d+', pdf_name).group())
        except:
            log(f"⚠ 파일명에서 숫자를 찾을 수 없음: {pdf_name}, 건너뜀")
            continue

        result_txt_path = os.path.join(SAVE_DIR, os.path.splitext(pdf_name)[0] + ".txt")
        if os.path.exists(result_txt_path):
            log(f"⏩ [SKIP] 제 {ep_num}화는 이미 완료됨.")
            continue

        log(f"==========================================")
        log(f"▶ 작업 시작: 제 {ep_num}화 ({pdf_name})")
        
        start_time = time.time()
        upload_pdf(pdf_path)
        prompt = make_prompt_text(ep_num)
        send_text_to_input(prompt)
        click_send_button()
        wait_for_ai_completion()
        saved_path = save_result(pdf_name)
        
        if saved_path and os.path.exists(saved_path):
            try: shutil.copy(saved_path, BACKUP_DIR)
            except: pass

        elapsed = time.time() - start_time
        log(f"⏱ 소요 시간: {int(elapsed)}초")

        # 세션 초기화 로직 (10회마다)
        if ep_num % 10 == 0:
            log(f"♻ {ep_num}화 도달 (10회차): 세션 초기화...")
            try:
                driver.get("https://gemini.google.com/app")
            except Exception as e:
                driver.refresh()
            time.sleep(5) 
        else:
            time.sleep(2) 

    # --- 모든 Gemini 작업 종료 후 ---
    log("==========================================")
    log("🎉 모든 PDF 변환 작업 완료!")
    
    # 1. 압축
    zip_path = compress_results_to_zip()
    
    # 2. 메일 발송
    if zip_path:
        send_result_email(zip_path)
    else:
        log("❌ 압축 파일이 없어 메일을 발송하지 못했습니다.")

if __name__ == "__main__":
    main()