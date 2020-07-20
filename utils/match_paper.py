import re
from fuzzywuzzy.fuzz import ratio


def match_aminer_paper(title: str, aminer_title: str):
    aminer_title = aminer_title.replace('&quot;', ' ')
    title_nosymbol = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title.lower())
    a_title_nosymbol = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', aminer_title.lower())
    if ratio(title_nosymbol, a_title_nosymbol) > 97:
        return 1
    else:
        return 0