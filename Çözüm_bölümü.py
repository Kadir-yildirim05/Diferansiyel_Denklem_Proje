from sympy import *
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from pdf_oluşturma_kütüphanesi import tur_bulma_pdf,dadd_pdf,tdd_pdf,thg_pdf
from seslendirme import adim_listesi_oku
import datetime, re

zaman_etiketi=datetime.datetime.now().strftime("%H%M%S")
init_printing()
dx = symbols('dx')
dy = symbols('dy')
x=symbols('x')
C=symbols('C')
C1= symbols('C1')
C2= symbols('C2')
C3= symbols('C3')
y= Function('y')
y_s = symbols('y')
localler = {'x': x, "y": y,'dx': dx,'dy': dy, 'e': E, 'E': E, 'exp': exp, 'sin': sin, 'cos': cos, 'tan': tan,'cot': cot,'asin': asin,'acos':acos,'sec' : sec,'csc': csc,'ln' : ln,'log': log,}
#localler.update(locals())
transformations = (standard_transformations + (implicit_multiplication_application,))

init_printing(use_unicode=True) # karakter görsellerinin daha iyi gözükmesini sağlar.

#artık y(x) olarak gözükmez çıktıda y olarak gözükür. log da lne çevrilir.
def y_lnduzelt(expr):
    # Eğer liste ise her elemanı ayrı ayrı işle
    if isinstance(expr, list):
        return [y_lnduzelt(e) for e in expr]

    result = expr.replace(lambda e: isinstance(e, log) and len(e.args) == 1,
                            lambda e: ln(e.args[0]))

    result = result.replace(Derivative(y(x), (x, 4)), Symbol("y''''"))
    result = result.replace(Derivative(y(x), (x, 3)), Symbol("y'''"))
    result = result.replace(Derivative(y(x), (x, 2)), Symbol("y''"))
    result = result.replace(Derivative(y(x), x), Symbol("y'"))
    result = result.subs(y(x), y_s)

    return result


#ln için fonksiyon düzenleme
class ln(log):
    def __str__(self):
        return f"ln({self.args[0]})"

    def _sympystr(self, printer):
        return f"ln({printer.doprint(self.args[0])})"

#dx ve dy çarpanlarını fonksiyonun sağında kalmasını sağlıyor
#daha sonra geliştir sadece katsayısını ve sembolünü girmek yerine girilen bütün denklemlerden dx ve dy yi çarpım durumunda olduğu ifadenin sağına yazdırsın
class DxDyduzelt(Expr):
    def __new__(cls, *args):
        # args = (M, dx, N, dy) veya (M, dx) gibi çiftler halinde
        return Expr.__new__(cls, *args)

    def _pretty(self, printer):
        from sympy.printing.pretty.stringpict import prettyForm
        result = None
        args = list(self.args)

        # İkişerli gruplar halinde işle (katsayı, dx/dy)
        for i in range(0, len(args), 2):     # burada terimlerdi değişken ve katsayısı olarak ikişer ikişer alıyor
            katsayi = args[i]
            sembol = args[i + 1]  # dx veya dy

            kat_pretty = printer._print(katsayi)
            sem_pretty = printer._print(sembol)

            # Katsayıyı parantez içine al
            paran = prettyForm(*kat_pretty.parens())
            # (katsayı)*dx veya (katsayı)*dy
            terim = prettyForm(*paran.right('.', sem_pretty))     # buradaki çarpıma * gösteriyordu bu sorun giderildi

            if result is None:
                result = terim
            else:
                result = prettyForm(*result.right(' + ', terim))

        return result

    def _sympystr(self, printer):        #print için işlemi str olarak yapıyor
        args = list(self.args)
        terimler = []
        for i in range(0, len(args), 2):
            kat = printer.doprint(args[i])
            sem = printer.doprint(args[i + 1])
            terimler.append(f"({kat})*{sem}")
        return " + ".join(terimler)

    def _latex(self, printer):
        args = list(self.args)
        terimler = []
        for i in range(0, len(args), 2):
            kat = printer._print(args[i])
            sem = printer._print(args[i + 1])
            terimler.append(f"\\left({kat}\\right) {sem}")
        return " + ".join(terimler)

def dxdyduzelt(expr):
    A = expr.coeff(dx)  # dx'in katsayısı
    B = expr.coeff(dy)  # dy'nin katsayısı

    if expr.coeff(Derivative(y(x),x)) == 1:
        return expr
    elif A ==0 and B == 0:
        return expr
    elif A ==0 :
        temizhali = DxDyduzelt(B, dy)
        return temizhali
    elif B == 0 :
        temizhali =DxDyduzelt(A, dx)
        return temizhali
    else:
        temizhali = DxDyduzelt(B, dy, A, dx)
        return temizhali

def donusum(expr):
    expr = str(expr)
    expr = expr.replace(' ', '')
    expr = expr.replace('^', '**')
    expr = expr.replace('dy/dx', "y'")
    expr = expr.replace("y''''", '(Derivative(y(x),(x,4)))')
    expr = expr.replace("y'''", '(Derivative(y(x),(x,3)))')
    expr = expr.replace("y''", '(Derivative(y(x),(x,2)))')
    expr = expr.replace("y'",'(Derivative(y(x),(x,1)))')
    expr = expr.replace("dx", "_DX_")
    expr = expr.replace("dy", "_DY_")
    expr = expr.replace("y(x)", "y") # burda bütün y(x) leri y ye çevirmeden y leri y(x) yapsaydık fazladan x çarpanı gelecekti
    expr = expr.replace("y", "y(x)")
    expr = expr.replace("_DX_", "(dx)")#kodda yanına parantezsiz bir çarpan geldiği zaman dy yapısı bozuluyor
    expr = expr.replace("_DY_", "(dy)")#bu yüzden yapıyı bozmadan dy ve dx i ayırmak için parantez koydum

    expr = parse_expr(expr,local_dict=localler, transformations=transformations)#
    return expr

def esittir_duzenleme(expr):
    expr = str(expr)
    if "=" not in expr:
        expr = donusum(expr)
    else:
        sol_denklem1, sag_denklem1 = expr.split("=")
        sol_denklem1 = donusum(sol_denklem1)
        sag_denklem1 = donusum(sag_denklem1)
        expr = (sol_denklem1 - sag_denklem1)
    return expr

#y' olan denklemi dy dx  çevime
def dy_dx_cevirme(expr):
    if "=" in str(expr):
       expr = esittir_duzenleme(expr) #eşittir donuşumde kullanayamayacağı için denklemden eşittiri çıkartıp öyle işleme başladık
    expr = donusum(expr)
    if expr.coeff(Derivative(y(x), x)) != 0:                     #hatalı daha sonra düzenlemeleri yap!!!
        expr = expr * dx
        expr = simplify(expr.subs((Derivative(y(x), x)), dy/dx ))
    return expr

#dy dx olarak verilen denklemi y' olarak çevirme
def yturev_cevirme(expr):
    if "=" in str(expr):
       expr = esittir_duzenleme(expr)
    expr = donusum(expr)
    if expr.coeff(Derivative(y(x), x)) == 0:
        expr = simplify(expr.subs(dy,Derivative(y(x), x)))
        expr = simplify(expr.subs(dx,1))
    return expr

def denk_ayirmax(denklemm):
    xler =''
    denklemm = str(denklemm).replace('/', '*1/')
    denklemm = denklemm.replace('-', '-1*')
    denklemm = denklemm.replace('**', '^')
    parcalar = denklemm.split('*')
    for i in parcalar:
        if 'y(x)' not in str(i):
            xler += str(i) + '*'
    if xler == '':
        return 1
    xler = xler[:-1].replace(' ','')
    xler = xler.replace('^','**')
    return simplify(xler)

def denk_ayirmay(denklemm):
    yler =''
    denklemm=str(denklemm).replace('/','*1/')
    denklemm = denklemm.replace('-', '-1*')
    denklemm = denklemm.replace('**', '^')
    parcalar=denklemm.split('*')
    for i in parcalar:
        if 'y(x)' in str(i):
            yler += str(i) + '*'
    if yler =='':
        return 1
    yler = yler[:-1].replace(' ','')
    yler = yler.replace('^', '**')
    return sympify(yler)

##### HATA analizi

def secenek_al(secenekler,soru): #kullanıcının giridği seçenekleri kontrol etmek için kullanılır
    elemanın_girdigi=input(soru).replace(' ','')
    while True:
        elemanın_girdigi=elemanın_girdigi
        if elemanın_girdigi in secenekler:
            return elemanın_girdigi
        else:
            elemanın_girdigi=input(f"Hatalı giriş yaptınız lütfen sadece şu seçeneklerden birisini seçiniz {'|'.join(secenekler)}: ")

def denklem_kontrol(denk):
    while True:
        try:
            denk1=input(denk)
            if not denk1:
                print("Bu alan boş bırakılamaz")
                #adim_listesi_oku(["Bu alan boş bırakılamaz."])
                continue
            if "=" not in denk1:
                print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 1")
                #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])
                continue
            esittir_sayi=denk1.split("=")
            if len(esittir_sayi)!=2:
                print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 2")
                #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])
                continue
            
            if re.search(r"[a-wA-W_,]y'+|y'+[a-wA-W_,]",denk1):
                print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 3")
                #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])
                continue
            if re.search(r"[a-wA-W_,]d[xy]|d[xy][a-wA-W_,]",denk1):
                print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 4")
                #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])
                continue
            sol_dnek,sag_denk=esittir_sayi
            sol=donusum(sol_dnek)
            sag=donusum(sag_denk)
            denk2 = sol + sag

            dif_terim_var_mi=(denk2.has(dx) or 
                              denk2.has(dx) or 
                              denk2.has(Derivative(y(x),x)) or 
                              denk2.has(Derivative(y(x),(x,2))) or 
                              denk2.has(Derivative(y(x),(x,3))) or
                              denk2.has(Derivative(y(x),(x,4))) or 
                              denk2.has(Derivative(y(x),(x,5)))
                              )
            if not dif_terim_var_mi:
                print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 5")
                #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])
                continue
            return denk1
        except Exception:
            print("Hatalı bir formatta giriş yaptınız tekrar giriş yapınız 6")
            #adim_listesi_oku(["Hatalı bir formatta giriş yaptınız tekrar giriş yapınız"])


pdf_birlestirme_icin=[]  # eğer direk 3 e basıp tam diff çözmek isterse kullanıcı orada pdf birleştirme için tanımlı olmadığı için hata veriyordu o yüzden buraya ekledim.
cozumler3=[] # denklemin çözülebildiği türler
siramiz1=[] #eğer diğer çözüme geçmek isterlerse diye lazım
####
while True:
    if cozumler3 != []:
        del cozumler3[siramiz1.index(int(denklem_turu))]
        siramiz1.remove(int(denklem_turu))
        if cozumler3 != []:
            sırası1=[]
            for tür, sırası in zip (cozumler3, siramiz1):
                sırası1+=str(sırası)
            denklem_turu=secenek_al(sırası1,"Girdiğiniz denklemi"+','.join(f"{tür} ile çözmek için {sırası} tuşuna " for tür, sırası in zip (cozumler3, siramiz1))+"basınız:")

    if cozumler3 ==[]:
        denklem_turu = secenek_al(["1", "2", "3", "4"],"Çözülmesini istediğiniz denklem türünü giriniz\n1. Diferansiyel Denklemin Türünü Öğrenme: \n2. Değişkenlerine Ayrılabilir Diferansiyel Denklem Çözümü:\n3. Tam Diferansiyel Denklem Çözümü: \n4. Tam Hale Gelebilir Diferansiyel Denklem Çözümü:")
        b=5
        if denklem_turu == '1':    #denklem türü hesaplama
            b=0
            denklem1 = denklem_kontrol("Diferansiyel Denkleminizi giriniz: ")
            denklem2=denklem1
                        # pdfte düzgün gözükmesi için
            sol_denklempdf, sag_denklempdf = denklem1.split("=")
            sol_denklempdf=(donusum(sol_denklempdf))
            sag_denklempdf=(donusum(sag_denklempdf))
            denklempdf = y_lnduzelt(Eq(dxdyduzelt(sol_denklempdf), dxdyduzelt(sag_denklempdf), evaluate=False))
            print("Denkleminiz:\n ")
            #_ladimistesi_oku(["girilen diferansiyel denkleminiz: "])
            pprint(denklempdf) #burada girilen denklem söylenebilir.
            #adim_listesi_oku([str(denklempdf)])
            denklem = esittir_duzenleme(denklem1)
            denklem = yturev_cevirme(denklem)
            cozumler =[]
            turkceleri = {
                "separable": " Değişkenlerine ayrılabilir diferansiyel denklem",
                "homogeneous": " Homojen diferansiyel denklem",
                "1st_exact": " Tam diferansiyel denklem",
                "1st_exact_Integral": " Tam hale getirilebilen diferansiyel denklem",
                '1st_linear': ' Lineer diferansiyel denklem',
                "Bernoulli": " Bernoulli tipi diferansiyel denklem",
                "Ricatti": " Riccati diferansiyel denklem",
                "Clairaut": " Clairaut tipi diferansiyel denklem",
                "Liouville": " Liouville  diferansiyel denklem",
                # 'Abel': '-Abel tipi diferansiyel denklem',
                #"linear": "-Genel lineer diferansiyel denklem",
                #"nonlinear": "-lineer  olmayan diferansiyel denklem",
                #"nth_linear_constant_coeff_homogeneous": "-Sabit katsayılı n. dereceden homojen lineer diferansiyel denklem",
                #"reduce_order": "-Mertebesi indirilebilen diferansiyel denklem"

                }

                # bu sayede kendi sözlüğümüzü oluşturduk istediğimiz kelimeleri artık burdan karşılıkları ile değiştirebiliriz

            for t in classify_ode(Eq(donusum(denklem), 0), y(x)):  # classify_ode bizim denklemlerimizi sınıflandırır
                if t in turkceleri:
                    cozumler.append(turkceleri[t])
                if not " Tam hale getirilebilen diferansiyel denklem" in cozumler:
                    denklem=denklem2
                    sol_denklem, sag_denklem = denklem.split("=")
                    denklem = esittir_duzenleme(denklem)
                    if denklem.coeff(Derivative(y(x), x)) !=0:
                        yt_katsayi = denklem.coeff(Derivative(y(x), x))
                        denklem = denklem - (yt_katsayi * (Derivative(y(x), x)))
                        denklem = -denklem / yt_katsayi
                        pay, payda = denklem.as_numer_denom()
                        dxkat=-pay
                        dykat=payda
                    else:
                        dxkat=denklem.coeff(dx)
                        dykat=denklem.coeff(dy)
                        tdd_denk = y_lnduzelt(dxdyduzelt(dxkat*dx + dykat*dy))
                    dxkat=dxkat.subs(y(x),y_s)
                    dykat=dykat.subs(y(x),y_s)
                    My = diff(dxkat,y_s)
                    Nx = diff(dykat,x)
                    if simplify((My-Nx)/((y_s*dykat)-(x*dxkat)))!=0:
                        z=symbols('z')
                        degisken_degis=simplify((My-Nx)/((y_s*dykat)-(x*dxkat))).subs(y_s*x,z)
                        if degisken_degis.free_symbols <={z}:
                            cozumler.append(" Tam hale getirilebilen diferansiyel denklem")
            if len(cozumler)==0:
                print("\nGirdiğiniz denklem hiç bir adi diferansiyel formuna uymamaktadır.")
                #adim_listesi_oku(["Girdiğiniz denklem hiç bir adi diferansiyel formuna uymamaktadır."])
            else:
                elimizdeki_turler=[" Değişkenlerine ayrılabilir diferansiyel denklem", " Tam diferansiyel denklem", " Tam hale getirilebilen diferansiyel denklem"]
                cozumler2=""
                cozumler3=[]
                siramiz1=[]
                sol_denklem, sag_denklem = denklem1.split("=")
                denklem1 = esittir_duzenleme(denklem1)
                if denklem1.coeff(Derivative(y(x), x)) == 1:
                    #tdd_girdi = y_lnduzelt(Eq(donusum(sol_denklem), donusum(sag_denklem)))
                    yt_katsayi = denklem1.coeff(Derivative(y(x), x))  # y' nin katsayısını al
                    denklem1 = denklem1 - (yt_katsayi * (Derivative(y(x), x)))  # y' dışındakileri karşıya at
                    denklem1 = -denklem1 / yt_katsayi  # şu an y'=denklem olarak durmakta
                    pay, payda = denklem1.as_numer_denom()
                    dxkat = -pay
                    dykat = payda
                else:
                    dxkat = denklem1.coeff(dx)  # M(x,y)
                    dykat = denklem1.coeff(dy)  # N(x,y)
                dxkat = dxkat.subs(y(x), y_s)
                dykat = dykat.subs(y(x), y_s)
                My = diff(dxkat, y_s)
                Nx = diff(dykat, x)

                for t1 in elimizdeki_turler:

                    if t1 in cozumler:
                        cozumler1=t1
                        cozumler2+=t1 + '\n'
                        cozumler3+=[t1]
                        siramiz=(elimizdeki_turler.index(cozumler1))
                        siramiz1+=[siramiz+2]
                if My!=Nx:

                    if " Tam diferansiyel denklem" in cozumler3:
                        cozumler3.remove(" Tam diferansiyel denklem")
                        siramiz1.remove(3)
                else:
                    if " Tam hale getirilebilen diferansiyel denklem" in cozumler3:
                        cozumler3.remove(" Tam hale getirilebilen diferansiyel denklem")#elimizdeki turlerden değil cozumlerdenn çıkartmamız gerekiyordu
                        siramiz1.remove(4)
                aciklama= {}
                if " Değişkenlerine ayrılabilir diferansiyel denklem" in cozumler3:
                    denklem = esittir_duzenleme(denklem2)
                    if denklem.coeff(Derivative(y(x), x)) == 0:
                        kat_dx = denklem.coeff(dx)
                        kat_dy = denklem.coeff(dy) # artık tek tek denklemin katsayılarını sormak yerine istediğimiz denklemi direk girebiliyoruz
                        print('\nÇözüm :\n\n     -Denklemin dy\'li tarafını y\'ye ve dx olan tarafını x\'e göre düzenleyelim\n')
                        #adim_listesi_oku(["Birinci adım. Denklemin de ye li tarafını ye ye ve de ix olan tarafını ix e göre düzenleyelim."])
                        aa = denk_ayirmay(kat_dy)
                        ab = denk_ayirmay(kat_dx)   #y ye ve x'e bağlı çarpanları ayırmak için kullandım
                        ba = denk_ayirmax(kat_dx)
                        bb = denk_ayirmax(kat_dy)
                        y_bagli=aa/ab
                        x_bagli=-1*ba/bb
                    else:
                        denklem = esittir_duzenleme(denklem)
                        y_katsayi = denklem.coeff(Derivative(y(x), x))
                        denklem = denklem - (y_katsayi * (Derivative(y(x), x)))
                        denklem = -denklem / y_katsayi
                        x_bagli = denk_ayirmax(denklem)
                        y_bagli = 1/denk_ayirmay(denklem)
                    dadd_dxdyduzen = y_lnduzelt(Eq(dxdyduzelt(y_bagli*dy), dxdyduzelt(x_bagli*dx),evaluate=False))
                    duzgun_dadd=pretty(dadd_dxdyduzen)
                    aciklama[" Değişkenlerine ayrılabilir diferansiyel denklem"]=f"\nDüzenlenmiş hali:\n{duzgun_dadd}\n\n Girilen denklem F(y)dy = H(x)dx formuna uyduğu için Değişkenlerine Ayrılabilir Diferansiyel Denklemdir"
                if " Tam diferansiyel denklem" in cozumler3:
                    aciklama[" Tam diferansiyel denklem"]= f"\n\nDenklemin genel formu M(x,y)dx+N(x,y)dy=0 formuna uymaktadır\nM(x,y) = {dxkat} ve N(x,y) = {dykat} \n\nM(x,y)'nin y'ye göre türevi My = {My} ve N(x,y)'nin x'e göre türevi Nx = {Nx} My=Nx şeklinde olduğundan Tam Diferansiyel Denklem"
                if " Tam hale getirilebilen diferansiyel denklem" in cozumler3:
                    if simplify((My-Nx)/dykat).free_symbols <= {x}:
                        thg_x = y_lnduzelt(simplify((My-Nx)/dykat))
                        thg_ex=y_lnduzelt(exp(integrate(thg_x,x)))  
                        aciklama[" Tam hale getirilebilen diferansiyel denklem"]=f"\nDenklemin genel formu M(x,y)dx+N(x,y)dy=0 formuna uymaktadır\nM(x,y) = {dxkat} ve N(x,y) = {dykat} \n\nM(x,y)'nin y'ye göre türevi My = {My} ve N(x,y)'nin x'e göre türevi Nx = {Nx} My Nx'e eşit olmadığı için tam diferansiyel denkelm değildir.\n\nM(x,y) ve N(x,y) değerlerini integral çarpanı ile çarparsak denklemimizi tam diferansiyel denklem haline getirebiliriz."
                    elif simplify((Nx - My) / dxkat).free_symbols <= {y_s}:
                        thg_y = y_lnduzelt(simplify((Nx - My) / dxkat))
                        thg_ey = y_lnduzelt(exp(integrate(thg_y, y_s)))
                        aciklama[" Tam hale getirilebilen diferansiyel denklem"]=f"\nDenklemin genel formu M(x,y)dx+N(x,y)dy=0 formuna uymaktadır\nM(x,y) = {dxkat} ve N(x,y) = {dykat} \n\nM(x,y)'nin y'ye göre türevi My = {My} ve N(x,y)'nin x'e göre türevi Nx = {Nx} My Nx'e eşit olmadığı için tam diferansiyel denklem değildir.\n\nM(x,y) ve N(x,y) değerlerini integral çarpanı ile çarparsak denklemizi tam diferansiyel denklem haline getirebiliriz."
                    elif simplify((My-Nx)/((y_s*dykat)-(x*dxkat)))!=0:
                        thg_z= y_lnduzelt(simplify((My-Nx)/((y_s*dykat)-(x*dxkat))).subs(y_s*x,z))
                        thg_xy= y_lnduzelt(simplify((My-Nx)/((y_s*dykat)-(x*dxkat))))
                        thg_ez= y_lnduzelt(exp(integrate(thg_z,z)))
                        thg_exy= thg_ez.subs(z,y_s*x)
                        aciklama[" Tam hale getirilebilen diferansiyel denklem"]=f"Denklemin genel formu M(x,y)dx+N(x,y)dy=0 formuna uymaktadır\nM(x,y) = {dxkat} ve N(x,y) = {dykat} \n\nM(x,y)'nin y'ye göre türevi My = {My} ve N(x,y)'nin x'e göre türevi Nx = {Nx} My Nx'e eşit olmadığı için tam diferansiyel denklem değildir.\n\nM(x,y) ve N(x,y) değerlerini integral çarpanı ile çarparsak denklemimizi tam diferansiyel denklem haline getirebiliriz."

                for tur in cozumler3:
                    print(f"{aciklama[tur]}")

                adimlar_listesi=[]
                adimlar_listesi.append("Girdiğiniz Denklem:")
                adimlar_listesi.append(denklempdf)
                adimlar_listesi.append("Diferansiyel denkleminizin türleri:")
                adimlar_listesi.append(str(cozumler3))# buralar düzenlenecek

                if len(cozumler3)==1:  #denklem türünü ve seçenekler
                    denklem_turu=secenek_al([f"{siramiz1[0]}"],f"\nGirdiğiniz deklemin türü {','.join(cozumler3)} çözmek istiyorsanız şu tuşa basınız {siramiz1[0]}: ")
                elif len(cozumler3)>1:
                    sırası1=[]
                    for tür, sırası in zip (cozumler3, siramiz1):
                        sırası1+=str(sırası)
                    denklem_turu=secenek_al(sırası1,"\nGirdiğiniz denklemi"+','.join(f"{tür} ile çözmek için {sırası} tuşuna " for tür, sırası in zip (cozumler3, siramiz1))+"basınız:")

            # --- pdf çıktısı---
                raporiceriği = []
                pdf_birlestirme_icin = tur_bulma_pdf(denklem, cozumler3, raporiceriği, y_lnduzelt, dxdyduzelt,  denk_ayirmay, denk_ayirmax)

    if denklem_turu == '2':  #değişkenlerine ayrılabilir diferansiyel denklem
        if b==5:
            al_denklem=denklem_kontrol("Diferansiyel denkleminizi giriniz: ")
            sol_denklem, sag_denklem = al_denklem.split("=")
            print("Denkleminiz:\n")
            #adim_listesi_oku(["Denkleminiz: "])
            pprint(y_lnduzelt(Eq(dxdyduzelt(donusum(sol_denklem)),dxdyduzelt(donusum(sag_denklem))))) # buradaki dx dyleri de düzeltmeyi öğren. y' ni de buraya ekle class için
            #adim_listesi_oku([Eq(donusum(sol_denklem),donusum(sag_denklem))])

            denklem = esittir_duzenleme(al_denklem)
    #buradaki if ve elsenin sebebi denklem dx_dy şeklinde çözüldüğü için y' olarak verilirse dx_dy çevirmemiz ama iki türüde uzun uzun kodlamak yerine aynı adıma gelecekleri yere kadar ayırdım sonraki adımları beraber ilerliyor
            if denklem.coeff(Derivative(y(x), x)) == 0: # denklem dx dy şeklindeyse
                kat_dx = denklem.coeff(dx)
                kat_dy = denklem.coeff(dy) # artık tek tek denklemin katsayılarını sormak yerine istediğimiz denklemi direk girebiliyoruz

                print('\n\n     -Denklemin dy\'li tarafını y\'ye ve dx olan tarafını x\'e göre düzenleyelim\n')
                #adim_listesi_oku(["Birinci adım. Denklemin de ye li tarafını ye ye ve de ix olan tarafını ix e göre düzenleyelim."])

                aa = denk_ayirmay(kat_dy)
                ab = denk_ayirmay(kat_dx)   #y ye ve x'e bağlı çarpanları ayırmak için kullandım
                ba = denk_ayirmax(kat_dx)
                bb = denk_ayirmax(kat_dy)
                y_bagli=aa/ab
                x_bagli=-1*ba/bb
                #print(gcd(y_bagli,x_bagli))
                dadd_dxdyduzen = y_lnduzelt(Eq(dxdyduzelt(y_bagli*dy), dxdyduzelt(x_bagli*dx),evaluate=False))
                pprint(dadd_dxdyduzen)   # burada DxDy girince sıkıntı oluyor bu düzeltilecek  hata düzeltildi
                #adim_listesi_oku([str(dadd_dxdyduzen)])

            else :
                print('\n\n  -Denklemimizi F(y)dy = H(x)dx olarak düzenleyelim.\n')
                #adim_listesi_oku(["Birinci adım. Denklemimizi fe ix ye, de ye eşittir he ix ye, de ix olarak düzenleyelim."])

                denklem = esittir_duzenleme(denklem)  # denklemi tek tarafa topla
                y_katsayi = denklem.coeff(Derivative(y(x), x))  # y' nin katsayısını al
                denklem = denklem - (y_katsayi * (Derivative(y(x), x)))  # y' dışındakileri karşıya at
                denklem = -denklem / y_katsayi  # y' nin katsayısına böl
                #bu şekilde y' şeklinde yazılan bir denklemi dx_dy olarak ayırabiliyoruz

                x_bagli = denk_ayirmax(denklem)
                y_bagli = 1/denk_ayirmay(denklem)
                dadd_dxdyduzen = y_lnduzelt(Eq(dxdyduzelt(y_bagli*dy), dxdyduzelt(x_bagli*dx),evaluate=False))
                pprint(dadd_dxdyduzen)
                #adim_listesi_oku([str(dadd_dxdyduzen)])
        else:
            al_denklem=denklem2
        print('\n\n     -İki tarafında integralini alalım.\n')
        #adim_listesi_oku(["İkinci adım. İki tarafında integralini alalım."])


        Fx = integrate( x_bagli, x) # dx'in katsayısının x'e göre integrali
        Fy = integrate(y_bagli, y(x)) #dy'nin katsayısının y'ye göre integrali
        dadd_int=y_lnduzelt(Eq(Fy, Fx + C1))
        pprint(dadd_int)
        #adim_listesi_oku([str(dadd_int)])

        print('\n\n     -Denklemi kapalı form olarak düzenleyelim\n')  # sanırım karmaşık denklemlerde y eşittir olarak yazamıyor bunu araştır ve ona göre bir hata düzenleme bul
        #adim_listesi_oku(["Üçüncü adım. Denklemi ye eşittir olarak düzenleyelim."])
        dadd_ciktisi= y_lnduzelt(Eq(Add(Fy,-Fx,C,evaluate=False),0,evaluate=False))#Add ile toplamayı sıraya sokamıyorum C en sonda oluyor
        pprint(dadd_ciktisi)
        #adim_listesi_oku([str(y_lnduzelt(dadd_ciktisi))])
        print("\nÇözüm tamamlandı!")
        #adim_listesi_oku(["Çözüm tamamlandı."])
        # --- pdf çıktısı---
        dadd_pdf(al_denklem, dadd_dxdyduzen, dadd_int, dadd_ciktisi,pdf_birlestirme_icin)


    if denklem_turu == '3' or denklem_turu== '4': #Tam diferansiyel denklem

        adimlar_listesi=[]
        if b==5:
            denklem=denklem_kontrol("Diferansiyel denklemi giriniz: ")
            #adim_listesi_oku(["Denkleminiz: "])
            sol_denklempdf, sag_denklempdf = denklem.split("=")
            sol_denklempdf = (donusum(sol_denklempdf))
            sag_denklempdf = (donusum(sag_denklempdf))
            denklempdf = y_lnduzelt(Eq(dxdyduzelt(sol_denklempdf), dxdyduzelt(sag_denklempdf), evaluate=False))
            print("Denkleminiz: \n")
            pprint(denklempdf)  # burada girilen denklem söylenebilir.
            #adim_listesi_oku([str(y_lnduzelt(denklempdf))])
        else:
            denklem=denklem2

        sol_denklem, sag_denklem = denklem.split("=")
        denklem = esittir_duzenleme(denklem)

        if denklem.coeff(Derivative(y(x), x)) !=0:
            #tdd_girdi = y_lnduzelt(Eq(donusum(sol_denklem), donusum(sag_denklem)))
            yt_katsayi = denklem.coeff(Derivative(y(x), x))  # y' nin katsayısını al
            denklem = denklem - (yt_katsayi * (Derivative(y(x), x)))  # y' dışındakileri karşıya at
            denklem = -denklem / yt_katsayi  # şu an y'=denklem olarak durmakta
            pay, payda = denklem.as_numer_denom()
            dxkat=-pay
            dykat=payda

            print("-Öncelikle denklemimizi M(x,y)dx + N(x,y)dy = 0 olarak yazalım.")
            #adim_listesi_oku(["Öncelikle denklemimizi Me ix ye, de ix artı Ne ix ye, de ye eşittir sıfır olarak yazalım."])
            tdd_denk=y_lnduzelt(dxdyduzelt(dxkat*dx + dykat*dy))
            pprint(Eq(tdd_denk,0))
            #adim_listesi_oku([str(Eq(tdd_denk,0))])


        else:
            dxkat=denklem.coeff(dx) # M(x,y)
            dykat=denklem.coeff(dy) # N(x,y)
            tdd_denk = y_lnduzelt(dxdyduzelt(dxkat*dx + dykat*dy))

        if b==5:
            print('\n\n     -Denklemimizin Tam Diferansiyel olup olmadığını kontrol edelim ')
            print('\n\n     -Denklemimizin Tam Diferansiyel olması için My = Nx olmalı \n\n')
        #adim_listesi_oku(["Birinci adım. Denklemimizin Tam Diferansiyel olup olmadığını kontrol edelim. Denklemimizin tam diferansiyel olması için, M(y) eşittir N(x) olmalı."])
        dxkat=dxkat.subs(y(x),y_s)
        dykat=dykat.subs(y(x),y_s)
        My = diff(dxkat,y_s)
        Nx = diff(dykat,x)
                                                            #tam diff olup olmadığını kontrol aşaması
        if My == Nx:

            tdd_kontrol=y_lnduzelt(Eq(My, Nx, evaluate=False))

            satirlar=pretty(My).split('\n')
            orta=len(satirlar)//2
            satirlar[orta]='My = '+satirlar[orta]
            print('\n'.join(satirlar))
            #adim_listesi_oku(["Me ye eşittir " + str(y_lnduzelt(My))])

            satirlar=pretty(Nx).split('\n')
            orta=len(satirlar)//2
            satirlar[orta]='Nx = '+satirlar[orta]
            print('\n'.join(satirlar))
            #adim_listesi_oku(["Ne ix eşittir " + str(y_lnduzelt(Nx))])

            print('\n     My = Nx olduğuna göre Denklem Tam Diferansiyeldir')
            #adim_listesi_oku(["Me ye eşittir Ne ix olduğuna göre denklem tam diferansiyeldir."])
            print(f'\n\n\n\n     -F(x,y) = C  çözüm olsun o halde : \n\n          1) əF/əX = M(x,y)       ve          2) əF/əY = N(x,y)')
            #adim_listesi_oku(["İkinci adım. Fe ix ye eşittir Ce çözüm olsun o halde Birinci seçenek: Fe nin ix e göre kısmi türevi eşittir Me ix ye'yi kullanarak çözmek."])
            #adim_listesi_oku(["İkinci seçenek: Fe nin ye ye göre kısmi türevi eşittir Ne ix ye'yi kullanarak çözmek."])
            print(f'\n  1) əF/əX = {y_lnduzelt(dxkat)}   ve  2) əF/əY = {y_lnduzelt(dykat)}')
            #adim_listesi_oku([f"Birinci seçenek: Fe nin ix e göre kısmi türevi eşittir {y_lnduzelt(dxkat)}. İkinci seçenek: Fe nin ye ye göre kısmi türevi eşittir {y_lnduzelt(dykat)}."])
            print("\nŞimdi F(x,y)'yi yanlız bırakalım ")
            #adim_listesi_oku(["Şimdi Fe ix ye yi yalnız bırakalım]."])

            F = symbols('F')
            H = Function("H")
            print(f"\n 1) əF / əX = {y_lnduzelt(dxkat)} her iki tarafın x'e göre integralini alalım")
            #adim_listesi_oku([f"Birinci denklemi çözelim: Fe nin ix e göre kısmi türevi eşittir {y_lnduzelt(dxkat)}. Her iki tarafın ix e göre integralini alalım."])
            M_intx = integrate(dxkat,x)
            tdd_a1=y_lnduzelt(Eq(F, Add(simplify(M_intx), H(y_s), evaluate=False)))
            pprint(tdd_a1)# Add toplama işlemidir sırası değişmeden toplatır evulation folse ise toplamları birleştirtmez
            #adim_listesi_oku([str(tdd_a1)])
            print("    \n H(y)'yi bulmak bunun için y'e göre türev alarak N(x,y)'ye eşitleyeceğiz ")
            #adim_listesi_oku(["Üçüncü adım. He ye yi bulmak. Bunun için ye ye göre türev alarak ikinci denkleme eşitleyeceğiz."])
            M_diffy = diff(M_intx, y_s)
            print("əF / əY = ", y_lnduzelt(M_diffy), " + H'(y)")
            #adim_listesi_oku(["Fe nin ye ye göre kısmi türevi eşittir " + str(y_lnduzelt(M_diffy)) + " artı he türev ye."])
            print("N(x,y)'i yerine yerleştirip H'(y) i yalnız bırakalım:")
            #adim_listesi_oku(["İkinci denklemi yerine yerleştirip He türev ye yi yalnız bırakalım."])
            Hy = y_lnduzelt(simplify(dykat - M_diffy))
            print(f"H'(y) = {Hy}")
            #adim_listesi_oku([f"He türev ye eşittir {Hy}"])
            print("\n Her iki tarafında y'ye göre integralini alalım: ")
            #adim_listesi_oku(["Her iki tarafında ye'ye göre integralini alalım."])
            Hy = y_lnduzelt(integrate(Hy, y_s))
            print(f'H(y) = {Hy + C}')
            #adim_listesi_oku([f"He ye eşittir Ce artı  {Hy}"]) # burada hy - li ılunca artı eksi diye okuyor düzeltilecek
            tdd_cevap=y_lnduzelt(Eq(F, M_intx + Hy, evaluate=False))
            pprint(tdd_cevap)
            #adim_listesi_oku([str(tdd_cevap)])

            F = symbols('F')
            print(f"\n\n\n 2) əF / əY = {y_lnduzelt(dykat)} iki tarafınıda y'e göre integralini alalım")
            #adim_listesi_oku([f"İkinci denklemi çözelim: Fe nin ye ye göre kısmi türevi eşittir {y_lnduzelt(dykat)}. Her iki tarafın ye ye göre integralini alalım."])
            N_inty = y_lnduzelt(integrate(dykat, y_s))
            pprint(f"F = {N_inty} + H(x) ")
            #adim_listesi_oku([f"Fe eşittir {N_inty} artı He ix"])
            print("    -\n H(x)'i bulmak için x'e göre türev alarak M(x,y)'ye eşitleyeceğiz\n ")
            #adim_listesi_oku([f"Üçüncü adım. He ix i bulmak, bunun için ix e göre türev alarak birinci denkleme eşitleyeceğiz."])
            N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
            print("əF / əX = ", N_diffx, " + H'(x)")#əF / əY əF / əX oldu
            #adim_listesi_oku(["Fe nin ix e göre kısmi türevi hesaplandı."])
            print("M(x,y)'i yerine yerleştirip H'(x) i yalnız bırakalım:")#N(x,y) M(x,y) oldu
            #adim_listesi_oku(["İkinci denklemi yerine yerleştirip He nin ix e göre türevini yalnız bırakalım."])
            Hx = y_lnduzelt(simplify(dxkat - N_diffx))
            print(f"H'(x) = {Hx}")
            #adim_listesi_oku([f"He türev ix eşittir {Hx}"])
            print("\n her iki tarafında x'e göre integralini alalım: ")
            #adim_listesi_oku(["Her iki tarafın ix e göre integralini alalım."])
            Hx = y_lnduzelt(integrate(Hx, x))
            print(f'H(x) = {Hx}')
            #adim_listesi_oku([f"He ix eşittir {Hx}"])
            print("F = ")
            #adim_listesi_oku(["Fe eşittir"])
            tdd_cevap= y_lnduzelt(Eq(N_inty + Hx, C, evaluate=False))
            pprint(tdd_cevap)
            #adim_listesi_oku([str(tdd_cevap)])

            print(f"\n\nBulduğumuz ilk çözüm, {y_lnduzelt(expand(M_intx + Hy))}, ikinci çözüm, {y_lnduzelt(expand(N_inty + Hx))} olduğundan her iki yolda bizi aynı çözüme götürüyor\n\n") #cümlenin sonundaki çözüm çözüme olarak değiştirilecek
            #adim_listesi_oku([f"Bulduğumuz ilk çözüm {y_lnduzelt(M_intx + Hy)} , ikinci çözüm {y_lnduzelt(N_inty + Hx)} olduğundan, her iki yolda bizi aynı çözüm götürüyor."])
    #                        ----pdf çıktısı---

            tdd_pdf(denklempdf, dxkat, dykat, My, Nx, adimlar_listesi, zaman_etiketi, pdf_birlestirme_icin)
        else: #tam hale gelebilir kısım
            if b==5:
                satirlar=pretty(y_lnduzelt(My)).split('\n')
                orta=len(satirlar)//2
                satirlar[orta]='My='+satirlar[orta]
                print('\n'.join(satirlar))
                #adim_listesi_oku(["Me ye eşittir " + str(y_lnduzelt(My)) ])

                satirlar=pretty(Nx).split('\n')
                orta=len(satirlar)//2
                satirlar[orta]='Nx='+satirlar[orta]
                print('\n'.join(satirlar))
                #adim_listesi_oku(["Ne ix  eşittir " + str(y_lnduzelt(Nx)) ])

                print(f'My ve Nx birbirine eşit olmadığından denkleminiz Tam diferansiyel değildir. Denklemi tam hale getirebilmek için integral çarpanına ihtiyaç duyarız bu çarpanı belirlemek için 3 durum söz konusudur.')
                #adim_listesi_oku(["Me ye ve Ne ix birbirine eşit olmadığından denkleminiz tam diferansiyel değildir."])
                #adim_listesi_oku(["Denklemi Tam hale getirebilmek için integral çarpanına ihtiyaç duyarız bu çarpanı belirlemek için 3 durum söz konusudur."])
                print("1. Durum: sadece x'e bağlı interal çarpan (My-Nx)/N(x,y) = f(x) ise e^∫f(x)dx şeklindedir.")#(Nx-My)/M(x,y) = f(y) ise e^∫f(y)dy şeklindedir. ifadesi (My-Nx)/N(x,y) = f(x) ise e^∫f(x)dx şeklindedir. şeklinde değiştirilmiştir
                print("2. Durum: sadece y'ye bağlı interal çarpan (Nx-My)/M(x,y) = f(y) ise e^∫f(y)dy şeklindedir.")
                #adim_listesi_oku(["İkinci durum: sadece ye ye bağlı integral çarpan, Ne ix eksi Me ye bölü Me eşittir fe ye ise e üzeri integral, fe ye, de ye şeklindedir."])
                print("3. Durum: hem x'e hem y'ye bağlı integral çarpan (My-Nx)/(yN(x,y)-xM(x,y)) = f(x,y) ise e^∫f(x,y) dxdy şeklindedir.\n")
                #adim_listesi_oku(["Üçüncü durum: hem ix e hem ye ye bağlı integral çarpan, Me ye eksi Ne ix bölü, ye çarpı Ne eksi ix çarpı Me eşittir, f ix ye ise e üzeri çift integral, f ix ye, de ix de ye şeklindedir."])
            if simplify((My-Nx)/dykat).free_symbols <= {x}:
                if b==5:
                    thg_x = y_lnduzelt(simplify((My-Nx)/dykat))
                    thg_ex=y_lnduzelt(exp(integrate(thg_x,x)))
                    print(f"Burada (My-Nx)/N(x,y) = ({My}-{Nx})/{dykat} = {thg_x} x'e bağlı olduğundan integral çarpanımız {thg_ex} şeklindedir.")
                    #adim_listesi_oku([f"Burada Me ye eksi Ne ix bölü Ne eşittir {thg_x} ix e bağlı olduğundan integral çarpanımız {thg_ex} şeklindedir."])
                print(f"\n(My-Nx)/N(x,y) = ({My}-{Nx})/{dykat} = {thg_x} x'e bağlı olduğundan integral çarpanımız {thg_ex} şeklindedir.")
                print(f"\nM(x,y) ve N(x,y) değerlerini {thg_ex} ile çarparsak denklemimiz tam diferansiyel hale gelir. \n Denklemimiz: \n")
                #adim_listesi_oku([f"Me ix ye ve Ne ix ye değerlerini {thg_ex} ile çarparsak denklemimiz tam diferansiyel hale gelir. Denklemimiz:"])
                thg_dx_kat = dxkat * thg_ex
                thg_dy_kat = dykat * thg_ex
                thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
                pprint(thgmis)  # integral çarpanı eklenecek ve diğer 2 durum oluşturulacak
                #adim_listesi_oku([str(y_lnduzelt(thgmis))])

            elif simplify((Nx - My) / dxkat).free_symbols <= {y_s}:
                if b==5:
                    thg_y = y_lnduzelt(simplify((Nx - My) / dxkat))
                    thg_ey = y_lnduzelt(exp(integrate(thg_y, y_s)))
                    print(f"Burada (Nx-My)/M(x,y) = ({Nx}-{My})/{dxkat} = {thg_y} y'e bağlı olduğundan integral çarpanımız {thg_ey} şeklindedir.")
                    #adim_listesi_oku([f"Burada Me ye eksi Ne ix bölü Ne eşittir {thg_y} ye ye bağlı olduğundan integral çarpanımız {thg_ey} şeklindedir."])
                print(f"\n(Nx-My)/M(x,y) = ({Nx}-{My})/{dxkat} = {thg_y} y'e bağlı olduğundan integral çarpanımız {thg_ey} şeklindedir")
                print(f"\nM(x,y) ve N(x,y) değerlerini {thg_ey} ile çarparsak denklemizim tam diferansiyel hale gelir. \n Denklemimiz: \n")
                #adim_listesi_oku([f"Me ix ye ve Ne ix ye değerlerini {thg_ey} ile çarparsak denklemimiz tam diferansiyel hale gelir. Denklemimiz:"])
                thg_dx_kat = dxkat * thg_ey
                thg_dy_kat = dykat * thg_ey
                thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
                pprint(thgmis)  # integral çarpanı eklenecek ve diğer 2 durum oluşturulacak
                #adim_listesi_oku([str(y_lnduzelt(thgmis))])

            elif simplify((My-Nx)/((y_s*dykat)-(x*dxkat)))!=0:
                z=symbols('z')
                degisken_degis=simplify((My-Nx)/((y_s*dykat)-(x*dxkat))).subs(y_s*x,z)
                if degisken_degis.free_symbols <={z}:
                    if b==5:
                        thg_z= y_lnduzelt(simplify((My-Nx)/((y_s*dykat)-(x*dxkat))).subs(y_s*x,z))
                        thg_xy= y_lnduzelt(simplify((My-Nx)/((y_s*dykat)-(x*dxkat))))
                        thg_ez= y_lnduzelt(exp(integrate(thg_z,z)))
                        thg_exy= thg_ez.subs(z,y_s*x)
                        print(f"Burada (My-Nx)/(yN(x,y)-xM(x,y)) = {(My-Nx)/((y_s*dykat)-(x*dxkat))} = {thg_xy} xy'ye bağlı, integli alabilmek için xy = z diyeceğiz, buradan integral çarpanı {thg_ez} bulunur")
                    print(f"\nBurada (My-Nx)/(yN(x,y)-xM(x,y)) = {(My-Nx)/((y_s*dykat)-(x*dxkat))} = {thg_xy} xy'ye bağlı, integli alabilmek için xy = z diyeceğiz, buradan integral çarpanı {thg_ez} şeklindedir")
                    print(f"\nxy değerlerimizi tekrar yerine koyarsak integral çarpanımız {thg_exy} şeklindedir\n")
                    thg_dx_kat = dxkat * thg_exy
                    thg_dy_kat = dykat * thg_exy
                    thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
                    pprint(thgmis)


            print('\n     -Denklemimizin Tam Diferansiyel olamsı için My = Nx olmalı ')
            #adim_listesi_oku(["Denklemimizin tam diferansiyel olması için, Me ye eşittir Ne ix olmalı."])
            My = simplify(diff(thg_dx_kat, y_s))
            print(f"{My}")
            Nx = simplify(diff(thg_dy_kat, x))
            print(f"{Nx}")
            # tam diff olup olmadığını kontrol aşaması
            if My == Nx:

                tdd_kontrol = y_lnduzelt(Eq(My, Nx, evaluate=False))
                print(f"My= {y_lnduzelt(My)}")
                #adim_listesi_oku([f"Me nin ye ye göre türevi eşittir {y_lnduzelt(My)} olarak hesaplandı."])
                print(f"Nx= {y_lnduzelt(Nx)}")
                #adim_listesi_oku([f"Ne nin ix e göre türevi eşittir {y_lnduzelt(Nx)} olarak hesaplandı."])
                pprint(tdd_kontrol)  # bu sayede Eq denklemi çözmez nesne olarak bırakır
                #adim_listesi_oku([f"Me ye eşittir Ne ix, {y_lnduzelt(My)} eşittir {y_lnduzelt(Nx)}"])
                print('\n     My = Nx oludğu için denklem Tam Diferansiyeldir')
                #adim_listesi_oku([f"Me ye eşittir Ne ix olduğu için denklem tam diferansiyeldir."])
                print(f' \n\n     -F(x,y) = C  çözüm olsun o halde : \n\n          1) əF/əX = M(x,y)       ve          2) əF/əY = N(x,y)')
                #adim_listesi_oku(["Fe ix ye eşittir Ce çözüm olsun o halde. İki seçeneğimiz var. "])
                #adim_listesi_oku(["Birinci seçenek: Fe nin ix e göre kısmi türevi eşittir Me ix ye'yi kullanarak çözme. "])
                #adim_listesi_oku(["İkinci seçenek: Fe nin ye ye göre kısmi türevi eşittir Ne ix ye'yi kullanarak çözme ."])
                print(f'\n  1) əF/əX = {y_lnduzelt(thg_dx_kat)}   ve  2) əF/əY = {y_lnduzelt(thg_dy_kat)}')
                #adim_listesi_oku([f"Birinci seçenek: Fe nin ix e göre kısmi türevi eşittir {y_lnduzelt(dxkat)}. "])
                #adim_listesi_oku([f"İkinci seçenek: Fe nin ye ye göre kısmi türevi eşittir {y_lnduzelt(dykat)}."])
                print("\n Şimdi F(x,y)'yi yanlız bırakalım")
                #adim_listesi_oku(["Fe ix ye yi yalnız bırakalım."])


                F = symbols('F')
                H = Function("H")
                print(f"\n 1) əF / əX = {y_lnduzelt(thg_dx_kat)} iki tarafında x'e göre integralini alalım")
                #adim_listesi_oku([f"Birinci seçenek: Fe nin ix e göre kısmi türevi eşittir {y_lnduzelt(dxkat)}. Her iki tarafında ix e göre integralini alalım."])

                M_intx = integrate(thg_dx_kat, x)
                tdd_a1 = y_lnduzelt(Eq(F, dxdyduzelt(Add(simplify(M_intx), H(y_s), evaluate=False))))
                pprint(tdd_a1)  # Add toplama işlemidir sırası değişmeden toplatır evulation folse ise toplamları birleştirtmez
                #adim_listesi_oku([str(tdd_a1)])
                print("H(y)'yi bulmak bunun için y'e göre türev alarak N(x,y)'ye eşitleyeceğiz ")
                #adim_listesi_oku(["He ye yi bulmak bunun için ye'ye göre türev alarak ikinci denkleme eşitleyeceğiz"])
                M_diffy = diff(M_intx, y_s)
                print("əF / əY = ", y_lnduzelt(M_diffy), " + H'(y)")
                #adim_listesi_oku(["Fe nin ye'ye göre kısmi türevi eşittir " + str(y_lnduzelt(M_diffy)) + " artı He türev ye."])
                print("N(x,y)'yi yerine yerleştirip H'(y) i yalnız bırakalım:")
                #adim_listesi_oku(["İkinci denklemi yerine yerleştirip He türev ye'yi yalnız bırakalım."])
                Hy = y_lnduzelt(simplify(thg_dy_kat - M_diffy))
                print(f"H'(y) = {Hy}")
                #adim_listesi_oku([f"He türev ye eşittir {y_lnduzelt(Hy)} olarak bulundu."])
                print("\n her iki tarafında y'ye göre integralini alalım: ")
                #adim_listesi_oku(["Her iki tarafın ye'ye göre integralini alalım."])
                Hy = y_lnduzelt(integrate(Hy, y_s))
                print(f'H(y) = {Hy + C}')
                #adim_listesi_oku([f"He ye eşittir {y_lnduzelt(Hy)} artı Ce olarak bulundu."])
                tdd_cevap = y_lnduzelt(Eq(F, M_intx + Hy, evaluate=False))
                pprint(tdd_cevap)
                #adim_listesi_oku([f"Denklemin genel çözümü: {tdd_cevap}"])


                F = symbols('F')
                print(f"\n\n\n2) əF / əY = {y_lnduzelt(thg_dy_kat)} iki tarafınında y'e göre integralini alalım")
                #adim_listesi_oku([f"İkinci denklemin her iki tarafınında ye ye göre integralini alalım."])

                N_inty = y_lnduzelt(integrate(thg_dy_kat, y_s))
                pprint(f"F = {N_inty} + H(x) ")
                #adim_listesi_oku([f"Ef fonksiyonu eşittir {y_lnduzelt(N_inty)} artı He ix olarak bulundu."])
                print("H(x)'i bulmak bunun için x'e göre türev alarak M(x,y)'ye eşitleyelim\n ")
                #adim_listesi_oku(["He ix i bulmak bunun için ix e göre türev alarak birinci denkleme eşitlemek."])
                N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
                print("əF / əY = ", N_diffx, " + H'(x)")
                #adim_listesi_oku([f"Fe nin ix e göre kısmi türevi eşittir {y_lnduzelt(N_diffx)} artı He türev ix olarak hesaplandı."])
                print("N(x,y)'yi yerine yerleştirip H'(x) i yalnız bırakalım:")
                #adim_listesi_oku(["İkinci denklemi yerine yerleştirip He türev ix i yalnız bırakalım."])
                Hx = y_lnduzelt(simplify(thg_dx_kat - N_diffx))
                print(f"H'(x) = {Hx}")
                #adim_listesi_oku([f"He türev ix eşittir {y_lnduzelt(Hx)} olarak bulundu."])
                print("\nHer iki tarafında x'e göre integralini alalım: ")
                #adim_listesi_oku(["Her iki tarafında ix e göre integralini alalım."])
                Hx = y_lnduzelt(integrate(Hx, x))
                print(f'H(x) = {Hx + C}')
                #adim_listesi_oku([f"Böylece He ye eşittir {y_lnduzelt(Hx)} olarak hesaplandı."])
                print("F = ")
                #adim_listesi_oku([f"Şimdi bulduğumuz değerleri yerine koyarak genel çözümü oluşturalım."])
                tdd_cevap = y_lnduzelt(Eq(N_inty + Hx, C, evaluate=False))
                pprint(tdd_cevap)
                #adim_listesi_oku([f"Denklemin genel çözümü: {tdd_cevap}"])
                print(f"\n\nBulduğumuz ilk çözüm, {y_lnduzelt(expand(M_intx + Hy))} ve ikinci çözüm, {y_lnduzelt(expand(N_inty + Hx))} olduğundan her iki yolda bizi aynı çözüme götürüyor\n\n")
                #adim_listesi_oku([f"Bulduğumuz ilk çözüm {M_intx + Hy} ve ikinci çözüm {N_inty + Hx} olduğundan her iki yolda bizi aynı çözüme götürüyor."])
                #adim_listesi_oku([str(tdd_cevap)])
    #           ----pdf çıktısı---
                thg_pdf(denklempdf, dxkat, dykat, My, Nx, thg_dx_kat, thg_dy_kat, thgmis, zaman_etiketi, adimlar_listesi, pdf_birlestirme_icin)



#3. durumla tam hale gelebilen denk  (y-xy^3)dx+xdy=0  ama arama bunu tam hale gelebilir olarak görmüyor
#(y^2 + e^y) dy/dx = x * sin(x) tam dif   bu denklemi tamdan çözünce cevap 0 çıkıyor  halloldu


 #tam hale gelebilir (x*y^2+x)dx+(2*x^2*y)dy=0   x e bağlı
#tam diferansiyel denklem (ln(y)+y/x)dx+(x/y+ln(x))dy=0

 #tam hale gelebilir 6xydx + (4y+9x^2)dy=0 y'ye bağlı
 #tam hale gelebilir (x-x^2-y^2)dx + y dy = 0  x'e bağlı
#tam difdenk = (2y-xe^(xy))dy = (2+ye^(xy))dx
 #tam hale gelebilir = 6xydx = -(4y+9xx)dy    y'ye bağlı
#x(x-4)dy + y dx = 0
#tamdif = (3*(x^2)*y + 2xy)dx + (x^3+x^2+2y) dy = 0
#tamdif = (ln(y)+ y/x)dx + (x/y + ln(x))dy = 0


#tam hale getirilebilen xy'ye bağlı  (y^2*x+y)dx + (x-x^2*y)dy = 0 

                               #   ÖRNEK DENKLEMLER  #


# ÇARPANLARINA AYRILABİLİR(SEPARABLE)
#   (1 + x^2) * y' = y * ln(y)
#   y' = x * exp(x*y) yapay zekanın verdiği denklem çarpanlarına ayrılabilir değilmiş kod doğru çalışmış
#   y' = (x^2 + 1) / (y * ln(y))
#   (y^2 + e^y) dy/dx = x * sin(x)
#   y' = (x * y) / (1 + x^2 * y^2) buda aynı şekilde

#1. MERTEBEDEN LİNEER
#   y' + (ln(x)/x) y = x^2
#   y' - (2/x) y = x * e^x
#   y' + (1/(x ln x)) y = ln(x)
#   y' + x^2 y = e^(-x^3) eğer süslü parantez girerse hata veriyor  y' + x^2 y = e^{-x^3}
#   y' + tan(x) y = sec(x) bunu eğer bu şekilde yazarsa her karakteri bir çarpan sanıyor y' + (tan x) y = sec x

#BERNOLLİ
#   y' + (1/x) y = x^2 y^3
#   y' - y = e^x y^2
#   y' + ln(x) y = x y^(-1) burdada lnx olarak yazarsa teker teker çarpan olarak algılıyor   y' + lnx y = x y^(-1)
#   y' + x y = x^2 y^4
#   y' - (2/x) y = x y^5

#RİCCATİ
#   y' = y^2 + x
#   y' = x y^2 + y + 1
#   y' = y^2 + (1/x) y + x
#   y' = (x^2) y^2 + sin(x) riccati yapısını sağlıyor ama özel çözümü bilinmediği sürece çözülemeyeceğinden algoritma bunu riccati sınıfının içine dahil etmiyor
#   y' = y^2 + e^x y + x buda aynı şekilde yapı olarak sağlıyor sadece

#1. MERTEBE HOMOJEN
#   y' = (x^2 + y^2) / (x y)
#   y' = (y - x) / (y + x)
#   (x + y) dx - (x - y) dy = 0
#   y' = (x^3 + y^3) / (x^2 y)
#   (x^2 + y^2) dy - 2xy dx = 0

#TAM DİFERANSİYEL
#   (2xy + e^x) dx + (x^2 + y) dy = 0     y' = -(2xy + e^x)/(x^2 + y)
#   (y cos(x) + 2x) dx + sin(x) dy = 0
#   (ln(y) + x/y) dx + (x/y) dy = 0 tam diferansiyel denk çıkmadı
#   (x^2 y + y) dx + (x^2 + x) dy = 0
#   (x y^2 + x) dx + (2x^2 y) dy = 0

#CAUCHY-EULER
#   x^2 y'' + 5x y' + 4y = 0 homojen olan
#   x^2 y'' - x y' + y = 0  homojen olan
#   x^2 y'' + 5x y' + 4y = 0 homojen olan            homojen olmayanlar ve olanları kendisi ayı sınıflar içerisinde tanımlı
#   x^2 y'' + x y' + y = x^2 homojen olmayan
#   x^2 y'' - 4x y' + 6y = x^3 homojen olmayan

#YÜKSEK MERTEBELİ LİNEER
#   y''' - 3y'' + 3y' - y = 0 homojen olan
#   y'''' + y'' = x           homojen olmayan
#   y'' - 2y' + y = x^2  homojen olmayan                   bundada kendi içerisinde ayrılmış şekilde
#   y''' + y = x        homojen olmayan
#   y'''' - 4y'' + 4y = 0 homojen olan

#MERTEBESİ DÜŞÜRÜLEBİLEN
#   y'' = x (y')^3
#   y'' = (y')^4

#LİE GRUP
#   y' = (x + y)/(x - y)
#   y' = (x^2 + y^2)/(x y)
#   y' = (x^3 + y^3)/(x^2 y)


#sympyda log 10 tabanında değil e tabanındadır o yüzden integrallerde ln yerine log yazar aslında ikisi aynı anlama gelir



#nezahat denediğim denklemler
#tam hale gelebilir (ycos(x))dx+(2sin(x))dy=0 x'e bağlı
#y(cos(xy))dx+x(cos(xy))dy=0 garip işlemler çıkarıyor tam dif
#(e^xsin(y)-2ysin(x))dx+(e^xcos(y)+2cos(x))dy=0 bundada yer değiştirip aldığı için tam olarak almıor.


