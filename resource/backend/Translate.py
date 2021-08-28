import requests 

def google_tl(text, lang):
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={}&dt=t&q={}'.format(text, lang)
    print(url)
    r = requests.get(url)
    return r.json()[0][0][0]

# result = requests.get( 
#    "https://api.deepl.com/v2/translate", 
#    params={ 
#      "auth_key": auth_key, 
#      "target_lang": target_language, 
#      "text": text, 
#    }, 
# ) 
# translated_text = result.json()["translations"][0]["text"]

# https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=こんにちは
# https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=das ist ein krankenhaus

# print(google_tl("id", "das ist ein krankenhaus"))
# print(google_tl("jp", "こにちわ"))
