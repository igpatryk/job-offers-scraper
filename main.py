from time import sleep
from selenium import webdriver


# Let's scrap justjoin.it!

def scrap_justjoinit(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    # options.add_argument('window-size=1200x600')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(chrome_options=options)
    browser.get(link)
    sleep(5)
    browser.execute_script("document.body.style.zoom='20%'")
    sleep(5)
    resp = browser.page_source
    # I want to check offers only in specific region, so I need to discard offers in other cities
    useful_resp = resp.split("Python</span> in other cities")[0]
    return useful_resp


def get_average_salary_justjoinit(offers):
    if 'PLN' in offers:
        offers_divided_by_pln = offers.split(" PLN")
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
        return round(sum_of_salaries / counter_of_salaries, 2) * 1000
    else:
        return 0


def process_justjoinit_data():
    junior_python_dev_jobs_offers_in_warsaw = scrap_justjoinit(
        'https://justjoin.it/warszawa/python/junior?tab=with-salary')
    average_junior_python_dev_in_warsaw_salary = get_average_salary_justjoinit(junior_python_dev_jobs_offers_in_warsaw)
    junior_python_dev_jobs_offers_remote_poland = scrap_justjoinit(
        'https://justjoin.it/remote-poland/python/junior?tab=with-salary')
    average_junior_python_dev_remote_poland_salary = get_average_salary_justjoinit(
        junior_python_dev_jobs_offers_remote_poland)
    if average_junior_python_dev_remote_poland_salary != 0 and average_junior_python_dev_in_warsaw_salary != 0:
        if average_junior_python_dev_remote_poland_salary > average_junior_python_dev_in_warsaw_salary:
            print("It is better to look for offers in category 'Remote Poland'! Average salary is {}zł more."
                  .format(average_junior_python_dev_remote_poland_salary - average_junior_python_dev_in_warsaw_salary))
        else:
            print("It is better to look for offers based in Warsaw! Average salary is {}zł more. "
                  .format(average_junior_python_dev_in_warsaw_salary - average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        print(
            "Today the average salary of junior python developer in Warsaw according to offers on justjoin.it is {}zł."
            .format(average_junior_python_dev_in_warsaw_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        print("Today the average salary of junior python developer working remotely in Poland according to offers on "
              "justjoin.it is {}.zł".format(average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary != 0:
        return (average_junior_python_dev_in_warsaw_salary + average_junior_python_dev_remote_poland_salary) / 2
    elif average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary == 0:
        return average_junior_python_dev_in_warsaw_salary
    elif average_junior_python_dev_in_warsaw_salary == 0 and average_junior_python_dev_remote_poland_salary != 0:
        return average_junior_python_dev_remote_poland_salary


average_junior_python_dev_salary_on_justjoinit = process_justjoinit_data()  # I'm looking for a job in Warsaw or for
# a remotely job so I won't check other categories on justjoin.it

# Let's scrap other site - nofluffjobs.com/pl! Coming soon...


# def scrap_nofluffjobs(link):
#    browser = webdriver.Chrome()
#    browser.get(link)
#    sleep(5)
#    browser.execute_script("document.body.style.zoom='20%'")
#    sleep(5)
#    resp = browser.page_source
#    return resp
