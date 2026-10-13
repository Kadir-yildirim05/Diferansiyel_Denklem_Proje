from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import List, Optional

import streamlit as st
from sympy import Eq, Function, Symbol, diff, exp, integrate, simplify, symbols, latex

from difsolv_engine import (
    detect_equation_type,
    generate_audio_bytes,
    generate_pdf_bytes,
    solve_equation,
)

st.set_page_config(page_title="Difsolv", page_icon="∫", layout="wide")

EQUATION_TYPES = [
    "Tür Bulma",
    "Değişkenlerine Ayrılabilen",
    "Tam",
    "Homojen",
    "Lineer",
    "Bernoulli",
    "Tam Hale Gelebilir",
]


def init_session():
    if "active_type" not in st.session_state:
        st.session_state.active_type = "Tür Bulma"
    if "equation" not in st.session_state:
        st.session_state.equation = "y' + 2*x*y = 5"
    if "detected_type" not in st.session_state:
        st.session_state.detected_type = ""
    if "methods" not in st.session_state:
        st.session_state.methods = []
    if "steps" not in st.session_state:
        st.session_state.steps = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes = b""
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = b""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False


def render_header():
    st.markdown(
        """
        <style>
        .difsolv-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.25rem 0 1rem 0;
            border-bottom: 1px solid rgba(148,163,184,0.35);
            margin-bottom: 1rem;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f172a;
        }
        .brand-logo {
            width: 2.3rem;
            height: 2.3rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            box-shadow: 0 8px 18px rgba(37,99,235,0.28);
            font-size: 1.2rem;
        }
        .top-actions {
            display: flex;
            gap: 0.75rem;
            justify-content: flex-end;
        }
        .action-btn {
            padding: 0.6rem 1rem;
            border-radius: 12px;
            border: 1px solid rgba(37,99,235,0.25);
            background: white;
            color: #0f172a;
            font-weight: 600;
        }
        .primary-btn {
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            border: none;
            box-shadow: 0 10px 18px rgba(79,70,229,0.24);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([4, 2])
    with left_col:
        st.markdown(
            '<div class="brand"><span class="brand-logo">∫</span> Difsolv</div>',
            unsafe_allow_html=True,
        )
    with right_col:
        action_buttons = st.columns(2)
        with action_buttons[0]:
            if st.button("Giriş Yap", key="login_btn"):
                st.session_state.logged_in = not st.session_state.logged_in
        with action_buttons[1]:
            if st.button("Kaydol", key="signup_btn"):
                st.session_state.logged_in = True


@st.cache_data
def cached_detect(equation: str):
    return detect_equation_type(equation)


def detect_and_store():
    equation = st.session_state.equation.strip()
    if not equation:
        st.warning("Denklem alanı boş olamaz.")
        return
    try:
        detected_type, methods = cached_detect(equation)
        st.session_state.detected_type = detected_type
        st.session_state.methods = methods
        st.session_state.steps = []
    except Exception as exc:  # pragma: no cover - UI safety
        st.error(f"Tür tespitinde hata oluştu: {exc}")
        st.session_state.detected_type = "Bilinmeyen"
        st.session_state.methods = []


def solve_current_method(method: str):
    equation = st.session_state.equation.strip()
    if not equation:
        st.warning("Önce denklemi girin.")
        return
    try:
        steps = solve_equation(equation, method)
        st.session_state.steps = steps
        st.session_state.history.append(
            {"equation": equation, "method": method, "steps": steps}
        )
        st.session_state.history = st.session_state.history[-10:]
        st.session_state.audio_bytes = generate_audio_bytes(equation, steps)
        st.session_state.pdf_bytes = generate_pdf_bytes(equation, steps, method)
    except Exception as exc:  # pragma: no cover - UI safety
        st.error(f"Çözüm üretilirken hata oluştu: {exc}")


def render_left_panel():
    st.markdown("### Denklem Türleri")
    for item in EQUATION_TYPES:
        button_key = f"nav_{item}"
        selected = st.session_state.active_type == item
        label = item
        if st.button(
            label,
            key=button_key,
            use_container_width=True,
            type="primary" if selected else "secondary",
        ):
            st.session_state.active_type = item
            if item != "Tür Bulma":
                st.session_state.detected_type = item
                st.session_state.methods = [item]


def render_center_panel():
    st.markdown("### Ana Çalışma Alanı")
    equation = st.text_area(
        "Denkleminizi yazın",
        value=st.session_state.equation,
        height=120,
        key="equation_input",
    )
    st.session_state.equation = equation

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Türü Bul", use_container_width=True):
            detect_and_store()
    with col2:
        if st.button("Temizle", use_container_width=True):
            st.session_state.steps = []
            st.session_state.detected_type = ""
            st.session_state.methods = []
            st.session_state.equation = ""

    if st.session_state.detected_type:
        st.markdown(f"#### Tespit edilen tür: **{st.session_state.detected_type}**")

    if st.session_state.methods:
        st.markdown("#### Uygun yöntemler")
        method_cols = st.columns(min(3, len(st.session_state.methods)))
        for idx, method in enumerate(st.session_state.methods):
            with method_cols[idx % len(method_cols)]:
                if st.button(method, key=f"method_{idx}", use_container_width=True):
                    solve_current_method(method)

    st.markdown("### Adım Adım Çözüm")
    if not st.session_state.steps:
        st.info("Henüz çözüm üretmediniz. Denklem girip türü bulun veya yöntem seçin.")
        return

    for idx, step in enumerate(st.session_state.steps, start=1):
        st.markdown(f"**Adım {idx}:**")
        st.latex(step)


def render_right_panel():
    st.markdown("### Geçmiş")
    if st.session_state.logged_in:
        if not st.session_state.history:
            st.info("Kayıtlı çözüm bulunamadı.")
        else:
            for item in reversed(st.session_state.history):
                with st.container():
                    st.caption(item["equation"])
                    st.write(item["method"])
                    if st.button(f"Aç: {item['equation'][:24]}", key=f"history_{item['equation']}_{len(item['steps'])}"):
                        st.session_state.steps = item["steps"]
                        st.session_state.detected_type = item["method"]
    else:
        st.info("Geçmiş listesi için giriş yapmanız gerekir.")

    st.markdown("### Ses & PDF")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.download_button(
            label="Ses dosyasını indir",
            data=st.session_state.audio_bytes,
            file_name="difsolv_ses.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )
    else:
        st.info("Henüz ses üretimi yapılmadı.")

    if st.session_state.pdf_bytes:
        st.download_button(
            label="PDF indir",
            data=st.session_state.pdf_bytes,
            file_name="difsolv_cozum.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info("Henüz PDF üretimi yapılmadı.")


def main():
    init_session()
    render_header()

    left_col, center_col, right_col = st.columns([1.5, 4.3, 2.3])
    with left_col:
        render_left_panel()
    with center_col:
        render_center_panel()
    with right_col:
        render_right_panel()


if __name__ == "__main__":
    main()
