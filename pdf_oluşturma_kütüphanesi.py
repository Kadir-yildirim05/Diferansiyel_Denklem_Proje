# --- pdf çıktısı---
import subprocess
import datetime
from sympy import *
import os
from sympy import latex

x = Symbol('x')
y = Function('y')
dx, dy = symbols('dx dy')
F, C = symbols('F C')
H = Function('H')
y_s = Symbol('y')

class ln(log):
    def __str__(self):
        return f"ln({self.args[0]})"
    def _sympystr(self, printer):
        return f"ln({printer.doprint(self.args[0])})"
    def _latex(self, printer):
        return fr"\ln\left({printer._print(self.args[0])}\right)"

def y_lnduzelt(expr):
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


class DxDyduzelt(Expr):
    def __new__(cls, *args):
        return Expr.__new__(cls, *args)
    def _latex(self, printer):
        args = list(self.args)
        terimler = []
        for i in range(0, len(args), 2):
            kat = printer._print(args[i])
            sem = printer._print(args[i + 1])
            terimler.append(f"\\left({kat}\\right) {sem}")
        return " + ".join(terimler)

def dxdyduzelt(expr):
    A = expr.coeff(dx)
    B = expr.coeff(dy)
    if expr.coeff(Derivative(y(x), x)) == 1:
        return expr
    elif A == 0 and B == 0:
        return expr
    elif A == 0:
        return DxDyduzelt(B, dy)
    elif B == 0:
        return DxDyduzelt(A, dx)
    else:
        return DxDyduzelt(B, dy, A, dx)

b=5
pdf_birlestirme_icin=[]

def pdf_raporu_olustur(baslik, adimlar, dosya_adi):
    """
    Sadece kullanıcının girdiği denklemi ve hesaplamaları kullanarak PDF raporu oluşturur.
    """
    baslangic = r"""
\documentclass[12pt]{article}                 %belge türü makale
\usepackage[utf8]{inputenc}             %karakter kodlaması 
\usepackage[turkish]{babel}             %belgeyi türkçe yapıyor.
\usepackage[margin=2.5cm]{geometry}         %sayfanın kenalarından 2.5cm boşluk bırakıyor
\usepackage[fleqn]{amsmath}
%\usepackage{amsmath} 
%\usepackage{mathptmx}                       %matematiksel ifade ve yazılar farkı görünmick                   
\usepackage{amsfonts}
\usepackage{setspace}
\setstretch{1.1} 
\setlength{\mathindent}{1cm}
\begin{document}                        %belgeyi başlatıyor
\pagestyle{empty}                   %sayfa numarasını kaldırıyor 

\begin{center}                               %sayfaya ortalıyor
    {\huge \textbf{""" + baslik + r"""}} \\         
    \vspace{10pt}
\end{center}

\textbf
"""
    icerik = ""
    for adim in adimlar:
        if hasattr(adim, 'free_symbols') or isinstance(adim, (Equality, Add, Mul, Pow)):
            icerik += f"\\noindent \\hspace*{{20pt}} ${latex(adim)}$ \\\\[8pt] \n"
        else:
            # Açıklama metinleri normal hizada kalmaya devam ediyor
            icerik += f"\\noindent {str(adim)} \\\\[6pt] \n"
    bitis = r"""

\end{document}
"""

    tex_ismi = f"{dosya_adi}.tex"         #pdf oluşması için gerekiyor silme.
    with open(tex_ismi, "w", encoding="utf-8") as f:        #w yazma yetkisi utf-8 türkçe karakterler
        f.write(baslangic + icerik + bitis)

    try:                   #subprocess.run pdflatex çalıştırır 2. ise pdfi hataya rağmen oluştumaya devam ettirirhata ayıklama için önemli
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_ismi], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)  # stdout ve stderr ekledim bu sayede gereksiz çıktı vermez
        for ext in [".log", ".aux",".tex"]:
            yl=f"{dosya_adi}{ext}"
            if os.path.exists(yl):           #sadece pdf oluşturuyor kalabalığı önlüyor
                os.remove(yl)
        print(f"\n[SİSTEM] Rapor başarıyla kaydedildi: {dosya_adi}.pdf")
    except Exception as e:
        print(f"\n[HATA] PDF oluşturulamadı.Detay: {e} ")
        import traceback
        traceback.print_exc()
        print("\n[İPUCU] Klasöre git ve .log dosyasını aç. ! işareti olan satırı yapıştır.")




zaman_etiketi = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # tarih saat alıyor pdf ismi yapıyor
adimlar_listesi = []

from sympy import symbols, Function, latex, Eq, simplify, diff, exp, integrate, nsimplify, expand


def tur_bulma_pdf(denklem, cozumler3, adimlar_listesi, y_lnduzelt, dxdyduzelt, denk_ayirmay, denk_ayirmax):

    x = symbols('x')
    y_s = symbols('y')
    dx = symbols('dx')
    dy = symbols('dy')
    y = Function('y')
    adimlar_listesi.append("\\noindent \\textbf{Denkleminiz:}")
    if hasattr(denklem, 'lhs'):
        denklem_expr = nsimplify(expand(denklem.lhs - denklem.rhs), full=True)
    else:
        denklem_expr = nsimplify(expand(denklem), full=True)

    adimlar_listesi.append(y_lnduzelt(Eq(dxdyduzelt(denklem_expr), 0)))
    adimlar_listesi.append(r"\textbf{Denkleminizin Çözüm Türleri:}")
    dxkat = diff(denklem_expr, dx)
    dykat = diff(denklem_expr, dy)

    M = dxkat.subs(y(x), y_s)
    N = dykat.subs(y(x), y_s)
    My = nsimplify(diff(M, y_s), full=True)
    Nx = nsimplify(diff(N, x), full=True)

    cozum_turu = [t.strip() for t in cozumler3]

    if "Değişkenlerine ayrılabilir diferansiyel denklem" in cozum_turu:
        aa = nsimplify(denk_ayirmay(dykat), full=True)
        ab = nsimplify(denk_ayirmay(dxkat), full=True)
        ba = nsimplify(denk_ayirmax(dxkat), full=True)
        bb = nsimplify(denk_ayirmax(dykat), full=True)
        y_bagli = nsimplify(aa / ab) if ab != 0 else aa
        x_bagli = nsimplify(-1 * ba / bb) if bb != 0 else ba

        adimlar_listesi.append(rf"\indent Denklemin $dy$'li tarafını $y$'ye ve $dx$ olan tarafını $x$'e göre düzenleyelim."
            rf" \\ Düzenlenmiş hali: "
            rf"\\  \indent $({latex(y_lnduzelt(y_bagli))})\,dy=({latex(y_lnduzelt(x_bagli))})\,dx$ "
            rf"\\ Girilen denklem $F(y)dy=H(x)dx$ formuna uyduğu için \textbf {{Değişkenlerine Ayrılabilir Diferansiyel Denklemdir.}}")

    if "Tam diferansiyel denklem" in cozum_turu:
        adimlar_listesi.append(rf"\indent Denklemin genel formu $M(x,y)dx+N(x,y)dy=0$ formuna uymaktadır. "
            rf" $M(x,y)={latex(y_lnduzelt(M))}$ ve $N(x,y)={latex(y_lnduzelt(N))}$ "
            rf" $M(x,y)$'nin $y$'ye göre türevi $M_y={latex(y_lnduzelt(My))}$ ve $N(x,y)$'nin $x$'e göre türevi $N_x={latex(y_lnduzelt(Nx))}$ olup $M_y=N_x$ şeklinde olduğundan \textbf{{Tam Diferansiyel Denklemdir.}}" )

    elif "Tam hale getirilebilen diferansiyel denklem" in cozum_turu:
        metin = (rf"\indent Denklemin genel formu $M(x,y)dx+N(x,y)dy=0$ formuna uymaktadır. Denkleminizde $M(x,y)={latex(y_lnduzelt(M))}$ ve $N(x,y)={latex(y_lnduzelt(N))}$ 'dir."
            rf"Buradan $M(x,y)$'nin $y$'ye göre türevi $M_y={latex(y_lnduzelt(My))}$ ve $N(x,y)$'nin $x$'e göre türevi $N_x={latex(y_lnduzelt(Nx))}$ olup $M_y$ $N_x$'e eşit olmadığı için tam diferansiyel değildir."
            rf" $M(x,y)$ ve $N(x,y)$ değerlerini integral çarpanı ile çarparsak denklemimizi \textbf{{ Tam Diferansiyel Denklem Haline Getirebiliriz}}")

        #if simplify((My - Nx) / N).free_symbols <= {x}:
            #thg_x = nsimplify(simplify((My - Nx) / N), full=True)
            #thg_ex = nsimplify(exp(integrate(thg_x, x)), full=True)
            #metin += rf"$\frac{{M_y - N_x}}{{N}} = {latex(y_lnduzelt(thg_x))}$ ifadesi sadece $x$'e bağlı olduğundan  İntegral çarpanı: $\mu(x) = {latex(y_lnduzelt(thg_ex))}$"

        #elif simplify((Nx - My) / M).free_symbols <= {y_s}:
            #thg_y = nsimplify(simplify((Nx - My) / M), full=True)
            #thg_ey = nsimplify(exp(integrate(thg_y, y_s)), full=True)
            #metin += rf"$\frac{{N_x - M_y}}{{M}} = {latex(y_lnduzelt(thg_y))}$ ifadesi sadece $y$'ye bağlı olduğundan İntegral çarpanı: $\mu(y) = {latex(y_lnduzelt(thg_ey))}$"

        #elif simplify((My-Nx)/(y-s * N - x * M)) !=0:
            #payda = nsimplify(y_s * N - x * M)
            #thg_xy_ifade = nsimplify((My - Nx) / payda)
            #thg_z = nsimplify(thg_xy_ifade.subs(x * y_s, z), full=True)
            #thg_ez = nsimplify(exp(integrate(thg_z, z)), full=True)
            #thg_exy = thg_ez.subs(z, x * y_s)  # Sonuçta z yerine tekrar x*y yazıyoruz

            #metin += (rf"$\frac{{M_y - N_x}}{{yN - xM}} = {latex(y_lnduzelt(thg_xy_ifade))}$ ifadesi $xy$ çarpımına bağlıdır. "
                     # rf"$xy = z$ dönüşümü yapılırsa $\mu(z) = {latex(y_lnduzelt(thg_ez))}$ olur. "
                     # rf"Buradan integral çarpanı: $\mu(x,y) = {latex(y_lnduzelt(thg_exy))}$")

        adimlar_listesi.append(metin)

    return adimlar_listesi

def dadd_pdf(al_denklem, dadd_dxdyduzen, dadd_int, dadd_ciktisi, pdf_birlestirme_icin):
    adimlar_listesi=[]
    if pdf_birlestirme_icin != []:
        adimlar_listesi= pdf_birlestirme_icin

    if not any("Denkleminiz" in str(oge) for oge in adimlar_listesi):
        adimlar_listesi.append("Denkleminiz:")
        adimlar_listesi.append(al_denklem)
    adimlar_listesi.append(r" \textbf {Değişkenlerine Ayrılabilir Diferansiyel Denklem Çözümü:}")
    adimlar_listesi.append("İki tarafında integralini alalım:")
    adimlar_listesi.append(dadd_int)     #zaten y_lnduzelt şeklinde alınmış ana kodda o yüzden bu formda
    adimlar_listesi.append("Denklemi kapalı form olarak düzenleyelim:")
    adimlar_listesi.append(fr"\indent ${latex(y_lnduzelt(dadd_ciktisi))}$")
    pdf_raporu_olustur("ÇÖZÜM RAPORU", adimlar_listesi, f"CÖZÜM{zaman_etiketi}")


#elif denklem_turu == '3' and 'My' in locals():   My ne için aldın anlamadım Nezahat
def tdd_pdf(denklempdf, dxkat, dykat, My, Nx, adimlar_listesi, zaman_etiketi,pdf_birlestirme_icin):

# SymPy'nin y(x) ile karıştırmaması için y'yi bir sembol olarak tanımlıyoruz
    y_s = Symbol('y')

    if pdf_birlestirme_icin != []:
        adimlar_listesi = pdf_birlestirme_icin
    adimlar_listesi = [oge for oge in adimlar_listesi if not isinstance(oge, bool)]
    if not any("Denkleminiz" in str(oge) for oge in adimlar_listesi):
        adimlar_listesi.insert(0, "Denkleminiz:")
        adimlar_listesi.append(denklempdf)

    adimlar_listesi.append(r" \textbf{Tam Diferansiyel Denklem Çözümü:}")

    adimlar_listesi.append(r"$F(x,y)=c$ çözüm olsun, o halde: \\ " +
            r"\indent 1) $\frac{\partial F}{\partial x} = M(x,y) =" + latex(y_lnduzelt(dxkat)) + r"$ \\ " +
            r"\indent 2) $\frac{\partial F}{\partial y} = N(x,y) = " + latex(y_lnduzelt(dykat)) + r"$ bulunur.")
    adimlar_listesi.append("Şimdi F(x,y)'yi yalnız bırakalım.")
    adimlar_listesi.append(rf"1) $\frac{{\partial F}}{{\partial x}} = {latex(y_lnduzelt(dxkat))}$ her iki tarafın $x$'e göre integralini alalım.")
    M_intx = integrate(dxkat, x)
    tdd_a1 = y_lnduzelt(Eq(F, Add(simplify(M_intx), H(y_s), evaluate=False)))
    adimlar_listesi.append(tdd_a1)
    M_diffy = diff(M_intx, y_s)
    adimlar_listesi.append(rf"$H(y)$'yi bulmak için y'ye göre türev alarak $N(x,y)$'ye eşitleyeceğiz."
                           rf"\\ \indent $ \frac{{\partial F}}{{\partial y}} = {latex(M_diffy)} + H'(y) $")
    adimlar_listesi.append("$N(x,y)$'i yerine yerleştirip $H'(y)$'yi yalnız bırakalım:")
    Hy = y_lnduzelt(simplify(dykat - M_diffy))
    adimlar_listesi.append(fr" \indent  $H'(y)= {latex(Hy)}$ ")
    adimlar_listesi.append("Her iki tarafında $y$'ye göre integralini alalım: ")
    Hy = y_lnduzelt(integrate(Hy, y_s))
    adimlar_listesi.append(fr"\indent $H(y)= {latex(Hy+C)}$")
    tdd_cevap = y_lnduzelt(Eq(F, Eq(M_intx + Hy, C,  evaluate=False), evaluate=False))
    adimlar_listesi.append(tdd_cevap)
    ### 2. seçenek
    adimlar_listesi.append( rf" 2) $\frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(dykat))}$ her iki tarafın $y$'e göre integralini alalım.")

    N_inty = y_lnduzelt(integrate(dykat, y_s))
    adimlar_listesi.append(rf"\indent $F={latex(N_inty)} + H(x)$")
    N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
    adimlar_listesi.append(rf"$H(x)$'i bulmak için $x$'e göre türev alarak $M(x,y)$'ye eşitleyeceğiz."
                           rf"\\ \indent $\frac{{\partial F}}{{\partial x}}= {latex(N_diffx)} + H'(x)$")
    adimlar_listesi.append("$M(x,y)$'yi yerine yerleştirip $H'(x)$'i yalnız bırakalım:")
    Hx = y_lnduzelt(simplify(dxkat - N_diffx))
    adimlar_listesi.append(rf" \indent $H'(x)= {latex(Hx)}$")
    adimlar_listesi.append("Her iki tarafında x'e göre integralini alalım: ")
    Hx = y_lnduzelt(integrate(Hx, x))
    adimlar_listesi.append(rf" \indent $H(x)= {latex(Hx)}$")
    tdd_cevap= y_lnduzelt(Eq(F, Eq(N_inty + Hx, C, evaluate=False), evaluate=False) )
    adimlar_listesi.append(tdd_cevap)

    adimlar_listesi.append(f"Bulduğumuz ilk çözüm: ${latex(y_lnduzelt(expand(M_intx + Hy)))}$, ikinci çözüm: ${latex(y_lnduzelt(expand(N_inty + Hx)))}$ olduğundan her iki yolda bizi aynı çözüme götürüyor." )

    pdf_raporu_olustur("ÇÖZÜM RAPORU", adimlar_listesi, f"Cozum_{zaman_etiketi}")


def thg_pdf(denklempdf, dxkat, dykat, My, Nx, thg_dx_kat, thg_dy_kat, thgmis, zaman_etiketi, adimlar_listesi, pdf_birlestirme_icin):
    y_s = Symbol('y')
    x_s = Symbol('x')
    dx = Symbol('dx')
    dy = Symbol('dy')
    F = Symbol('F')
    C = Symbol('C')

    if pdf_birlestirme_icin:
        adimlar_listesi = [oge for oge in pdf_birlestirme_icin if not isinstance(oge, bool)]
    else:
        adimlar_listesi = []

    if not any("Denkleminiz" in str(oge) for oge in adimlar_listesi):
        adimlar_listesi.append("Denkleminiz:")
        adimlar_listesi.append(denklempdf)
    adimlar_listesi.append(r"\textbf{Tam Hale Gelebilir Diferansiyel Denklem Çözümü:}")

    dxkat = dxkat.subs(y(x), y_s)
    dykat = dykat.subs(y(x), y_s)
    My = diff(dxkat, y_s)
    Nx = diff(dykat, x)

    if simplify((My - Nx) / dykat).free_symbols <= {x_s}:
        thg_x = y_lnduzelt(simplify((My - Nx) / dykat))
        thg_ex = y_lnduzelt(exp(integrate(thg_x, x_s)))
        adimlar_listesi.append(rf"$\frac{{M_y - N_x}}{{N(x,y)}} = \frac{{{latex(My)} - {latex(Nx)}}}{{{latex(dykat)}}}= {latex(y_lnduzelt(thg_x))}$ ifadesi sadece $x$'e bağlı olduğundan  İntegral çarpanı: $\mu(x) = {latex(y_lnduzelt(thg_ex))}$ şeklindedir.")

        thg_dx_kat = dxkat * thg_ex
        thg_dy_kat = dykat * thg_ex
        adimlar_listesi.append(f"M(x,y) ve N(x,y) değerlerini ${latex(thg_ex)}$ ile çarparsak denklemimiz tam diferansiyel hale gelir."
            " Denklemimiz: ")
        thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
        adimlar_listesi.append(thgmis)

    elif simplify((Nx - My) / dxkat).free_symbols <= {y_s}:
        thg_y = y_lnduzelt(simplify((Nx - My) / dxkat))
        thg_ey = y_lnduzelt(exp(integrate(thg_y, y_s)))
        adimlar_listesi.append(rf"Burada $\frac{{N_x - M_y}}{{M(x,y)}} = \frac{{{latex(Nx)} - {latex(My)}}}{{{latex(dxkat)}}} = {latex(thg_y)}$ "
            rf"ifadesi sadece $y$'ye bağlı olduğundan integral çarpanımız $\mu(y) = {latex(thg_ey)}$ şeklindedir.")
        #adimlar_listesi.append(fr"Burada $(M_y-N_x)/N = {latex(thg_y)}$ y'e bağlı olduğundan integral çarpanımız ${latex(thg_ey)}$ şeklindedir.")
        thg_dx_kat = dxkat * thg_ey
        thg_dy_kat = dykat * thg_ey
        adimlar_listesi.append(f"M(x,y) ve N(x,y) değerlerini ${latex(thg_ey)}$ ile çarparsak denklemimiz tam diferansiyel hale gelir."
            " Denklemimiz: ")
        thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
        adimlar_listesi.append(thgmis)

    elif simplify((My - Nx) / ((y_s * dykat) - (x * dxkat))) != 0:
        z = symbols('z')
        degisken_degis = simplify((My - Nx) / ((y_s * dykat) - (x * dxkat))).subs(y_s * x, z)
        if degisken_degis.free_symbols <= {z}:
            if b == 5:
                thg_z = y_lnduzelt(simplify((My - Nx) / ((y_s * dykat) - (x * dxkat))).subs(y_s * x, z))
                thg_xy = y_lnduzelt(simplify((My - Nx) / ((y_s * dykat) - (x * dxkat))))
                thg_ez = y_lnduzelt(exp(integrate(thg_z, z)))
                thg_exy = thg_ez.subs(z, y_s * x)
                adimlar_listesi.append(fr"Burada $\frac{{M_y - N_x}}{{yN - xM}} = \frac{{{latex(My)} - {latex(Nx)}}}{{{latex(y_s * dykat - x * dxkat)}}} = {latex(thg_xy)}$ $xy$'ye bağlı, integrali alabilmek için $xy = z$ diyeceğiz, buradan integral çarpanı $\mu(z) = {latex(thg_ez)}$ bulunur."
                                       fr"$xy$ değerlerimizi tekrar yerine koyarsak asıl integral çarpanımızı elde ederiz: $\mu(x,y) = {latex(thg_exy)}$ ")
                thg_dx_kat = dxkat * thg_exy
                thg_dy_kat = dykat * thg_exy
                thgmis = y_lnduzelt(Eq(dxdyduzelt(thg_dx_kat * dx + thg_dy_kat * dy), 0, evaluate=False))
                adimlar_listesi.append(thgmis)


    adimlar_listesi.append(fr" Denklemimizin tam diferansiyel olması için $M_y=N_x$ olmalı ")
    My = simplify(diff(thg_dx_kat, y_s))
    Nx = simplify(diff(thg_dy_kat, x))
    adimlar_listesi.append(fr" $M_y={latex(y_lnduzelt(My))}$ ve $N_x={latex(y_lnduzelt(Nx))}$ olup $M_y=N_x$ olduğu için denklem tam diferansiyeldir. ")
    adimlar_listesi.append(r"$F(x,y)=C$ çözüm olsun o halde:  1) $\frac{\partial F}{\partial x}=M(x,y)$ ve 2) $\frac{\partial F}{\partial y}=N(x,y)$")
    adimlar_listesi.append(fr" 1) $\frac{{\partial F}}{{\partial x}}={latex(y_lnduzelt(thg_dx_kat))}$ ve 2)  $\frac{{\partial F}}{{\partial y}}= {latex(y_lnduzelt(thg_dy_kat))}$")

    adimlar_listesi.append("Şimdi F(x,y)'yi yalnız bırakalım.")
    adimlar_listesi.append(rf" 1) $\frac{{\partial F}}{{\partial x}} = {latex(y_lnduzelt(thg_dx_kat))}$ her iki tarafın $x$'e göre integralini alalım.")
    M_intx = integrate(thg_dx_kat, x)
    tdd_a1 = y_lnduzelt(Eq(F, dxdyduzelt(Add(simplify(M_intx), H(y_s), evaluate=False))))
    adimlar_listesi.append(tdd_a1)
    adimlar_listesi.append(fr"$H(y)$'i bulmak için $y$'ye göre türev alarak $N(x,y)$'ye eşitleyecğiz.")
    M_diffy = diff(M_intx, y_s)
    adimlar_listesi.append(fr"\indent $ \frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(M_diffy))} + H'(y) $")
    adimlar_listesi.append(fr"$N(x,y)$'i yerine yerleştirip $H'(y)$'i yalnız bırakalım:")
    Hy = y_lnduzelt(simplify(thg_dy_kat - M_diffy))
    adimlar_listesi.append(fr" \indent $H'(y)= {latex(Hy)}$ ")
    adimlar_listesi.append("Her iki tarafında $y$'ye göre integralini alalım: ")
    Hy = y_lnduzelt(integrate(Hy, y_s))
    adimlar_listesi.append(fr" \indent $H(y)= {latex(Hy + C)}$")
    tdd_cevap = y_lnduzelt(Eq(F, M_intx + Hy, evaluate=False))
    adimlar_listesi.append(tdd_cevap)
    #2. seçenek
    adimlar_listesi.append(rf" 2) $\frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(thg_dy_kat))}$ iki tarafınında $y$'e göre integralini alalım.")
    N_inty = y_lnduzelt(integrate(thg_dy_kat, y_s))
    adimlar_listesi.append(fr" \indent $F={latex(N_inty)} + H(x)$")
    adimlar_listesi.append(fr"$H(x)$'i bulmak için ise $x$'ye göre türev alarak $M(x,y)$'ye eşitleyelim.")
    N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
    adimlar_listesi.append(fr"\indent  $ \frac{{\partial F}}{{\partial y}}= {latex(N_diffx)} + H'(x)$")
    adimlar_listesi.append(fr"$M(x,y)$'yi yerine yerleştirip $H'(x)$'i yalnız bırakalım:")
    Hx = y_lnduzelt(simplify(thg_dx_kat - N_diffx))
    adimlar_listesi.append(fr"\indent $H'(x)= {latex(Hx)}$")
    adimlar_listesi.append("Her iki tarafında x'e göre integralini alalım: ")
    Hx = y_lnduzelt(integrate(Hx, x_s))
    adimlar_listesi.append(fr" \indent $H(x)= {latex(Hx)}$")
    tdd_cevap = y_lnduzelt(Eq(F, N_inty + Hx, evaluate=False))
    adimlar_listesi.append(tdd_cevap)

    adimlar_listesi.append(f"Bulduğumuz ilk çözüm: ${latex(y_lnduzelt(expand(M_intx + Hy)))}$, ikinci çözüm: ${latex(y_lnduzelt(expand(N_inty + Hx)))}$ olduğundan her iki yolda bizi aynı çözüme götürüyor.")

    pdf_raporu_olustur("ÇÖZÜM RAPORU", adimlar_listesi, f"Cozum_{zaman_etiketi}")









