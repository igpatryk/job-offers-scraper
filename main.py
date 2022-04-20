import psycopg2
import logging
import ftplib
import os
import smtplib
import numpy
import matplotlib.pyplot as plt
from time import sleep
from selenium import webdriver
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class JustJoinItOffersScrapper:
    def __init__(self, link):
        self.link = link

    def scrap(self):
        link = self.link
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("window-size=1920,1080")
        browser = webdriver.Chrome(options=options)
        browser.get(link)
        sleep(10)
        browser.execute_script("document.body.style.zoom='20%'")
        sleep(10)
        resp = browser.page_source
        useful_resp = resp.split("Python</span> in other cities")[0]
        return useful_resp

    def get_avg_salary(self):
        offers = self.scrap()
        if 'PLN' in offers:
            offers_divided_by_pln = offers.split(" PLN")
            sum_of_salaries = 0
            counter_of_salaries = 0
            for element in offers_divided_by_pln:
                if element[-1] == "k":
                    salary = element[-16:].split(">", 1)[1]
                    salary = salary \
                        .replace("k", "") \
                        .replace(" ", "") \
                        .replace("-", " ") \
                        .split(" ")
                    sum_of_actual_salaries = 0
                    for i in range(0, len(salary)):
                        sum_of_actual_salaries = sum_of_actual_salaries + float(salary[i])
                        sum_of_actual_salaries = round(sum_of_actual_salaries, 2)
                    mean_of_actual_salaries = round(sum_of_actual_salaries / len(salary), 2)
                    sum_of_salaries = sum_of_salaries + mean_of_actual_salaries
                    counter_of_salaries = counter_of_salaries + 1
            avg = round(sum_of_salaries / counter_of_salaries, 2) * 1000
            return avg
        else:
            logging.warning("Did not found offers!")
            return 0


class PostgresConnector:
    def __init__(self):
        self.host = os.environ.get('pg_host')
        self.database = os.environ.get('pg_database')
        self.user = os.environ.get('pg_user')
        self.password = os.environ.get('pg_password')
        self.date = datetime.today().strftime('%Y-%m-%d')

    def insert_salaries(self, warsaw, remote, avg):
        date = self.date
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logging.debug("Trying to insert data to DB: {}, {}, {}, {}"
                          .format(date, warsaw, remote, avg))
            sql = """INSERT INTO salaries.justjoinit(date, warsaw, remote, avg) VALUES (%s,%s,%s,%s);"""
            data = (date, warsaw, remote, avg)
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
        except (Exception, psycopg2.Error) as error:
            logging.error(error)
        else:
            logging.info("Record inserted successfully into justjoinit table.")
        finally:
            if cur:
                cur.close()
                logging.info("Closed cursor.")
            if conn:
                conn.close()
                logging.info("Closed PGSQL Connection.")

    def select_salaries(self, sql):
        conn = None
        cur = None
        db_dates = []
        db_warsaw = []
        db_remote = []
        db_avg = []
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logging.debug("Trying to fetch data from DB with SQL: {}".format(sql))
            query = sql
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                db_dates.append(row[0])
                db_warsaw.append(row[1])
                db_remote.append(row[2])
                db_avg.append(row[3])
            cur.close()
            conn.close()
        except (Exception, psycopg2.Error) as error:
            logging.error(error)
        else:
            logging.info("Data fetched from DB: {}, {}, {}, {}.".format(db_dates, db_warsaw, db_remote, db_avg))
        finally:
            if cur:
                cur.close()
                logging.info("Closed cursor.")
            if conn:
                conn.close()
                logging.info("Closed PGSQL Connection.")
        return db_dates, db_warsaw, db_remote, db_avg


class Report:
    def __init__(self, monthly=False):
        self.ftp_address = os.environ.get('ftp_address')
        self.ftp_user = os.environ.get('ftp_user')
        self.ftp_pwd = os.environ.get('ftp_password')
        if not monthly:
            self.email_subject = "Daily salaries-scrapper's report"
            self.email_body = """Hi! It's me, salaries-scrapper.
Today: 
- the average salary of Junior Python Developer who works in Warsaw is {}zł."
- the average salary of Junior Python Developer who works remotely is {}zł."
The average of these salaries is {}zł."
This data was scrapped from justjoin.it website."
There is a graph for the last 7 days in the attachment, take a look!"""
            self.sql = """SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '7' day order by date ASC"""
            self.graph_name = "daily_graph.png"
        else:
            self.email_subject = "Monthly salaries-scrapper's report"
            self.email_body = """Hi! It's me, salaries-scrapper.
In the previous month:
- the average salary of Junior Python Developer who works in Warsaw was {}zł.
- the average salary of Junior Python Developer who works remotely was {}zł.
The average of these salaries is {}zł.
This data was scrapped from justjoin.it website.
There is a graph for the last one month in the attachment, take a look!"""
            self.sql = """SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '1 months' order by date ASC"""
            self.graph_name = "monthly_graph.png"

    def make_graph(self, dates, warsaw, remote, avg):
        x = numpy.arange(len(dates))
        width = 0.2
        fig, ax = plt.subplots()
        ax.set_facecolor("white")
        ax.set_ylabel('PLN')
        ax.set_title('Junior Python Dev Salary')
        ax.set_xticks(x, dates)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color="#808080", linestyle="dashed")
        warsaw_bar = ax.bar(x - width, warsaw, width, color='#F5CABF', label='Warsaw')
        avg_bar = ax.bar(x, avg, width, color="#C6F58E", label='Average')
        remote_bar = ax.bar(x + width, remote, width, color="#A6B9F5", label='Remote')
        ax.legend()
        ax.bar_label(warsaw_bar, padding=3)
        ax.bar_label(avg_bar, padding=3)
        ax.bar_label(remote_bar, padding=3)
        plt.gcf().set_size_inches(18, 9)
        plt.savefig(self.graph_name)
        logging.info(f"Plot created and saved to {self.graph_name}")

    def upload_to_ftp(self, dates, warsaw, remote, avg):
        self.make_graph(dates, warsaw, remote, avg)
        try:
            logging.info("Trying to upload file to FTP server.")
            ftp = ftplib.FTP(self.ftp_address)
            ftp.login(user=self.ftp_user, passwd=self.ftp_pwd)
            ftp.cwd('/patryk/wp-content/uploads/2021/12')
            ftp.encoding = "utf-8"
            with open(self.graph_name, 'rb') as file:
                ftp.storbinary(f'STOR {self.graph_name}', file)
            ftp.quit()
        except ftplib.all_errors as e:
            logging.error("FTP ERROR: {}".format(e))
        else:
            logging.info("File uploaded successfully to FTP server.")

    def create_message(self, warsaw, remote, avg):
        mail_from = os.environ.get('smtp_mail')
        mail_to = os.environ.get('my_mail')
        subject = self.email_subject
        body = self.email_body.format(warsaw, remote, avg)
        message = MIMEMultipart()
        message["From"] = mail_from
        message["To"] = mail_to
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        with open(f'{self.graph_name}', 'rb') as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {self.graph_name}",
        )
        message.attach(part)
        text = message.as_string()
        return text

    def send_email(self, warsaw, remote, avg):
        msg = self.create_message(warsaw, remote, avg)
        try:
            receiver_mail = os.environ.get('my_mail')
            smtp_mail = os.environ.get('smtp_mail')
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


def main():
    logging.info("Started salaries-scrapper.")
    jjit_warsaw_dev_offers_link = 'https://justjoin.it/warszawa/python/junior?tab=with-salary'
    logging.info(f"Set up justjoin.it junior Python dev in Warsaw job offers link as {jjit_warsaw_dev_offers_link}.")
    jjit_remote_dev_offers_link = 'https://justjoin.it/remote/python/junior?tab=with-salary'
    logging.info(f"Set up justjoin.it remote junior Python dev job offers link as {jjit_remote_dev_offers_link}.")
    jjit_warsaw_dev_salary = JustJoinItOffersScrapper(jjit_warsaw_dev_offers_link).get_avg_salary()
    logging.debug(f"Average salary of junior Python dev working in Warsaw is {jjit_warsaw_dev_salary}.")
    jjit_remote_dev_salary = JustJoinItOffersScrapper(jjit_remote_dev_offers_link).get_avg_salary()
    logging.debug(f"Average salary of junior Python dev working remotely is {jjit_remote_dev_salary}.")
    jjit_avg_dev_salary = round((jjit_remote_dev_salary + jjit_warsaw_dev_salary)/2, 2)
    logging.debug(f"Average salary of junior Python dev basing on scrapped offers is {jjit_avg_dev_salary}.")
    pg_database = PostgresConnector()
    pg_database.insert_salaries(jjit_warsaw_dev_salary, jjit_remote_dev_salary, jjit_avg_dev_salary)
    daily_report = Report(monthly=False)
    dates, warsaw, remote, avg = pg_database.select_salaries(daily_report.sql)
    daily_report.upload_to_ftp(dates, warsaw, remote, avg)
    daily_report.send_email(jjit_warsaw_dev_salary, jjit_remote_dev_salary, jjit_avg_dev_salary)
    if datetime.today().strftime('%d') == '01':
        monthly_report = Report(monthly=True)
        dates, warsaw, remote, avg = pg_database.select_salaries(monthly_report.sql)
        monthly_report.upload_to_ftp(dates, warsaw, remote, avg)
        monthly_remote_avg = round((sum(remote) / len(remote)), 2)
        monthly_warsaw_avg = round((sum(warsaw) / len(warsaw)), 2)
        monthly_avg = round((sum(avg) / len(avg)), 2)
        monthly_report.send_email(monthly_warsaw_avg, monthly_remote_avg, monthly_avg)
    logging.info("Stopped salaries-scrapper.")
    exit(0)


if __name__ == '__main__':
    current_date = str(datetime.utcnow().strftime('%Y_%m_%d'))
    log_file = 'scrapper_' + current_date + '.log'
    log_format = '%(asctime)s | %(levelname)s | %(message)s'
    logging.basicConfig(filename=log_file, encoding='utf=8', level=logging.DEBUG, format=log_format)
    logging.getLogger('matplotlib.font_manager').disabled = True
    main()
