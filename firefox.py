from selenium import webdriver
from selenium.webdriver.firefox.service import Service

# 设置 GeckoDriver 路径
service = Service('/usr/local/bin/geckodriver')
driver = webdriver.Firefox(service=service)

# 打开网页
driver.get('https://www.csu.edu.cn')

# 关闭浏览器
driver.quit()