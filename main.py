from time import sleep
from selenium import webdriver

browser = webdriver.Chrome(executable_path=r'C:\Users\Patryk\Downloads\chromedriver_win32(1)\chromedriver.exe')
browser.get('https://justjoin.it/warszawa/python/junior?tab=with-salary')
sleep(3)
browser.execute_script("document.body.style.zoom='50%'")
resp = browser.page_source
divided_by_pln = resp.split(' PLN')
list_of_salaries = []
sum_of_salaries = 0
counter_of_salaries = 0
for element in divided_by_pln:
    if element[-1]=='k':
        salary = element[-16:].split(">", 1)[1]
        salary2 = salary.replace("k", "")
        salary = salary2.replace(" ", "")
        salary2 = salary.replace("-", " ")
        salary = salary2.split(" ")
        sum_of_actual_salaries = 0
        for i in range(0, len(salary)):
            sum_of_actual_salaries = sum_of_actual_salaries + float(salary[i])
        mean_of_actual_salaries = sum_of_actual_salaries/len(salary)
        sum_of_salaries = sum_of_salaries + mean_of_actual_salaries
        counter_of_salaries = counter_of_salaries + 1
print(sum_of_salaries/counter_of_salaries)