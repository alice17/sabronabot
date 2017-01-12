# -*- coding: utf-8 -*-

import StringIO
import json
import logging
import random
import urllib
import urllib2
import time
import re

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

global text

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def getChatsId():
    return EnableStatus.query().fetch(keys_only=True)
    
def deleteChatId(chat_id):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.key.delete()
    
# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))
        
        text = ''
        query_text = ''
        
        adminId = '46731836'    # Alice ID
    
        update_id = body['update_id']
        #message = body['message']
        #query = body['inline_query']
        if 'message' in body:
        # messaggio
            bmessage = body['message'] #estrae bmessage (body message)
            message_id = bmessage.get('message_id')
            date = bmessage.get('date')
            text = bmessage.get('text')
            fr = bmessage.get('from')
            chat = bmessage['chat']
            chat_id = chat['id']
            
        elif 'inline_query' in body:
        # inline query
            query = body['inline_query']
            query_id = query.get('id')
            fr = query.get('from')
            query_text = query.get('query')
            query_offset = query.get('offset')
        
        
        #### FUNCTIONS #####
        
        def reply(msg=None, img=None, imgid=None, sticker=None, voice=None, video=None, venue=None, document=None):    
        # risposta
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg,#.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'parse_mode': 'HTML'
                    #'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id))
                ], [
                    ('photo', 'image.jpg', img)
                ])
                """
                resp = urllib2.urlopen(BASE_URL + 'sendPhoto', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'photo': img,
                })).read()"""
            elif imgid:
                resp = urllib2.urlopen(BASE_URL + 'sendPhoto', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'photo': imgid
                })).read()
            elif sticker:
                resp = urllib2.urlopen(BASE_URL + 'sendSticker', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'sticker': sticker,
                })).read()
            elif voice:
                resp = urllib2.urlopen(BASE_URL + 'sendVoice', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'voice': voice,
                })).read()
            elif venue:
                resp = urllib2.urlopen(BASE_URL + 'sendVenue', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'latitude': ven_lat,
                    'longitude': ven_long,
                    'title': ven_title,
                    'address': ven_address
                })).read()
            elif video:
                resp = urllib2.urlopen(BASE_URL + 'sendVideo', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'video': video,
                })).read()
            elif document:
                resp = urllib2.urlopen(BASE_URL + 'sendDocument', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'document': video,
                })).read()
            else:
                logging.error('reply error')
                resp = None

            logging.info('send response:')
            logging.info(resp)
            

        def broadcast(msg=None, img=None):
            # sends broadcast message to all chats  
            if msg:
                for es in getChatsId():
                    id = str(es.id())  
                    # logging.info(id)
                    if getEnabled(id):
                        try:
                            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                                'chat_id': str(id),
                                'text': msg.encode('utf-8'),
                            })).read()
                        except urllib2.HTTPError, err:
                            if err.code == 403:
                                textAdmin('Errore 403: Forbidden nella chat ' + str(id))
                            else:
                                textAdmin(err)
            elif img:
            # sends picture from url
                for es in getChatsId():
                    id = str(es.id())
                    
                    if getEnabled(id):
                        try:
                            resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                                ('chat_id', str(id))
                            ], [
                                ('photo', 'image.jpg', img)
                            ])
                        except urllib2.HTTPError, err:
                            if err.code == 403:
                                textAdmin('Errore 403: Forbidden nella chat ' + str(id))
                            else:
                                textAdmin(err)
                             
            logging.info('send response:')
            logging.info(resp)
            
        def textAdmin(msg=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': adminId,
                    'text': msg,#.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    #'reply_to_message_id': str(message_id),
                })).read()
            
            logging.info('text admin:')
            logging.info(resp)    
    
        def getChatInfo(chat_id, chatIdGet, toAdmin):
            respp = urllib2.urlopen(BASE_URL + 'getChat', urllib.urlencode({
                'chat_id': chatIdGet,
            })).read()
            
            resp = json.loads(respp)
            resp_dump = json.dumps(resp['result'], indent=0, ensure_ascii=False, encoding="utf-8", separators=(',', ': ')).replace('"', '').strip('{}')
            
            if toAdmin == False:
                reply(resp_dump.encode('utf-8'))
            else:
                textAdmin(resp_dump.encode('utf-8'))
            
        ###### ELABORAZIONE MESSAGGI #####    
        
        try:
            if text and text.startswith('/'):
                # elabora comandi con /
                if text == '/start' or text == '/start@Sabronabot':
                    reply('Ciao, io sono la Sabrona, e adesso ti rompo il culo.')
                    setEnabled(chat_id, True)
                elif text == '/stop' or text == '/stop@Sabronabot':
                    reply('Andrò nel lettone a farmi un ponsino.')
                    setEnabled(chat_id, False)
                elif text.startswith('/broadcastimg'):
                    # invia messaggio broadcast con immagine specificata nell'url
                    broadcast(img=urllib2.urlopen(text[13:]).read()) 
                elif text.startswith('/broadcast '):
                    # invia messaggio broadcast
                    broadcast(msg=text[10:])
                elif getEnabled(chat_id):
                    if text == '/manzi' or text == '/manzi@Sabronabot':
                    # manda foto di manzi
                        #nomefile = BERTHA_URL + 'manzi/manzi' + str(random.randint(1,12)) + '.jpg'
                        #reply(img=urllib2.urlopen(nomefile).read())
                        
                        manzi = ['AgADAgADjK0xGzwSyQKwQ8gxtZFN-n1bhCoABF9wAAEtb_fDeCJhAQABAg',
                                'AgADAgADja0xGzwSyQLec_sMPsuZWhFihCoABMVjeeWx21ieRWYBAAEC',
                                'AgADAgADjq0xGzwSyQLfykzvOvd_p3dhhCoABAgUcHbFXQxZImQBAAEC',
                                'AgADAgADj60xGzwSyQLCl3rhGYFiIZxchCoABFW9WDwFjLTtgGABAAEC',
                                'AgADAgADkK0xGzwSyQL8GCsKByRSJ7FbhCoABN4JoTzX7D8fxGIBAAEC',
                                'AgADAgADka0xGzwSyQJEcSq5wSytur0_hCoABArdNQ7A-JotMGEBAAEC',
                                ]
                        reply(imgid=(random.choice(manzi)))
                    elif text == '/gnagnette' or text == '/gnagnette@Sabronabot':
                    # manda foto di gnagnette
                        gnagnette = ['AgADAgADhrExGzwSyQIlczHRUDnLvmzthSoABIEKwrR4Jg7T5aoAAgI',
                                'AgADAgADh7ExGzwSyQKgKR2hU3FS0fXHgioABKwMZzYKY-tlXXsBAAEC',
                                'AgADAgADiLExGzwSyQKjQKnl8pRImjvXgioABDMvKdeZhNB0oX0BAAEC',
                                'AgADAgADibExGzwSyQImTibg9E9jprrphSoABClf5ilKUpd2BakAAgI',
                                'AgADAgADirExGzwSyQLyhqT8h7dgHPHEgioABLVEt180p3dAQnsBAAEC',
                                'AgADAgADi7ExGzwSyQLN7f-tP3RIsfnFgioABFgUT7bSOwIbPn0BAAEC',
                                'AgADAgADjLExGzwSyQIx9G3b-kfiB9z5hSoABEHbM4sb_-kY4awAAgI',
                                'AgADAgADjrExGzwSyQJbviEkoSCrJR_WgioABP7tkTyBtnwqv4EBAAEC',
                                'AgADAgADj7ExGzwSyQIt0SRGUlEjGk30hSoABNV_sTRBh6ZBQq0AAgI',
                                'AgADAgADkLExGzwSyQIpPvwOt1OPoT-ngioABJw4pwgXIESvEUgBAAEC',
                                'AgADAgADkbExGzwSyQIBk86Bxvy4XHj6hSoABPa62xLBGMgxpKwAAgI',
                                'AgADAgADkrExGzwSyQJhLMC5JppAVZ3YgioABNz6iDBds20qtIABAAEC',
                                'AgADAgADHLgxGzwSyQLAAAFznOEhz7KT4oENAASfAa_0YNbZKPwcAQABAg',
                                'AgADAgADGrgxGzwSyQInYJz_4jiBSk3NgQ0ABH4FRIdjX7ejWx8BAAEC'
                                ]
                        reply(imgid=(random.choice(gnagnette)))
                    elif text == '/cibo' or text == '/cibo@Sabronabot':
                    # manda foto di delizie
                        cibo = ['AgADAgADsbIxGzwSyQK4mwONzrJsA_PqhSoABLxCxOsLqc3ClNoBAAEC',
                                'AgADAgADsrIxGzwSyQLV8Fcoh57nwzTLRw0ABOOjNgABy-M9_KNeAAIC',
                                'AgADAgADs7IxGzwSyQLI77mJYqnNgdogSA0ABCbA8S71xjkcwlsAAgI',
                                'AgADAgADtLIxGzwSyQLvhjZMqSy_Wp34hSoABO8NDXeJSPEsm9cBAAEC',
                                'AgADAgADtbIxGzwSyQJF7eWSaMZ2HinGRw0ABC9BkAu02d3DdF0AAgI',
                                'AgADAgADtrIxGzwSyQJPrxo_cF91j-vphSoABDJcO_HEWCVMs88BAAEC',
                                'AgADAgADt7IxGzwSyQKeRpb6RYrqook1SA0ABH0ySziAa3cMMl4AAgI',
                                'AgADAgADuLIxGzwSyQIDcuJINaZhR2EjSA0ABGCOLCLC1YaNwlkAAgI',
                                'AgADAgADubIxGzwSyQIqnz8IaiAHY1UrSA0ABEHQhLDaQkNnSVsAAgI',
                                'AgADAgADurIxGzwSyQLX1FX_j37kmioUSA0ABIN4RrlZFI5_zVkAAgI',
                                'AgADAgADu7IxGzwSyQJgvkMWumxCYKTARw0ABB9Aws2aRnvZ-l8AAgI',
                                'AgADAgADvLIxGzwSyQL4a3oPHtZ9YXouSA0ABDtWljuFM2JMQVsAAgI',
                                'AgADAgADvbIxGzwSyQKLSY5JwidPFEwOSA0ABGKJ6fiacF-FMV4AAgI',
                                'AgADAgADvrIxGzwSyQJeNQY5np12sIvFRw0ABBQHbpnbiDwNqV4AAgI',
                                'AgADAgADv7IxGzwSyQIc2hzRHB0Nl5IfSA0ABGknMzpNEZcvuFwAAgI',
                                'AgADBAAD5rMxGwZG_gQLJYwa3OtZNOUTYBkABLug6bkHXcH93WACAAEC',
                                'AgADBAAD5bMxGwZG_gQZhX6t2G7wfL1baRkABF6w3x7WF40GV8gAAgI',
                                'AgADBAAD57MxGwZG_gRHjjh7xRecarTRXxkABM6WOUGi6K7tfGECAAEC',
                                'AgADBAAD6LMxGwZG_gS2kDCffw_AY8IuXhkABBpiLMO4pSGcWVwCAAEC',
                                'AgADBAAD67MxGwZG_gSzWoKUW0ZByTk4aRkABFAE6Ga2FBepXsgAAgI'
                                ]
                        reply(imgid=(random.choice(cibo)))
                    elif text == '/citazionibertesche' or text == '/citazionibertesche@Sabronabot':
                    # citazioni bertha
                        frasi = ['\"Voglio il lettone!!\"', 
                                '\"È gnagnetta!\"', 
                                '\"Edooo! La mia vuitton!!\"', 
                                '\"\xF0\x9F\x98\xAD\xF0\x9F\x98\xAD\xF0\x9F\x98\xAD\xF0\x9F\x98\xAD\"',
                                '\"Vi aiuto solo se voglio\"',
                                '\"Beh, fammi un panino\"',
                                '\"<b>Porcodio la gente</b>\"',
                                '\"Colon miar, we are free\"',
                                '\"Non posso uscire questo weekend, sono a cena da mia nonna\"',
                                '\"Il potere è caduto che noi l\'abbiamo fatto cadere\"',
                                '\"Così.\"'
                                ]
                        reply(random.choice(frasi))
                    elif text == '/stats' or text == '/stats@Sabronabot':
                        count = 0
                        for es in getChatsId():
                            count = count + 1
                            getChatInfo(chat_id, str(es.id()), False)
                            
                        reply('Num chat: ' + str(count))
                        
            elif text and getEnabled(chat_id):
                # elabora testo dei messaggi con chat enabled
                if text:
                    nomedir = BERTHA_URL + 'words/'
                    #### TESTO ####
                    if text.upper() == 'ANDREA':
                        reply('<i>\"Mi manca il respiro.\"</i>')
                    elif re.search(r'\bMIZY\b' ,text.upper()):
                        reply('Mizina \xF0\x9F\x98\x8D\xF0\x9F\x98\x8D')
                    elif re.search(r'\bBUONGIORNO\b' ,text.upper()):
                        reply('Vomitino \xF0\x9F\x98\xAD')
                    elif re.search(r'\b(GRAZIE SABRONA|THANK YOU SABRONA)\b' ,text.upper()):
                        reply('Prego stronza **')
                    elif re.search(r'\b(BUONANOTTE|bGOODNIGHT)\b' ,text.upper()):
                        reply('Io sono già a letto dalle 9.')
                    elif re.search(r'\bBERTHAPALOOZA\b' ,text.upper()):
                        frasi = ['<i>Mamma che trash!</i>',
						        '<i>Mi sento qui nel cranio un cratere, non so se ti ho palpato il sedere.</i>',
                                '<i>È mezzanotte ed io divento cattivo, se la serata non concludo in attivo.</i>',
                                '<i>Il primo passo è allontanarne gli amici per montarlo come fosse una bici.</i>',
                                '<i>Das ist Bertha.</i>',
                                '<i>Svuoto il bicchiere con lieto gorgoglio;\nimbizzarrite impazzan le lelle,\ned i fanciulli nel pieno rigoglio\nfanno sganciar le mascelle.</i>'
                                ]
                        reply(random.choice(frasi))
                    elif re.search(r'\b(ETERO|HETERO)\b' ,text.upper()):
                        reply('Etero \xF0\x9F\x98\xB7')
                    elif re.search(r'\bVOMITZ\b' ,text.upper()):
                        reply('<i>\"Lo trafiggo!\" (cit. Andrea)</i>')
                    elif re.search(r'\bDEERWAVES\b' ,text.upper()):
                        reply('Io con gli articoli di deerwaves mi ci pulisco il mio culo(ne).')
                    elif '********' in text.upper():
                        reply('**')
                    elif re.search(r'\b(CIAO|HI)\b' ,text.upper()):
                        reply('Ciao stronza **')
                    elif re.search(r'\bCINESE\b' ,text.upper()):
                        reply('Cinese? Io plendere spaghetti di shoia al male **')  
                    elif re.search(r'\bWHATSAPP\b' ,text.upper()):
                        reply('WhatsApp merda')  
                    elif re.search(r'\b(AMO SABRONA|SABRONABOT TI AMO|I LOVE YOU SABRONA)\b' ,text.upper()):
                        reply('Anche io mi amo \xF0\x9F\x98\x8D')  
                    elif re.search(r'\bJARVIS\b' ,text.upper()):
                        reply('Jarvis, we are common people like you!')  
                    elif text.upper()=='@SABRONABOT':
                        frasi = ['Sa vot?', 'Cusa ghè?', '?', 'Mo elora']
                        reply(random.choice(frasi))  
                    elif re.search(r'\bBRAVA SABRONA\b' ,text.upper()):
                        reply('Grazie troia **')
                    #### STICKERS ####
                    elif re.search(r'\b(FAMMELA VEDERE|LET ME SEE HER)\b' ,text.upper()):
                        reply(sticker='BQADAgAD4AADPBLJAiNxsbj_Dtz_Ag')
                    elif re.search(r'\bVINNIE\b' ,text.upper()):
                        reply(sticker='BQADAgADhAEAAjwSyQKNB2Uulnb3bAI')
                    elif re.search(r'\bANNA GRASSI\b' ,text.upper()):
                        reply(sticker='BQADAgADowEAAjwSyQJqTlUDp8mGMgI')
                    elif re.search(r'\bCOSA\\?\b' ,text) or re.search(r'\bWHAT\\?\b', text):
                        reply(sticker='BQADAgAD1QEAAjwSyQKuxP9mWe1k6AI')
                    elif re.search(r'\bBRETT\b' ,text.upper()):
                        reply(sticker='BQADBAADtAADBkb-BC2chwoXbupNAg')
                    elif re.search(r'\bGIACY\b' ,text.upper()):
                        reply(sticker='BQADBAADfgADBkb-BDeia4iBawS5Ag')
                    elif re.search(r'\bSCOPARE\b' ,text.upper()):
                        reply(sticker='BQADAgAD5AADPBLJAtaPzsq8UT4NAg')
                    elif text.upper()=='INDECENTE':
                        reply(sticker='BQADAgADBgEAAjwSyQJsbFZS-p0OLQI')
                    elif text.upper()=='ODELL':
                        reply(sticker='BQADAgADCQEAAjwSyQIEZFDzz8JvmAI')
                    #### IMMAGINI ####
                    elif re.search(r'\b(AMORE|LOVE)\b' ,text.upper()):
                        reply(imgid='AgADBAADC7AxGwZG_gT_TD3RXz3tAAEVMykZAATUh2tOX17G3aCVAAIC')
                    elif re.search(r'\b(MADRE|MOTHER)\b' ,text.upper()):
                        reply(imgid='AgADBAADp7AxG-JVIQNBU9gcZKIOVwpJaRkABOxEWXSj6X9zfUkAAgI')
                    elif re.search(r'\bDIMAGRIRE\b' ,text.upper()):
                        reply(imgid='AgADBAADCbAxGwZG_gSBMLAgdxyHGSDnJRkABCZIe4oEp7TWcXYBAAEC')
                    elif re.search(r'\b(ARTE|ART)\b' ,text.upper()):
                        reply(imgid='AgADBAADCrAxGwZG_gRbyQifT1LdDHcqKRkABM6Vj4SpO5BILJkAAgI')
                    elif re.search(r'\b(DROGA|DRUGS)\b' ,text.upper()):
                        reply(imgid='AgADAgADqaoxG8CQIAifm1aWXVH_uoDYgioABGVAwlFAPXRqiwMBAAEC')
                    elif re.search(r'\b(SOLDI|MONEY)\b' ,text.upper()):
                        reply(imgid='AgADBAADEbAxGwZG_gT-X0PIIjiKdH_fKxkABGRDsRbJfp5ZOpwAAgI')
                    elif re.search(r'\b(VINTO|WIN)\b' ,text.upper()):
                        reply(imgid='AgADAgADvqoxG8CQIAj5DVZAi5VmGs3rhSoABHzOR6occoUU6WUAAgI')
                    elif re.search(r'\b(SPIARE|SPY)\b' ,text.upper()):
                        reply(imgid='AgADBAADD7AxGwZG_gSaeFpVugybzC5GKRkABExtcjVQyx4kzZoAAgI')
                    elif re.search(r'\A(ALRIGHT|VA BENE)$', text.upper()):
                        reply(imgid='AgADBAADELAxGwZG_gSFooKhzc-t537OHBkABJTkho8S7FTbpLIBAAEC')
                    elif re.search(r'\bSTUPIDO\b' ,text.upper()):
                        reply(imgid='AgADAgADvaoxG8CQIAhjcg5wiiWYxtilgioABHkrqS8qlgtpggMBAAEC')
                    #elif 'FROCI' re.search(r'\b\b' ,text.upper()):
                    #    reply(imgid='AgADBAADFrAxGwZG_gTohyoEBK1St-0PHRkABKSmP-2VmEfJk4UBAAE')
                    elif re.search(r'\b(PIOVE|RAIN)\b' ,text.upper()):
                        reply(imgid='AgADBAADDrAxGwZG_gR0xChBDQOD_1WWJBkABJ-6MoadWi-5aJkAAgI')
                    elif re.search(r'\b(MATTINO|MORNING|MATTINA)\b' ,text.upper()): 
                        reply(imgid='AgADAgADsaoxG8CQIAjeeqT1KkPHBFf5hSoABCEeGTMjeIffa0EAAgI')
                    elif re.search(r'\b(ELEGANTE|SEXY)\b' ,text.upper()):
                        reply(imgid='AgADAgADu6oxG8CQIAghugM8dSOe1Xf6hSoABC7r1uO3wy0wgl4AAgI')
                    elif re.search(r'\A(BRUTTO|BRUTTA|UGLY)$', text.upper()): 
                        reply(imgid='AgADBAADDbAxGwZG_gTu4krVFMJq_qy1JRkABKly90Jsmf6nBXMBAAEC')
                    elif re.search(r'\bPSYCH\b' ,text.upper()):
                        reply(imgid='AgADBAADtK8xGwZG_gRjmdnkyto5MgImHRkABOMXyFgRotq9glACAAEC')
                    elif re.search(r'\bTATA\b' ,text.upper()):
                        reply(imgid='AgADAgADn7cxGzwSyQI7N_DYbJwXG_DLgQ0ABG8EFIh-cI9xK-wAAgI')
                    elif re.search(r'\bGANGSTER\b' ,text.upper()):
                        reply(imgid='AgADAgADkroxGzwSyQKrw9_XE4onB50vSw0ABE_ZVYfnhlGREnwCAAEC')
                    #### GIFS ####
                    #elif 'LSD' re.search(r'\b\b' ,text.upper()):
                    #    reply(document='BQADAgADpwIAAjwSyQJcnLggILrOmQI')
                    #### VOICE ####
                    elif re.search(r'\b(TORTINI|BROWNIE)\b', text.upper()):
                        reply(voice='AwADBAAD6HIGAAHdZekFtBBgtFRkaoAC')
                    elif re.search(r'\b(JENI|SAVAGES)\b', text.upper()):
                        frasi = ['AwADBAADJM4EAAHdZekFGPnlXk_cXigC',
                                 'AwADBAADHd0IAAHdZekFJTeubJfBIOoC',
                                 'AwADBAADBN4IAAHdZekFwL90BVgkyYIC',
                                 'AwADBAADw90IAAHdZekFh2F4Hkr-JhsC',
                                 'AwADBAAD-t0IAAHdZekF2nqX-IDRnBsC',
                                 'AwADBAADFN4IAAHdZekFOnLEv__mVwQC',
                                 'AwADBAADm90IAAHdZekFOBGkKyr26FQC',
                                 'AwADBAADF90IAAHdZekFV6rQM7uPn38C',
                                  ]
                        reply(voice=random.choice(frasi))
                    elif re.search(r'\b(TIZIA SPIGOLOSA|TICIA ESPIGOLOSA)\b', text.upper()):
                        reply(voice='AwADBAADHd0IAAHdZekFJTeubJfBIOoC')
                    elif re.search(r'\b(NON ME NE FOTTE UN CAZZO|NON ME NE FREGA UN CAZZO|GIVE A FUCK)\b' ,text.upper()):
                        reply(voice='AwADBAADDnEIAAHdZekF3uYqV9AWdZgC')
                    elif re.search(r'\bLA DINA\b' ,text.upper()):
                        reply(voice='AwADBAADl8gEAAHdZekFmyL4an9o-MMC')
                    elif re.search(r'\bLA BELLISSIMO\b' ,text.upper()):
                        reply(voice='AwADBAADLMgEAAHdZekFuXLgrgrt-ggC')
                    elif text.upper()=='GNAM GNAM':
                        reply(voice='AwADAgADEAIAAjwSyQKQUNqw9REo7AI')
                    elif text.upper()=='DANZA BERTHA':
                        frasi = ['AwADBAADcgIAAgZG_gR8IlaUu73yPgI',
                                 'AwADBAADcQIAAgZG_gRZzlnA-cQ_JAI',
                                 ]
                        reply(voice=random.choice(frasi))
                    elif re.search(r'\bASTRONAUTA\b' ,text.upper()):
                        reply(voice='AwADAgADUAMAAjwSyQKvuHSsjIfQ-wI')
                    elif re.search(r'\bPRINCE\b' ,text.upper()):
                        reply(voice='AwADAgADUQMAAjwSyQLygx336d7oMwI')
                    #elif 'VETRINA' re.search(r'\b\b' ,text.upper()):
                    #    reply(voice='BQADAgAD4AEAAjwSyQIMz1uOE1DzsQI')
            ##### EVENTI #####
            elif 'message' in body and 'new_chat_member' in bmessage and bmessage.get('new_chat_member').get('username')!='Sabronabot':
                # nuovo membro nella chat
                reply('Ecco un altro rompicoglioni')
            elif 'message' in body and 'new_chat_member' in bmessage and bmessage.get('new_chat_member').get('username')=='Sabronabot':
                # sabrona aggiunta ad una chat
                reply('Ciao. Io sono la Sabrona e adesso vi rompo il culo. \xf0\x9f\x98\x8e') 
                setEnabled(chat_id, True)
                textAdmin('Aggiunta alla chat ' + str(chat_id))
                getChatInfo(adminId, chat_id, True)
            elif 'message' in body and ('left_chat_member' in bmessage and bmessage.get('left_chat_member').get('username') != 'Sabronabot'):
                # membro lascia chat
                reply('A mai più rivederci.')
            elif 'message' in body and ('left_chat_member' in bmessage and bmessage.get('left_chat_member').get('username') == 'Sabronabot'):
                # sabrona eliminata dalla chat 
                deleteChatId(chat_id)
                textAdmin('Eliminata dalla chat ' + str(chat_id))
                # getChatInfo(adminId, chat_id)   --> NON POSSO :(  IMPORTANTE
            elif 'message' in body and 'location' in bmessage:
                reply('Ci sono stata in quel posto e fa cagare.')    
        except urllib2.HTTPError, err:
            if err.code == 404:
                reply('Porco dio manca una foto')
            elif err.code == 400:
                reply('ops, manca una foto')
            elif err.code == 429:
                reply('Le foto al momento non sono disponibili -_- riprova fra qualche ora')
            elif err.code == 403:
                reply('Sembra che non abbia il permesso di eseguire questa azione')
            else:
                raise


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
