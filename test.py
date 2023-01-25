from pprint import pprint
from deepl_scraper_pw import deepl_tr

pprint(deepl_tr("Test me\n\nTest him"))
# '测试我\n\n测试他'

pprint(deepl_tr("Test me\n\nTest him", from_lang="en", to_lang="de"))
# 'Teste mich\n\nTesten Sie ihn'
