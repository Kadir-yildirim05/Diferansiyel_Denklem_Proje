# --- pdf çıktısı---
import subprocess
import datetime
import re as _re   # 'sympy' kendi 're' (reel kısım) fonksiyonunu tanımladığından
                    # isim çakışmasını önlemek için modülü _re olarak alıyoruz.
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

# renkler ve kutu renkleri

_KUTU_RENKLERI = [
    ("mavikutu", "mavicerceve"),
    ("yesilkutu", "yesilcerceve"),
    ("lavantakutu", "lavantacerceve"),
]


def _baslik_metni_mi(adim):
    if not isinstance(adim, str):
        return None
    s = adim.strip().replace(r'\noindent', '').strip()
    if s == "Denkleminiz:":
        return s
    m = _re.match(r'^\\textbf\s*\{(.+?)\}\s*$', s, _re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _duz_denklem_mi(adim):
    if not isinstance(adim, str):
        return None
    s = adim.strip()
    m = _re.match(r'^(?:\\indent\s*)?\$(.+)\$\s*$', s, _re.DOTALL)
    if m and m.group(1).count('$') == 0:
        return m.group(1)
    return None


def _sonuc_cumlesi_mi(adim):
    if not isinstance(adim, str):
        return False
    s = adim.lower()
    anahtar_kelimeler = [
        "diferansiyel denklemdir", "diferansiyel değildir", "haline getirebiliriz",
    ]
    return any(k in s for k in anahtar_kelimeler)


def _matematik_mi(a):
    return (hasattr(a, 'free_symbols') or isinstance(a, (Equality, Add, Mul, Pow))
            or _duz_denklem_mi(a) is not None)


def _es_latex(a):
    """Bir adımın LaTeX gövdesini (```$``` işaretleri olmadan) döndürür."""
    if hasattr(a, 'free_symbols') or isinstance(a, (Equality, Add, Mul, Pow)):
        return latex(a)
    return _duz_denklem_mi(a)


class YanYana:
    """tdd ve thg için yan yana gelen iki kutu """
    def __init__(self, sol_baslik, sol_adimlar, sag_baslik, sag_adimlar):
        self.sol_baslik = sol_baslik
        self.sol_adimlar = sol_adimlar if isinstance(sol_adimlar, list) else [sol_adimlar]
        self.sag_baslik = sag_baslik
        self.sag_adimlar = sag_adimlar if isinstance(sag_adimlar, list) else [sag_adimlar]


def _yanyana_kolon_govde(baslik_metni, adimlar_alt, cerceve):
    """YanYana'nın tek bir sütununu (etiket + üst üste adımlar) LaTeX'e çevirir."""
    etiket = str(baslik_metni)
    tek_adim_mi = (len(adimlar_alt) == 1) and _matematik_mi(adimlar_alt[0])

    # Tek denklemlik sütun (örn. M(x,y), M_y): tek satırda "etiket = değer",
    # ayrı bir başlık satırı ya da iç kutu YOK — hepsi aynı (dış) kutuda.
    if tek_adim_mi and len(etiket) > 2:
        lg = _es_latex(adimlar_alt[0])
        return r"\centering $" + etiket + " = " + lg + r"$"

    ic = ""
    if len(etiket) <= 2:
        ic += (
            r"\centering\tikz[baseline=-0.5ex]{\node[draw=" + cerceve + ", fill=" + cerceve
            + r", circle, text=white, font=\bfseries\small, inner sep=1.5pt, "
            r"minimum size=16pt] {" + etiket + r"};}\\[6pt]" "\n"
        )
    else:
        ic += r"\noindent{\bfseries\small $" + etiket + r"$}\\[5pt]" "\n"

    n = len(adimlar_alt)
    for j, a in enumerate(adimlar_alt):
        son_mu = (j == n - 1)
        if _matematik_mi(a):
            lg = _es_latex(a)
            if son_mu:
                ic += r"\centering $\mathbf{" + lg + r"}$" "\n"
            else:
                ic += r"\centering $" + lg + r"$\\[5pt]" "\n"
        else:
            ic += r"\noindent{\footnotesize " + str(a) + r"}\\[4pt]" "\n"
    return ic


def _yanyana_latex(yy):
    sol_ic = _yanyana_kolon_govde(yy.sol_baslik, yy.sol_adimlar, "mavicerceve")
    sag_ic = _yanyana_kolon_govde(yy.sag_baslik, yy.sag_adimlar, "yesilcerceve")
    return (
        r"\noindent\begin{minipage}[t]{0.48\textwidth}"
        r"\begin{tcolorbox}[colback=mavikutu, colframe=mavicerceve, arc=2pt, boxrule=0.7pt, "
        r"left=6pt, right=6pt, top=5pt, bottom=5pt, valign=top]"
        + sol_ic +
        r"\end{tcolorbox}\end{minipage}\hfill"
        r"\begin{minipage}[t]{0.48\textwidth}"
        r"\begin{tcolorbox}[colback=yesilkutu, colframe=yesilcerceve, arc=2pt, boxrule=0.7pt, "
        r"left=6pt, right=6pt, top=5pt, bottom=5pt, valign=top]"
        + sag_ic +
        r"\end{tcolorbox}\end{minipage}"
        "\n\\vspace{6pt}\n"
    )


class TekKutuGrup:
    """tdd ve thgde işlemleri tek kutuya alma """
    def __init__(self, adimlar):
        self.adimlar = adimlar


def _yanyana_kolon_govde_ic(baslik_metni, adimlar_alt, cerceve):
    """YanYana'nın bir sütununu, TekKutuGrup içinde kullanılacak KÜÇÜK,
    beyaz zeminli iç içe kutucuk olarak hazırlar."""
    etiket = str(baslik_metni)
    if len(adimlar_alt) == 1 and _matematik_mi(adimlar_alt[0]):
        lg = _es_latex(adimlar_alt[0])
        return r"\centering $" + etiket + " = " + lg + r"$"
    ic = r"\noindent{\bfseries\small $" + etiket + r"$}\\[3pt]" "\n"
    for a in adimlar_alt:
        if _matematik_mi(a):
            ic += r"\centering $" + _es_latex(a) + r"$\\[3pt]" "\n"
        else:
            ic += r"\noindent{\footnotesize " + str(a) + r"}\\[3pt]" "\n"
    return ic


def _yanyana_latex_ic(yy):
    sol_ic = _yanyana_kolon_govde_ic(yy.sol_baslik, yy.sol_adimlar, "mavicerceve")
    sag_ic = _yanyana_kolon_govde_ic(yy.sag_baslik, yy.sag_adimlar, "yesilcerceve")
    return (
        r"\noindent\begin{minipage}[t]{0.47\textwidth}"
        r"\begin{tcolorbox}[colback=white, colframe=mavicerceve, arc=1pt, boxrule=0.6pt, "
        r"left=5pt, right=5pt, top=4pt, bottom=4pt, valign=top]"
        + sol_ic +
        r"\end{tcolorbox}\end{minipage}\hfill"
        r"\begin{minipage}[t]{0.47\textwidth}"
        r"\begin{tcolorbox}[colback=white, colframe=yesilcerceve, arc=1pt, boxrule=0.6pt, "
        r"left=5pt, right=5pt, top=4pt, bottom=4pt, valign=top]"
        + sag_ic +
        r"\end{tcolorbox}\end{minipage}\\[6pt]" "\n"
    )


def _tekkutu_latex(grup):
    ic = ""
    for a in grup.adimlar:
        if isinstance(a, YanYana):
            ic += _yanyana_latex_ic(a)
        elif _matematik_mi(a):
            ic += r"\centering $" + _es_latex(a) + r"$\\[5pt]" "\n"
        elif _sonuc_cumlesi_mi(a):
            ic += r"\noindent \checkmark\;\; " + str(a) + r"\\[5pt]" "\n"
        else:
            ic += r"\noindent " + str(a) + r"\\[5pt]" "\n"
    return (
        r"\begin{tcolorbox}[colback=mavikutu, colframe=mavicerceve, arc=2pt, boxrule=0.8pt, "
        r"left=8pt, right=8pt, top=6pt, bottom=6pt]"
        + ic +
        r"\end{tcolorbox}\vspace{4pt}" "\n"
    )


def pdf_raporu_olustur(baslik, adimlar, dosya_adi):
    matematik_indeksleri = [i for i, a in enumerate(adimlar) if _matematik_mi(a)]
    son_matematik_index = matematik_indeksleri[-1] if matematik_indeksleri else None

    ilk_denklem = None
    for i, a in enumerate(adimlar):
        if _baslik_metni_mi(a) == "Denkleminiz:" and i + 1 < len(adimlar):
            aday = adimlar[i + 1]
            if hasattr(aday, 'free_symbols') or isinstance(aday, (Equality, Add, Mul, Pow)):
                ilk_denklem = aday
            break

    baslangic = r"""
\documentclass[12pt]{article}                 %belge türü makale
\usepackage[utf8]{inputenc}             %karakter kodlaması
\usepackage[turkish]{babel}             %belgeyi türkçe yapıyor.
\usepackage[margin=2cm]{geometry}         %sayfanın kenalarından boşluk bırakıyor
\usepackage[fleqn]{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{setspace}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{tcolorbox}
\setstretch{1.15}
\setlength{\mathindent}{0.6cm}

% RENKLER 
\definecolor{lacivert}{HTML}{16213E}
\definecolor{altin}{HTML}{C9971F}
\definecolor{mavikutu}{HTML}{E8F1FB}
\definecolor{yesilkutu}{HTML}{E9F7EF}
\definecolor{lavantakutu}{HTML}{F1ECFB}
\definecolor{mavicerceve}{HTML}{2E5AAC}
\definecolor{yesilcerceve}{HTML}{2E9B5C}
\definecolor{lavantacerceve}{HTML}{7A52C7}
\definecolor{mavibaslikyumusak}{HTML}{6F94D3}

\begin{document}                        %belgeyi başlatıyor
\shorthandoff{=:!}          % Türkçe babel bu karakterleri "aktif" yapıyor;
                            % bu da tcolorbox/tikz'in key=value seçeneklerini
                            % (colback=..., boxrule=... gibi) bozuyordu.
\pagestyle{empty}                   %sayfa numarasını kaldırıyor

% üst başlık
\begin{tcolorbox}[colback=lacivert, colframe=lacivert, arc=3pt, boxrule=0pt,
                   sharp corners=south, left=10pt, right=10pt, top=8pt, bottom=8pt]
\centering\color{white}{\Large \textbf{""" + baslik + r"""}}
\end{tcolorbox}

\vspace{8pt}
"""

    if ilk_denklem is not None:
        baslangic += (
            r"\begin{tcolorbox}[colback=mavikutu, colframe=mavicerceve, arc=2pt, "
            r"boxrule=0.8pt, title=\textbf{DENKLEMİNİZ}, coltitle=white, "
            r"colbacktitle=mavibaslikyumusak, fonttitle=\small, left=8pt, right=8pt]"
            r"\centering $" + latex(ilk_denklem) + r"$"
            r"\end{tcolorbox}"
            "\n\\vspace{6pt}\n"
        )
    icerik = ""
    bolum_no = 0
    renk_index = 0
    for i, adim in enumerate(adimlar):
        baslik_metni = _baslik_metni_mi(adim)
        # "Denkleminiz:" başlığı ve hemen ardından gelen denklem zaten yazıldı tekrar yazmaması için
        if baslik_metni == "Denkleminiz:":
            continue
        if ilk_denklem is not None and adim is ilk_denklem:
            continue

        if baslik_metni:
            bolum_no += 1
            renk_index = 0
            baslik_govde = baslik_metni.rstrip(':').strip()
            icerik += (
                "\\vspace{8pt}\\noindent"
                "\\tikz[baseline=-0.6ex]{\\node[draw=mavicerceve, fill=mavicerceve, circle, "
                "text=white, font=\\bfseries\\small, inner sep=1.5pt, minimum size=16pt] {"
                + str(bolum_no) + "};}\\hspace{5pt}"
                "{\\bfseries\\color{lacivert} " + baslik_govde + "}\\\\[2pt]"
                "\\noindent\\rule{\\linewidth}{0.5pt}\\vspace{5pt}\n"
            )
            continue

        if isinstance(adim, TekKutuGrup):
            icerik += _tekkutu_latex(adim)
            continue

        if isinstance(adim, YanYana):
            icerik += _yanyana_latex(adim)
            continue

        if _sonuc_cumlesi_mi(adim):
            icerik += (
                r"\begin{tcolorbox}[colback=yesilkutu, colframe=yesilcerceve, arc=2pt, boxrule=0.7pt, "
                r"left=8pt, right=8pt, top=5pt, bottom=5pt]"
                r"\checkmark\;\; " + str(adim)
                + r"\end{tcolorbox}\vspace{4pt}" "\n"
            )
            continue

        latex_govde = _es_latex(adim) if not isinstance(adim, str) else _duz_denklem_mi(adim)

        if latex_govde is not None:
            if i == son_matematik_index:
                icerik += (
                    r"\begin{tcolorbox}[colback=altin!12, colframe=altin, arc=2pt, boxrule=1pt]"
                    r"\centering $\bigstar\;\;" + latex_govde + r"\;\;\bigstar$"
                    r"\end{tcolorbox}\vspace{5pt}" "\n"
                )
            else:
                arka, cerceve = _KUTU_RENKLERI[renk_index % len(_KUTU_RENKLERI)]
                renk_index += 1
                icerik += (
                    r"\begin{tcolorbox}[colback=" + arka + r", colframe=" + cerceve
                    + r", arc=2pt, boxrule=0.6pt, left=6pt, right=6pt, top=4pt, bottom=4pt]"
                    r"\centering $" + latex_govde + r"$"
                    r"\end{tcolorbox}\vspace{4pt}" "\n"
                )
        else:
            icerik += "\\noindent " + str(adim) + " \\\\[6pt]\n"

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

        adimlar_listesi.append(rf" Denklemin $dy$'li tarafını $y$'ye ve $dx$ olan tarafını $x$'e göre düzenleyelim."
            rf" \\ Düzenlenmiş hali: "
            rf"\\  \indent $({latex(y_lnduzelt(y_bagli))})\,dy=({latex(y_lnduzelt(x_bagli))})\,dx$ "
            rf"\\ Girilen denklem $F(y)dy=H(x)dx$ formuna uyduğu için \textbf {{Değişkenlerine Ayrılabilir Diferansiyel Denklemdir.}}")

    if "Tam diferansiyel denklem" in cozum_turu:
        adimlar_listesi.append(TekKutuGrup([
            r"Denklemin genel formu $M(x,y)dx+N(x,y)dy=0$ formuna uymaktadır.",
            YanYana("M(x,y)", y_lnduzelt(M), "N(x,y)", y_lnduzelt(N)),
            YanYana("M_y", y_lnduzelt(My), "N_x", y_lnduzelt(Nx)),
            r"$M_y=N_x$ şeklinde olduğundan \textbf{Tam Diferansiyel Denklemdir.}",
        ]))

    elif "Tam hale getirilebilen diferansiyel denklem" in cozum_turu:
        adimlar_listesi.append(TekKutuGrup([
            r"Denklemin genel formu $M(x,y)dx+N(x,y)dy=0$ formuna uymaktadır.",
            YanYana("M(x,y)", y_lnduzelt(M), "N(x,y)", y_lnduzelt(N)),
            YanYana("M_y", y_lnduzelt(My), "N_x", y_lnduzelt(Nx)),
            r"$M_y$, $N_x$'e eşit olmadığı için tam diferansiyel değildir. "
            r"$M(x,y)$ ve $N(x,y)$ değerlerini integral çarpanı ile çarparsak "
            r"denklemimizi \textbf{Tam Diferansiyel Denklem Haline Getirebiliriz.}",
        ]))

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
    adimlar_listesi.append(
        r"$F(x,y)=c$ çözüm olsun, o halde: "
        r"1) $\frac{\partial F}{\partial x}=M(x,y)=" + latex(y_lnduzelt(dxkat)) + r"$ "
        r"ve 2) $\frac{\partial F}{\partial y}=N(x,y)=" + latex(y_lnduzelt(dykat)) + r"$ bulunur."
    )
    adimlar_listesi.append("Şimdi F(x,y)'yi yalnız bırakalım.")

    # --- Yol 1: F_x = M(x,y) üzerinden ---
    yol1 = []
    yol1.append(rf"$\frac{{\partial F}}{{\partial x}} = {latex(y_lnduzelt(dxkat))}$ her iki tarafın $x$'e göre integralini alalım.")
    M_intx = integrate(dxkat, x)
    tdd_a1 = y_lnduzelt(Eq(F, Add(simplify(M_intx), H(y_s), evaluate=False)))
    yol1.append(tdd_a1)
    M_diffy = diff(M_intx, y_s)
    yol1.append(rf"$H(y)$'yi bulmak için ise $y$'ye göre türev alarak $N(x,y)$'ye eşitleyeceğiz."
                rf"\\ $\frac{{\partial F}}{{\partial y}} = {latex(M_diffy)} + H'(y)$")
    yol1.append("$N(x,y)$'i yerine yerleştirip $H'(y)$'yi yalnız bırakalım:")
    Hy = y_lnduzelt(simplify(dykat - M_diffy))
    yol1.append(fr"$H'(y)= {latex(Hy)}$")
    yol1.append("Her iki tarafında $y$'ye göre integralini alalım:")
    Hy = y_lnduzelt(integrate(Hy, y_s))
    yol1.append(fr"$H(y)= {latex(Hy+C)}$")
    tdd_cevap1 = y_lnduzelt(Eq(F, M_intx + Hy, evaluate=False))
    yol1.append(tdd_cevap1)

    # --- Yol 2: F_y = N(x,y) üzerinden ---
    yol2 = []
    yol2.append(rf"$\frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(dykat))}$ her iki tarafın $y$'e göre integralini alalım.")
    N_inty = y_lnduzelt(integrate(dykat, y_s))
    yol2.append(rf"$F={latex(N_inty)} + H(x)$")
    N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
    yol2.append(rf"$H(x)$'i bulmak için ise $x$'e göre türev alarak $M(x,y)$'ye eşitleyeceğiz."
                rf"\\ $\frac{{\partial F}}{{\partial y}}= {latex(N_diffx)} + H'(x)$")
    yol2.append("$N(x,y)$'yi yerine yerleştirip $H'(x)$'i yalnız bırakalım:")
    Hx = y_lnduzelt(simplify(dxkat - N_diffx))
    yol2.append(rf"$H'(x)= {latex(Hx)}$")
    yol2.append("Her iki tarafında $x$'e göre integralini alalım:")
    Hx = y_lnduzelt(integrate(Hx, x))
    yol2.append(rf"$H(x)= {latex(Hx)}$")
    tdd_cevap2 = y_lnduzelt(Eq(F, N_inty + Hx, evaluate=False))
    yol2.append(tdd_cevap2)

    adimlar_listesi.append(YanYana("1", yol1, "2", yol2))

    adimlar_listesi.append(f"Bulduğumuz ilk çözüm: ${latex(y_lnduzelt(M_intx + Hy))}$, ikinci çözüm: ${latex(y_lnduzelt(N_inty + Hx))}$ olduğundan her iki yolda bizi aynı çözüme götürüyor.")


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

    # --- Yol 1: F_x = M(x,y) üzerinden ---
    yol1 = []
    yol1.append(rf"$\frac{{\partial F}}{{\partial x}} = {latex(y_lnduzelt(thg_dx_kat))}$ her iki tarafın $x$'e göre integralini alalım.")
    M_intx = integrate(thg_dx_kat, x)
    tdd_a1 = y_lnduzelt(Eq(F, dxdyduzelt(Add(simplify(M_intx), H(y_s), evaluate=False))))
    yol1.append(tdd_a1)
    yol1.append(fr"$H(y)$'i bulmak için $y$'ye göre türev alarak $N(x,y)$'ye eşitleyeceğiz.")
    M_diffy = diff(M_intx, y_s)
    yol1.append(fr"$\frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(M_diffy))} + H'(y)$")
    yol1.append(fr"$N(x,y)$'i yerine yerleştirip $H'(y)$'i yalnız bırakalım:")
    Hy = y_lnduzelt(simplify(thg_dy_kat - M_diffy))
    yol1.append(fr"$H'(y)= {latex(Hy)}$")
    yol1.append("Her iki tarafında $y$'ye göre integralini alalım:")
    Hy = y_lnduzelt(integrate(Hy, y_s))
    yol1.append(fr"$H(y)= {latex(Hy + C)}$")
    tdd_cevap1 = y_lnduzelt(Eq(F, M_intx + Hy, evaluate=False))
    yol1.append(tdd_cevap1)

    # --- Yol 2: F_y = N(x,y) üzerinden ---
    yol2 = []
    yol2.append(rf"$\frac{{\partial F}}{{\partial y}} = {latex(y_lnduzelt(thg_dy_kat))}$ her iki tarafın $y$'e göre integralini alalım.")
    N_inty = y_lnduzelt(integrate(thg_dy_kat, y_s))
    yol2.append(rf"$F={latex(N_inty)} + H(x)$")
    yol2.append(fr"$H(x)$'i bulmak için ise $x$'ye göre türev alarak $M(x,y)$'ye eşitleyelim.")
    N_diffx = y_lnduzelt(simplify(diff(N_inty, x)))
    yol2.append(fr"$\frac{{\partial F}}{{\partial y}}= {latex(N_diffx)} + H'(x)$")
    yol2.append(fr"$N(x,y)$'yi yerine yerleştirip $H'(x)$'i yalnız bırakalım:")
    Hx = y_lnduzelt(simplify(thg_dx_kat - N_diffx))
    yol2.append(fr"$H'(x)= {latex(Hx)}$")
    yol2.append("Her iki tarafında $x$'e göre integralini alalım:")
    Hx = y_lnduzelt(integrate(Hx, x_s))
    yol2.append(fr"$H(x)= {latex(Hx)}$")
    tdd_cevap2 = y_lnduzelt(Eq(F, N_inty + Hx, evaluate=False))
    yol2.append(tdd_cevap2)

    adimlar_listesi.append(YanYana("1", yol1, "2", yol2))

    adimlar_listesi.append(f"Bulduğumuz ilk çözüm: ${latex(y_lnduzelt(expand(M_intx + Hy)))}$, ikinci çözüm: ${latex(y_lnduzelt(expand(N_inty + Hx)))}$ olduğundan her iki yolda bizi aynı çözüme götürüyor.")


    pdf_raporu_olustur("ÇÖZÜM RAPORU", adimlar_listesi, f"Cozum_{zaman_etiketi}")