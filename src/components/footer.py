import streamlit as st
from pathlib import Path
import base64

# Project root locate karna (footer.py -> components -> src -> root)
BASE_DIR = Path(__file__).resolve().parents[2]
LOGO_PATH = BASE_DIR / "img" / "logo.png"


def get_base64_image(image_path: Path):
    if image_path.exists():
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""


def _render_footer():
    img_b64 = get_base64_image(LOGO_PATH)
    img_tag = (
        f'<img src="data:image/png;base64,{img_b64}" width="200" height="140" style="object-fit: contain; vertical-align: middle;" />'
        if img_b64
        else ""
    )

    st.markdown(
        f"""
        <div style="
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            width: 100%;
        ">
            <span style="font-weight: 600; color: #111; font-size: 15px; margin: 0;">
                Created by Hamid Ansari
            </span>
            {img_tag}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Dono functions define kar diye taaki koi bhi screen import kare to error na aaye
def footer_home():
    _render_footer()


def footer_dashboard():
    _render_footer()