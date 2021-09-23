from requests_html import HTMLSession

session = HTMLSession()
resp = session.get("https://justjoin.it/warszawa/python/junior")
resp.html.render()
print(resp.html.html)
