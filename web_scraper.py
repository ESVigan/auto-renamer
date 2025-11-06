import requests
import json

def fetch_data_from_web(curl_url, cookies_str):
    """
    使用提供的 cookie 从指定 URL 获取数据。
    """
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
        'cookie': cookies_str
    }

    try:
        response = requests.get(curl_url, headers=headers, timeout=15)
        response.raise_for_status()  # 如果请求失败则抛出异常
        
        # 尝试解析JSON，如果失败则返回文本
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None

if __name__ == '__main__':
    # 请将这里的 URL 替换为正确的 API 请求 URL
    # 这个 URL 通常可以在浏览器开发者工具的 Fetch/XHR 请求中找到
    API_URL = 'https://uaod.learnings.ai/' 

    # 从您提供的 cURL 命令中提取的 cookie
    # 注意：这个 cookie 有时效性，可能会过期
    COOKIES = '_tea_utm_cache_1229=undefined; _ga=GA1.1.1575084333.1760372327; learnings-passport=18MCxN55C-gvX2Tt3MxWNDOG8zq5kcFfxQLyWWPbdnAVwB7kJpOWa6VvMt4ETJ1o; learnings-user=Zaf_t42v7XVx6aI6K-od7Crnr0pKpVrJn5WP-l9sVVByy11bgJhE1CC9J4G8bQnNqZnX_rloaC27rejiDVTyXyL_DzJHQkORqeWQR2ty3IzJYlLQTipiESrdMv5gAN3LVpR7i-Dtefii1pKFQpFNtNkyzjDbdGOpZTaDFRggSUlkQJ-FjGos4ZySUyUMXENjTZbcDx9_Jqt0DYikWPMNMSDO7t7AgH7TCMm_t9GKv_GwJShhgiVX3TjG5jjTaOhiMQTVE0qZ1a-iFTpJ5twigh8gXPNbWz40qSCDuElmXUt0gZLxPUcYB0f9cqLlQESzSlEXNVZdO695G62Z2ylqRfNaVdTYNC2DMPKaqtgpgdxuHMWLGdFLCUmYxf4VBlpWKQXeRBhQQ8CpWsq06AUVXCeBSbz2tsGmqmc1SoA7fccJW8Z-k3vAVMDcfPlcajvFJCI4TWeq2RClgoabh_-tdlAlqQ4ydwVAE7ccEV9UQRwOuLCHkrblIRqp5iIJrBMI_iM5CmIq7EcXquiJMW1lDAQWNBdFijzr_QPkGJ0bBHl7mj6Jz4Tgpj8zwU3jxd1pCJbtvYzf-ZiErKqoEFQGYp0h3fsXNEDgKZ-xvJk1Rtm9o2FdMlqiP6TUT-LuduSuUnZnP0eTYNjCdz9cz9bokQ; learnings-passport=26LNGWH_36TNjO_UOY90sa2dXqvhCoxBhtd0GOKvkQAJkbilN1EOC3eVFf8kRPcC; learnings-user=5sVVGFyFA0AWlawkvFomVDbCGKZ7FH8POA1cRVtLLV6gpKwoaO4TXJUIbXIv7PEoV50v6D2vdM9XsBYFltZ3uUQ03LxfOQefT0QS9yi3tIIQ7mp9CyrEo02Z3pqcHlKrSWDmYqrJtDyY8l9nRBpay7naqRn1dpC8htf-dZKKxQogyAqOv_KHUkfvVfvZm-4AzszKaNxieKGGhx6OZ2Qc3oHjjpKQRgvuMdF5y0p71dhvthnwwoe6u7ex7hlYrfowx4UPw9RDQHCgvDb2PDmBynT60DC9JyJIZeThAH2PZB_7Vrkc2mnnzm3CR-jMYOEStm6EYERdwxRAro1YA1gJcp0oQ8iy2yqZdtt3fWSRy2z9aMFQ64TSwWsoELDFU6YnETHUbiDs7pE8BW2bA_ovVOKsjQ2yacKbJVYHzDjnz96XDa0p7d4zqutPqKDSL3Eb_vvfpokjKrMayev4SvqQIRD-SY3OaLpWb5hVPzwpT1qoUdd9BcGSeJ9-70B_p2-cHmEm1eDxohqd7oqqIzushff-x8uZOy7p8oWRcLKm1ga-JeFQ-wVKw0jhs9x2fiDENAHX5Mqrde8mbsM0-nN35H93C6z3NOiqXRd198czjDj2Nxr0arwsV3ApCOx9VqFcBugvgkXRDAP4O9xpEtsaeA; _ga_2Z4PFG28RG=GS2.1.s1760816568$o2$g1$t1760816862$j55$l0$h0'

    data = fetch_data_from_web(API_URL, COOKIES)

    if data:
        print("成功获取到数据，已保存到 response.html 文件中供分析。")
        with open('response.html', 'w', encoding='utf-8') as f:
            f.write(str(data))
