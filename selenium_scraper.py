import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def fetch_html_after_manual_login(url):
    """
    启动浏览器让用户手动登录，然后获取页面 HTML。
    """
    driver = None
    try:
        # 自动管理 ChromeDriver
        service = ChromeService(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # 保持浏览器窗口打开，而不是在后台运行
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        
        print("\n" + "="*50)
        print("浏览器窗口已打开，请在浏览器中扫描二维码完成登录。")
        print("脚本将在此期间暂停，登录成功后会自动继续...")
        print("="*50 + "\n")
        
        # 等待用户登录，通过判断 URL 是否不再包含 'login' 来确认
        # 设置最长等待时间为 5 分钟 (300秒)
        WebDriverWait(driver, 300).until(
            EC.url_contains("#/") 
        )
        
        print("检测到登录成功！")
        
        # 登录后，再等待几秒钟，确保页面上的动态数据加载完成
        print("正在等待页面数据加载...")
        time.sleep(5)
        
        # 获取页面源码
        page_source = driver.page_source
        print("成功获取页面源码。")
        
        return page_source

    except Exception as e:
        print(f"操作时出错: {e}")
        if "TimeoutException" in str(e):
            print("错误：等待登录超时（超过5分钟），请重新运行脚本。")
        return None
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")


if __name__ == '__main__':
    TARGET_URL = 'https://work.learnings.ai/'

    html_content = fetch_html_after_manual_login(TARGET_URL)

    if html_content and "<html>" in html_content:
        with open('response.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("页面源码已成功保存到 response.html。")
    else:
        print("获取页面源码失败，可能是因为登录未成功或页面内容为空。")
