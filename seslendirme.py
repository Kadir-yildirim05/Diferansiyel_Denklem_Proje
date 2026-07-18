from gtts import gTTS
from playsound import playsound
import time
import sys
import os
import threading
import uuid


def yazi_yaz(metin):
    for harf in metin:
        sys.stdout.write(harf)
        sys.stdout.flush()
        time.sleep(0.05)
    print()

def ses_hazirla(metin):
    dosya = f"ses_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=metin, lang='tr')
    tts.save(dosya)
    return dosya

def adim_listesi_oku(adimlar):
    for adim in adimlar:
        dosya = ses_hazirla(metinduzenleme(adim))
        time.sleep(0.05) # kod hızlı akarken ses dosyası oluşturup silme buna yetişebilsin diye yaptım.
        playsound(dosya)  #threading kullanımını kaldırdım sesleri aynı ayda çalıştırmayı sağlıyordu buda hataya sebep oluyordu.paralel kullanımlar için iyi
        time.sleep(0.05)
        os.remove(dosya)

import re

def metinduzenleme(expr):
    expr = str(expr)

    # --- 1.ADIM ---
    expr = expr.replace("evaluate=False", "")
    expr = expr.replace("y_lnduzelt", "")
    expr = expr.replace("DxDyduzelt", "")
    expr = expr.replace("y_s", "ye")
    expr = expr.replace("y(x)", "ye")

    # --- 2.ADIM Eq(...) içindeki sadece İLK virgülü eşittir yapar ---
    #iç içe parantezlerde de yapar
    #if elif else olmasa her karaktere aynı işlem yapılır F(x,y) içindeki virgülüde eşittir yapardı
    def eq_virgul_duzenle(m):
        icerik = m.group(1) #m.group parantez içine alınan kısımlar
        derinlik = 0 #derinlik kaç tane iç içe parantez açıldığını sayar
        yeni = [] #String’e karakter karakter eklemek için. Python’da string’e += ile karakter eklemek yerine listeye ekleyip sonunda birleştirdim
        degistirildi = False #virgülü sadece bir kez değiştirmek için durdurur kilit yapar
        for kar in icerik: #kar değişken ismi karakteri kısalttım
            if kar == '(':
                derinlik += 1
                yeni.append(kar)
            elif kar == ')':
                derinlik -= 1
                yeni.append(kar)
            elif kar == ',' and not degistirildi and derinlik == 0:
                yeni.append(' eşittir ')
                degistirildi = True
            else:
                yeni.append(kar)
        return ''.join(yeni)
    expr = re.sub(r'Eq\(((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*)\)', eq_virgul_duzenle, expr)

    # --- 3.ADIM Türevli kısımlar  ---
    expr = re.sub(r"Derivative\(y\(x\),\s*x\)", "ye nin birinci türevi", expr)
    expr = re.sub(r"y'", "ye nin birinci türevi", expr)

    # --- 4.ADIM Fonksiyonlar ---
    expr = re.sub(r'exp\(([^()]+)\)', lambda m: 'e üzeri ' + m.group(1), expr)
    expr = re.sub(r'ln\(([^)]+)\)',  lambda m: 'elen ' + m.group(1), expr)
    expr = re.sub(r'log\(([^)]+)\)', lambda m: 'logaritma ' + m.group(1), expr)
    expr = re.sub(r'sin\(([^)]+)\)', lambda m: 'sinüs ' + m.group(1), expr)
    expr = re.sub(r'cos\(([^)]+)\)', lambda m: 'kosinüs ' + m.group(1), expr)
    expr = re.sub(r'tan\(([^)]+)\)', lambda m: 'tanjant ' + m.group(1), expr)

    # --- 5.ADIM Kısmi türevler ---
    expr = expr.replace("∂F/∂x", "Fe nin ix e göre kısmi türevi")
    expr = expr.replace("∂F/∂y", "Fe nin ye ye göre kısmi türevi")
    expr = expr.replace("əF/əX", "Fe nin ix e göre kısmi türevi")
    expr = expr.replace("əF/əY", "Fe nin ye ye göre kısmi türevi")

    # --- 6.ADIM fonksiyonlar ---
    expr = re.sub(r"H'\(y\)", "He nin ye göre türevi", expr)
    expr = re.sub(r"H'\(x\)", "He nin ix e göre türevi", expr)
    expr = re.sub(r"H\(y\)", "He ye", expr)
    expr = re.sub(r"H\(x\)", "He ix", expr)
    expr = re.sub(r"M\(y\)", "Me ye", expr)
    expr = re.sub(r"N\(x\)", "Ne ix", expr)
    expr = re.sub(r"F\(x,\s*y\)", "Fe ix ye", expr)
    expr = re.sub(r"M\(x,\s*y\)", "Me ix ye", expr)
    expr = re.sub(r"N\(x,\s*y\)", "Ne ix ye", expr)

    # --- 7.ADIM My, Nx ---
    expr = re.sub(r'\bMy\b', "Me nin ye göre türevi", expr)
    expr = re.sub(r'\bNx\b', "Ne nin ix göre türevi", expr)

    # --- 8.ADIM Üslü ifadeler (sayı dönüşümünden önce yapılmalı) ---
    us_sozluk = {'2': 'kare', '3': 'küp', '4': 'dördüncü kuvveti', '5': 'beşinci kuvveti'}
    expr = re.sub(r'\by\*\*(\d+)', lambda m: 'ye ' + us_sozluk.get(m.group(1), m.group(1) + ' inci kuvveti'), expr)
    expr = re.sub(r'\bx\*\*(\d+)', lambda m: 'ix ' + us_sozluk.get(m.group(1), m.group(1) + ' inci kuvveti'), expr)
    expr = re.sub(r'\*\*(\d+)', lambda m: ' üzeri ' + m.group(1), expr)
    expr = re.sub(r'\^(\d+)',   lambda m: ' üzeri ' + m.group(1), expr)

    # --- 9.ADIM Katsayılı çarpımlar (sayı dönüşümü burada, sadece *y ve *x önünde) ---
    sayi_sozluk = {'1':'bir','2':'iki','3':'üç','4':'dört','5':'beş','6':'altı','7':'yedi','8':'sekiz','9':'dokuz','10':'on'}

    expr = re.sub(r'(\d+)\s*\*\s*y(?!\w)', lambda m: sayi_sozluk.get(m.group(1), m.group(1)) + ' ye', expr)
    expr = re.sub(r'(\d+)\s*\*\s*x(?!\w)', lambda m: sayi_sozluk.get(m.group(1), m.group(1)) + ' ix', expr)
    expr = expr.replace("*", " ")

    # --- 10.ADIM dx, dy (\b ile sadece kelimenin tamamı) ---
    expr = re.sub(r'\(dy\)', ' de ye ', expr)
    expr = re.sub(r'\(dx\)', ' de ix ', expr)
    expr = re.sub(r'\bdy\b',  ' de ye ', expr)
    expr = re.sub(r'\bdx\b',  ' de ix ', expr)

    # --- 11.ADIM Tek başına y ve x (\b ile diğer kelimeleri bozmaz) ---
    expr = re.sub(r'\by\b', 'ye', expr)
    expr = re.sub(r'\bx\b', 'ix', expr)

    # --- 12.ADIM Sabitler ---
    expr = re.sub(r'\bC1\b', 'Ce bir', expr)
    expr = re.sub(r'\bC2\b', 'Ce iki', expr)
    expr = re.sub(r'\bC3\b', 'Ce üç', expr)

    # --- 13.ADIM Sembolik kalıpları temizle ---
    expr = re.sub(r'\bEq\(',      '', expr)
    expr = re.sub(r'\bAdd\(',     '', expr)
    expr = re.sub(r'\bsimplify\(','', expr)

    # --- 14.ADIM Operatörler ---
    expr = expr.replace("/", " bölü ")
    expr = expr.replace("+", " artı ")
    expr = expr.replace("-", " eksi ")
    expr = re.sub(r'=\s*0\b',          ' eşittir sıfır', expr)
    expr = re.sub(r'(?<![<>!])=(?!=)', ' eşittir ', expr)

    # Tek başına kalan sayıları kelimeye çevir
    sayi_kelime = {r'\b0\b': 'sıfır', r'\b1\b': 'bir', r'\b2\b': 'iki',
        r'\b3\b': 'üç', r'\b4\b': 'dört', r'\b5\b': 'beş',
        r'\b6\b': 'altı', r'\b7\b': 'yedi', r'\b8\b': 'sekiz',
        r'\b9\b': 'dokuz'}
    for rakam, kelime in sayi_kelime.items():
        expr = re.sub(rakam, kelime, expr)

    # --- 15.ADIM Son kısım---
    expr = re.sub(r'[ \t]+', ' ', expr)
    expr = expr.strip()

    return expr


#def adim_listesi_oku(adimlar: list):
#    for adim in adimlar:
#        #ses_hazirla(metinduzenleme(adim)) bu komutu da kaldırdım
#        ses_hazirla(adim)


# ── TEST ──────────────────────────────────────────────
adimlar = [
    "Birinci adım. Değişkenleri ayırıyoruz.",
    "İkinci adım. Her iki tarafın integralini alıyoruz.",
    "Üçüncü adım. Çözüme ulaştık."
]

#                    YAPILACAKLAR
#adımkların altına daha iyi seslendirecek kelimeleri bul ve tekrar düzenle
#metinleri düzenlemek için tek bir def fonksiyonu oluşturulabilirmi araştır
#denklem seslendirme için bir fonksiyon (def) oluştur. kesin bir def gerekiyor.






#adim_listesi_oku(adimlar)

# Önce ses dosyasını hazırla (internet gerekiyor, zaman alır)
#metin = 'Birinci adım. Diferansiyel denklemi çözmeye başlıyoruz.'
#ses_hazirla(metin)

# Dosya hazır olduktan sonra ikisini aynı anda başlat
#yazi_thread = threading.Thread(target=yazi_yaz, args=(metin,))
#ses_thread = threading.Thread(target=ses_cal)

#yazi_thread.start()
#ses_thread.start()

#yazi_thread.join()
#ses_thread.join()