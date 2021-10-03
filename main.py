from time import sleep
from selenium import webdriver


def scrap_justjoinit(link):
    browser = webdriver.Chrome()
    browser.get(link)
    sleep(5)
    browser.execute_script("document.body.style.zoom='20%'")
    sleep(5)
    resp = browser.page_source
    # I want to check offers only in specific region, so I need to discard offers in other cities
    useful_resp = resp.split("Python</span> in other cities")[0]
    return useful_resp


def get_average_salary_justjoinit(junior_python_dev_jobs_in_warsaw):
    offers_divided_by_pln = junior_python_dev_jobs_in_warsaw.split(" PLN")
    sum_of_salaries = 0
    counter_of_salaries = 0
    for element in offers_divided_by_pln:
        if element[-1] == "k":
            salary = element[-16:].split(">", 1)[1]
            salary2 = salary.replace("k", "")
            salary = salary2.replace(" ", "")
            salary2 = salary.replace("-", " ")
            salary = salary2.split(" ")
            sum_of_actual_salaries = 0
            for i in range(0, len(salary)):
                sum_of_actual_salaries = sum_of_actual_salaries + float(salary[i])
                sum_of_actual_salaries = round(sum_of_actual_salaries, 2)
            mean_of_actual_salaries = round(sum_of_actual_salaries / len(salary), 2)
            sum_of_salaries = sum_of_salaries + mean_of_actual_salaries
            counter_of_salaries = counter_of_salaries + 1
    return round(sum_of_salaries / counter_of_salaries, 2)


junior_python_dev_jobs_in_warsaw = scrap_justjoinit('https://justjoin.it/warszawa/python/junior?tab=with-salary')
average_junior_python_dev_in_warsaw_salary = get_average_salary_justjoinit(junior_python_dev_jobs_in_warsaw)*1000
print("Today, the average salary of junior python developer in Warsaw is {}zł.".format(average_junior_python_dev_in_warsaw_salary))

