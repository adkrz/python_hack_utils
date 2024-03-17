"""
This script allows pasting raw HTTP request headers and body (e.g. caught from OWASP ZAP or Burp)
and convert them to dictionaries, usable with Python requests module.
It parses:
- headers (skipping ones not needed or regenerated anyway, like Content-Length)
- cookies from headers (to separate dictionary, with url-decode), to be used with requests cookies or session
- body as form data (with url-decode), to use with data=...
- for JSON body, no special parsing is needed - just use import json + json.loads(str) and then in requests use json=...
The repr of each dictionary can be easily copied and adjusted to current needs.
"""

from urllib.parse import unquote


def query_or_post_to_dict(raw):
    d = {}
    for param in raw.split("&"):
        vars = param.split("=")
        vv = vars[1]
        isint = False
        try:
            vv = int(vv)
            isint = True
        except:
            pass
        d[unquote(vars[0])] = unquote(vv) if not isint else vv
    return d


def parse_headers(raw: str):
    ignored_headers = ["dnt", "content-length", "host"]
    d = {}
    method = ""
    url = ""
    cookie_dict = {}
    for line in raw.split("\n"):
        line = line.strip()
        if line:
            if " HTTP/" in line:
                vars = line.split(" ")
                method = vars[0]
                url = vars[1]
            elif ": " in line:
                vars = line.split(": ")
                name = vars[0]
                value = vars[1]
                if name.lower() in ignored_headers:
                    continue
                if name.lower() == "cookie":
                    cookies = value.split("; ")
                    for c in cookies:
                        kvp = c.split("=")
                        if len(kvp) == 2:
                            cookie_dict[unquote(kvp[0])] = unquote(kvp[1])
                else:
                    d[name] = value
    return d, method, url, cookie_dict


headers = """
POST https://example.com HTTP/1.1
host: example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: pl,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Origin: https://example.com
Sec-GPC: 1
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: iframe
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
"""

body = "value1=a&value2=b"

h, _, _, cookie = parse_headers(headers)
print(h)

print(query_or_post_to_dict(body))