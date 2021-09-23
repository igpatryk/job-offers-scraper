from requests_html import HTMLSession

session = HTMLSession()
resp = session.get("https://justjoin.it/warszawa/python/junior")
resp.html.render()
dividedbypln = resp.html.html.split(' PLN')
for element in dividedbypln:
    if element[-1]=='k':
        print(element[-16:].split(">",1)[1])