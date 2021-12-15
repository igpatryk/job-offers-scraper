from time import sleep
from selenium import webdriver
import psycopg2
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from ftplib import FTP
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log_file = 'scrapper_' + str(datetime.utcnow().strftime('%Y_%m_%d')) + '.log'
logging.basicConfig(filename=log_file, encoding='utf=8', level=logging.DEBUG, format='%(asctime)s | %(levelname)s'''
                                                                                     ' | %(message)s')
logging.getLogger('matplotlib.font_manager').disabled = True


def scrap_justjoinit(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("window-size=1920,1080")
    browser = webdriver.Chrome(options=options)
    browser.get(link)
    sleep(1)
    browser.execute_script("document.body.style.zoom='20%'")
    sleep(1)
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
    average_junior_python_dev_salary_on_justjoinit = None
    junior_python_dev_jobs_offers_in_warsaw = scrap_justjoinit(
        'https://justjoin.it/warszawa/python/junior?tab=with-salary')
    average_junior_python_dev_in_warsaw_salary = round(get_average_salary_justjoinit(
        junior_python_dev_jobs_offers_in_warsaw), 2)
    junior_python_dev_jobs_offers_remote_poland = scrap_justjoinit(
        'https://justjoin.it/remote-poland/python/junior?tab=with-salary')
    average_junior_python_dev_remote_poland_salary = round(get_average_salary_justjoinit(
        junior_python_dev_jobs_offers_remote_poland), 2)
    if average_junior_python_dev_remote_poland_salary != 0 and average_junior_python_dev_in_warsaw_salary != 0:
        if average_junior_python_dev_remote_poland_salary > average_junior_python_dev_in_warsaw_salary:
            logging.debug("SCRAP RESULT: It is better to look for offers in category 'Remote Poland'! Average salary "
                         "is {}zł more. ".format(average_junior_python_dev_remote_poland_salary
                                                 - average_junior_python_dev_in_warsaw_salary))
        else:
            logging.debug("SCRAP RESULT: It is better to look for offers based in Warsaw! Average salary is {}zł more. "
                         .format(average_junior_python_dev_in_warsaw_salary
                                 - average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        logging.debug("SCRAP RESULT: Today the average salary of junior python developer in Warsaw according to offers "
                     "on justjoin.it is {}zł.".format(average_junior_python_dev_in_warsaw_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        logging.debug("SCRAP RESULT: Today the average salary of junior python developer working remotely in Poland ""ac"
                     "cording to offers on ""justjoin.it is {}.zł"
                     .format(average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary != 0:
        average_junior_python_dev_salary_on_justjoinit = round(((average_junior_python_dev_in_warsaw_salary +
                                                          average_junior_python_dev_remote_poland_salary) / 2), 2)
    elif average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary == 0:
        average_junior_python_dev_salary_on_justjoinit = average_junior_python_dev_in_warsaw_salary
    elif average_junior_python_dev_in_warsaw_salary == 0 and average_junior_python_dev_remote_poland_salary != 0:
        average_junior_python_dev_salary_on_justjoinit = average_junior_python_dev_remote_poland_salary
    return average_junior_python_dev_in_warsaw_salary, average_junior_python_dev_remote_poland_salary, \
        average_junior_python_dev_salary_on_justjoinit


def insert_data(date, warsaw, remote, avg):
    conn = psycopg2.connect(
        host=os.environ.get('pg_host'),
        database=os.environ.get('pg_database'),
        user=os.environ.get('pg_user'),
        password=os.environ.get('pg_password')
    )
    try:
        logging.info("Trying to insert data to PGSQL.")
        sql = """INSERT INTO salaries.justjoinit(date, warsaw, remote, avg) VALUES (%s,%s,%s,%s);"""
        data = (date, warsaw, remote, avg)
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        logging.info("Record inserted successfully into justjoinit table.")
    except (Exception, psycopg2.Error) as error:
        logging.error(error)


def select_data(sql):
    conn = psycopg2.connect(
        host=os.environ.get('pg_host'),
        database=os.environ.get('pg_database'),
        user=os.environ.get('pg_user'),
        password=os.environ.get('pg_password')
    )
    cur = None
    try:
        query = sql
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        dates = []
        warsaw = []
        remote = []
        avg = []
        for row in rows:
            dates.append(row[0])
            warsaw.append(row[1])
            remote.append(row[2])
            avg.append(row[3])
        cur.close()
        conn.close()
        return dates, warsaw, remote, avg
    except (Exception, psycopg2.Error) as error:
        logging.error(error)
    finally:
        if conn:
            cur.close()
            conn.close()
            logging.info("Closed PGSQL Connection.")


def make_graph(dates, warsaw, remote, avg):
    x = np.arange(len(dates))
    width = 0.2
    fig, ax = plt.subplots()
    ax.set_facecolor("white")
    ax.set_ylabel('PLN')
    ax.set_title('Junior Python Dev Salary')
    ax.set_xticks(x, dates)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#808080", linestyle="dashed")
    warsaw = ax.bar(x - width, warsaw, width, color='#F5CABF', label='Warsaw')
    avg = ax.bar(x, avg, width, color="#C6F58E", label='Average')
    remote = ax.bar(x + width, remote, width, color="#A6B9F5", label='Remote')
    ax.legend()
    ax.bar_label(warsaw, padding=3)
    ax.bar_label(avg, padding=3)
    ax.bar_label(remote, padding=3)
    plt.gcf().set_size_inches(18, 9)
    plt.savefig('graph.png')


def upload_to_ftp():
    ftp = FTP(os.environ.get('ftp_address'))
    ftp.login(user=os.environ.get('ftp_user'), passwd=os.environ.get('ftp_password'))
    ftp.cwd('/patryk/wp-content/uploads/2021/12')
    ftp.encoding = "utf-8"
    with open('graph.png', 'rb') as file:
        ftp.storbinary('STOR graph.png', file)
    ftp.quit()


def create_report(remote, warsaw, avg, monthly):
    global smtp_mail
    smtp_mail = os.environ.get('smtp_mail')
    global receiver_mail
    receiver_mail = os.environ.get('my_mail')
    daily_subject = "Daily salaries-scrapper's report"
    daily_body = "Hi! It's me, salaries-scrapper.\n" \
           "Today:\n" \
           "- the average salary of Junior Python Developer who works in Warsaw is {}zł.\n" \
           "- the average salary of Junior Python Developer who works remotely is {}zł.\n" \
           "- the average of these salaries is {}zł.\n" \
           "This data was scrapped from justjoin.it website.\n" \
           "There is a graph for the last 7 days in the attachment, take a look!".format(warsaw, remote, avg)
    monthly_subject = "Monthly salaries-scrapper's report"
    monthly_body = "Hi! It's me, salaries-scrapper.\n" \
           "In the previous month:\n" \
           "- the average salary of Junior Python Developer who works in Warsaw was {}zł.\n" \
           "- the average salary of Junior Python Developer who works remotely was {}zł.\n" \
           "- the average of these salaries was {}zł.\n" \
           "This data was scrapped from justjoin.it website.\n" \
           "There is a graph for the last one month in the attachment, take a look!".format(warsaw, remote, avg)
    message = MIMEMultipart()
    message["From"] = smtp_mail
    message["To"] = receiver_mail
    if monthly == 0:
        message["Subject"] = daily_subject
        message.attach(MIMEText(daily_body, "plain"))
    else:
        message["Subject"] = monthly_subject
        message.attach(MIMEText(monthly_body, "plain"))
    with open('graph.png', 'rb') as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= graph.png",
    )
    message.attach(part)
    text = message.as_string()
    return text


def send_mail(msg):
    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_password = os.environ.get('smtp_password')
        logging.info("Trying to send an email.")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_mail, smtp_password)
            server.sendmail(smtp_mail, receiver_mail, msg)
            server.quit()
    except Exception as e:
        logging.error(e)
    else:
        logging.info("Successfully send an email.")

logging.info("Started job-offers-scrapper.")
# get salaries
average_junior_python_dev_in_warsaw_salary, average_junior_python_dev_remote_poland_salary, \
average_junior_python_dev_salary_on_justjoinit = process_justjoinit_data()
# insert salaries into pgsql database with today's date
insert_data(datetime.today().strftime('%Y-%m-%d'), average_junior_python_dev_in_warsaw_salary,
            average_junior_python_dev_remote_poland_salary, average_junior_python_dev_salary_on_justjoinit)
# select data from pgsql database for latest 7 days
select = "SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '7' day order by date ASC"
dates, warsaw, remote, avg = select_data(select)
# make a graph
make_graph(dates, warsaw, remote, avg)
# upload file to the ftp
upload_to_ftp()
# create daily report
message = create_report(average_junior_python_dev_remote_poland_salary, average_junior_python_dev_in_warsaw_salary, average_junior_python_dev_salary_on_justjoinit, 0)
# send daily report
send_mail(message)
# monthly report
if datetime.today().strftime('%d') == '01':
    select = "SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '1 months' order by date ASC"
    dates, warsaw, remote, avg = select_data(select)
    make_graph(dates, warsaw, remote, avg)
    monthly_remote_avg = sum(remote) / len(remote)
    monthly_warsaw_avg = sum(warsaw) / len(warsaw)
    monthly_avg_avg = sum(avg) / len(avg)
    message = create_report(monthly_remote_avg, monthly_warsaw_avg, monthly_avg_avg, 1)
    send_mail(message)
logging.info("Stopped job-offers-scrapper.")
