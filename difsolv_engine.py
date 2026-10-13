from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sympy as sp
from gtts import gTTS
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def normalize_equation(raw: str) -> str:
    if raw is None:
        raise ValueError("Denklem boş olamaz.")
    text = str(raw).strip()
    if not text:
        raise ValueError("Denklem boş olamaz.")
    text = text.replace("×", "*").replace("÷", "/")
    text = text.replace("–", "-").replace("−", "-")
    return text


def _legacy_candidates():
    try:
        import importlib.util

        repo_root = Path(__file__).resolve().parent
        legacy_path = repo_root / "tür_ile_çözüm_birleştirme_bütünü_30.py"
        if legacy_path.exists():
            spec = importlib.util.spec_from_file_location("legacy_solver", legacy_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception:
        return None
    return None


LEGACY_SOLVER = _legacy_candidates()


def detect_equation_type(raw: str) -> Tuple[str, List[str]]:
    text = normalize_equation(raw)
    lower = text.lower()

    if LEGACY_SOLVER is not None:
        try:
            if hasattr(LEGACY_SOLVER, "classify_ode"):
                x = sp.Symbol("x")
                y = sp.Function("y")
                expr = sp.sympify(text.replace("y'", "Derivative(y(x), x)"), locals={"x": x, "y": y})
                result = LEGACY_SOLVER.classify_ode(sp.Eq(expr, 0), y(x))
                if result:
                    methods = [
                        "Değişkenlerine Ayrılabilen",
                        "Tam",
                        "Homojen",
                        "Lineer",
                        "Bernoulli",
                        "Tam Hale Gelebilir",
                    ]
                    return "Tespit Edildi", methods
        except Exception:
            pass

    if "y'" in text or "dy/dx" in lower or "derivative" in lower:
        if re.search(r"y\s*\+\s*P\(x\)|y\s*\+\s*.*\*\s*y|y'\s*\+\s*", text):
            return "Lineer", ["Lineer", "Değişkenlerine Ayrılabilen", "Tam"]
        if "y" in text and "x" in text and re.search(r"y\s*\*\s*y|x\s*\*\s*y|y\^", text):
            return "Homojen", ["Homojen", "Değişkenlerine Ayrılabilen", "Tam"]
        return "Değişkenlerine Ayrılabilen", ["Değişkenlerine Ayrılabilen", "Lineer", "Tam"]

    if "dx" in lower or "dy" in lower:
        return "Tam", ["Tam", "Tam Hale Gelebilir", "Lineer"]

    return "Bilinmeyen", ["Tür Bulma", "Değişkenlerine Ayrılabilen", "Lineer", "Tam"]


def _clean_latex_steps(steps: List[str]) -> List[str]:
    cleaned: List[str] = []
    for step in steps:
        text = str(step).strip()
        if not text:
            continue
        cleaned.append(text.replace("\\n", " "))
    return cleaned


def solve_equation(raw: str, method: str = None) -> List[str]:
    text = normalize_equation(raw)
    method = (method or "Tür Bulma").strip()
    x = sp.Symbol("x")
    y = sp.Function("y")

    if method in {"Tür Bulma", "Değişkenlerine Ayrılabilen"}:
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\text{Denklem } \frac{dy}{dx}=f(x)g(y) \text{ biçimindedir.}",
            r"\text{İki tarafın } x \text{ ve } y \text{ değişkenlerine göre integrali alınır.}",
            r"\boxed{\int \frac{dy}{g(y)} = \int f(x)dx + C}",
        ])

    if method == "Lineer":
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\text{Form: } y' + P(x)y = Q(x)",
            r"\mu(x)=e^{\int P(x)dx}",
            r"\frac{d}{dx}(\mu(x)y)=\mu(x)Q(x)",
            r"\boxed{y=\frac{1}{\mu(x)}\left(\int \mu(x)Q(x)dx + C\right)}",
        ])

    if method == "Tam":
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\text{Denklem } M(x,y)dx + N(x,y)dy = 0 \text{ biçimine getirilir.}",
            r"M_y = N_x \text{ kontrol edilir.}",
            r"\text{Daha sonra } F(x,y) = \int M dx + g(y) \text{ veya } F = \int N dy + h(x)",
            r"\boxed{F(x,y)=C}",
        ])

    if method == "Homojen":
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\text{Denklem } y' = f(x,y) \text{ ve } f(tx,ty)=t^n f(x,y) \text{ koşulunu sağlar.}",
            r"y = vx \text{ dönüşümü yapılır.}",
            r"\frac{dy}{dx} = v + x\frac{dv}{dx}",
            r"\boxed{\text{Sonraki adım: değişkenlere ayrılır ve integral alınır.}}",
        ])

    if method == "Bernoulli":
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\text{Bernoulli formu: } y' + P(x)y = Q(x)y^n",
            r"u = y^{1-n} \text{ dönüşümü yapılır.}",
            r"\frac{du}{dx} + (1-n)P(x)u = (1-n)Q(x)",
            r"\boxed{\text{Lineer denklem elde edilir; çözülür.}}",
        ])

    if method == "Tam Hale Gelebilir":
        return _clean_latex_steps([
            r"\text{Verilen denklem: } " + text,
            r"\mu(x,y) \text{ integral çarpanı aranır.}",
            r"\text{Eğer } \frac{M_y-N_x}{N} \text{ sadece } x \text{e bağlı ise } \mu = e^{\int f(x)dx}",
            r"\text{veya } \frac{N_x-M_y}{M} \text{ sadece } y \text{ye bağlı ise } \mu = e^{\int f(y)dy}",
            r"\boxed{\mu(x,y)\cdot(Mdx+Ndy)=0 \rightarrow \text{tam diferansiyel hale gelir.}}",
        ])

    return _clean_latex_steps([
        r"\text{Verilen denklem: } " + text,
        r"\text{Yöntem tanımlanmamış; tür analizi yapılır.}",
        r"\boxed{\text{İlgili yöntem seçilerek çözüm devam ettirilir.}}",
    ])


def generate_pdf_bytes(equation: str, steps: List[str], method: str = "") -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setTitle("Difsolv Çözüm Raporu")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 60, "Difsolv - Çözüm Raporu")
    c.setFont("Helvetica", 12)
    c.drawString(60, height - 90, f"Denklem: {equation}")
    c.drawString(60, height - 110, f"Yöntem: {method or 'Tespit Edildi'}")

    y = height - 150
    for idx, step in enumerate(steps, start=1):
        text = step.replace(r"\text{", "").replace("}", "")
        text = text.replace(r"\boxed{", "")
        text = text.replace(r"\frac", "")
        text = text.replace(r"\left", "")
        text = text.replace(r"\right", "")
        text = text.replace(r"\\", " ")
        text = text.replace("{", "").replace("}", "")
        lines = [text[i : i + 80] for i in range(0, len(text), 80)]
        for line in lines:
            if y < 80:
                c.showPage()
                y = height - 60
            c.drawString(60, y, f"{idx}. {line}")
            y -= 18
    c.save()
    return buffer.getvalue()


def generate_audio_bytes(equation: str, steps: List[str]) -> bytes:
    speech_text = f"Denklem: {equation}. " + " ".join(steps)
    speech_text = re.sub(r"\\text\{([^}]*)\}", r"\1", speech_text)
    speech_text = speech_text.replace("{", "").replace("}", "")
    speech_text = speech_text.replace("\\", " ")
    speech_text = speech_text.replace("_", " ")
    audio = gTTS(text=speech_text, lang="tr")
    stream = io.BytesIO()
    audio.write_to_fp(stream)
    stream.seek(0)
    return stream.getvalue()
