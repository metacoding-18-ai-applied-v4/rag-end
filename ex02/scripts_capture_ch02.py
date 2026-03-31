import os
import sys
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    assets_dir = Path("../../assets/CH02")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Start Server
    print("Starting Docker & FastAPI server...")
    subprocess.run(["docker", "compose", "up", "-d"])
    
    server_proc = subprocess.Popen([sys.executable, "run.py"])
    time.sleep(3) # Wait for server to start
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            
            # 2. Capture Swagger UI
            print("Capturing Swagger UI...")
            page.goto("http://localhost:8000/docs", wait_until="networkidle")
            time.sleep(1)
            # expand the GET /api/employees so it looks better
            
            page.screenshot(path=str(assets_dir / "02_swagger-ui.png"), full_page=True)
            
            # 3. Capture API Test
            print("Capturing API Test...")
            # Click POST /api/employees
            page.click("#operations-API-api_create_employee_api_employees_post")
            time.sleep(0.5)
            
            # Click Try it out
            page.click("button.try-out__btn")
            time.sleep(0.5)
            
            # We don't need to type the JSON since Swagger gives default, just evaluate and clear and type
            textarea = page.locator("textarea.body-param__text")
            textarea.fill('{\n  "emp_no": "EMP999",\n  "name": "테스터",\n  "dept": "개발팀",\n  "position": "사원",\n  "hire_date": "2026-03-05"\n}')
            time.sleep(0.5)
            
            # Click Execute
            page.click("button.execute")
            time.sleep(2) # wait for response
            
            # Scroll down a bit to show response
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
            
            page.screenshot(path=str(assets_dir / "02_api-test-employee.png"))
            
            # 4. Capture Admin Dashboard
            print("Capturing Admin Dashboard...")
            page.goto("http://localhost:8000/admin/dashboard", wait_until="networkidle")
            time.sleep(1)
            page.screenshot(path=str(assets_dir / "02_admin-dashboard.png"), full_page=True)
            
            # 5. Capture Admin Employee Create
            print("Capturing Admin Employee Create...")
            page.goto("http://localhost:8000/admin/employees", wait_until="networkidle")
            time.sleep(1)
            
            # Fill the form
            page.fill("input[name='emp_no']", "EMP998")
            page.fill("input[name='name']", "웹테스터")
            page.fill("input[name='dept']", "운영팀")
            page.fill("input[name='position']", "대리")
            page.fill("input[name='hire_date']", "2026-03-05")
            time.sleep(0.5)
            
            # Submit form
            page.click("button[type='submit']")
            time.sleep(1) # wait for reload
            
            # Form should be filled again in the screenshot as requested by user? "상단 등록 폼에 사번/이름/부서/직급/입사일을 입력한 상태 + 하단 직원 목록 테이블에 방금 등록한 직원이 표시된 화면"
            # Since submitting the form reloads the page (or clears it), let's fill it again to match the requirement "입력한 상태 + 목록 결과"
            page.fill("input[name='emp_no']", "EMP001") # Just some dummy data to show it's filled
            page.fill("input[name='name']", "김신입")
            page.fill("input[name='dept']", "인사팀")
            page.fill("input[name='position']", "사원")
            page.fill("input[name='hire_date']", "2026-03-06")
            time.sleep(0.5)
            
            page.screenshot(path=str(assets_dir / "02_admin-employee-create.png"), full_page=True)
            
            print("Capture complete.")
            browser.close()
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=5)
        subprocess.run(["docker", "compose", "down"])

if __name__ == "__main__":
    main()
