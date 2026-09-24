import streamlit as st


def style_background_home():

    st.markdown("""
        <style>

        /* Dark main background */
        .stApp {
            background:
                radial-gradient(circle at 10% 10%, #252B55 0%, transparent 25%),
                radial-gradient(circle at 90% 85%, #1D2850 0%, transparent 25%),
                #0B1020;

            background-attachment: fixed;
        }


        /* Soft glow */
        .stApp::before {
            content: "";
            position: fixed;

            width: 350px;
            height: 350px;

            top: -120px;
            left: -100px;

            background: #5865E8;

            border-radius: 50%;

            filter: blur(100px);

            opacity: 0.20;

            z-index: 0;
        }


        .stApp::after {
            content: "";
            position: fixed;

            width: 350px;
            height: 350px;

            bottom: -150px;
            right: -100px;

            background: #7C83F6;

            border-radius: 50%;

            filter: blur(100px);

            opacity: 0.18;

            z-index: 0;
        }


        /* Student / Teacher cards */

        .stApp div[data-testid="stColumn"] {
            background: #FFFFFF !important;

            padding: 2.5rem !important;

            border-radius: 2rem !important;

            box-shadow:
                0 15px 40px rgba(0, 0, 0, 0.30);

            transition:
                transform 0.25s ease,
                box-shadow 0.25s ease;
        }


        /* Card hover */

        .stApp div[data-testid="stColumn"]:hover {
            transform: translateY(-6px);

            box-shadow:
                0 20px 50px rgba(0, 0, 0, 0.40);
        }


        </style>
    """, unsafe_allow_html=True)


def style_background_dashboard():

    st.markdown("""
        <style>

        /* Dashboard dark background */

        .stApp {
            background:
                radial-gradient(circle at 10% 15%, #252B55 0%, transparent 25%),
                radial-gradient(circle at 90% 80%, #1D2850 0%, transparent 25%),
                #0B1020;

            background-attachment: fixed;
        }

        </style>
    """, unsafe_allow_html=True)


def style_base_layout():

    st.markdown("""
        <style>

        /* Fonts */

        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');

        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');


        /* Hide Streamlit top bar */

        #MainMenu,
        footer,
        header {
            visibility: hidden;
        }


        /* Main container */

        .block-container {
            padding-top: 1.5rem !important;
        }


        /* Main heading */

        h1 {
            font-family: 'Climate Crisis', sans-serif !important;

            font-size: 3.5rem !important;

            line-height: 1.1 !important;

            margin-bottom: 0rem !important;

            color: #FFFFFF !important;

            text-align: center;
        }


        /* Secondary heading */

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;

            font-size: 2rem !important;

            line-height: 0.9 !important;

            margin-bottom: 0rem !important;

            color: #FFFFFF !important;
        }


        /* Normal text */

        h3,
        h4,
        p {
            font-family: 'Outfit', sans-serif !important;

            color: #FFFFFF;
        }


        /* Primary button */

        button {
            border-radius: 1.5rem !important;

            background-color: #5865E8 !important;

            color: #FFFFFF !important;

            padding: 10px 20px !important;

            border: none !important;

            transition:
                transform 0.25s ease,
                box-shadow 0.25s ease !important;
        }


        /* Secondary button */

        button[kind="secondary"] {
            border-radius: 1.5rem !important;

            background-color: #7C83F6 !important;

            color: #FFFFFF !important;

            padding: 10px 20px !important;

            border: none !important;
        }


        /* Tertiary button */

        button[kind="tertiary"] {
            border-radius: 1.5rem !important;

            background-color: #FFFFFF !important;

            color: #111827 !important;

            padding: 10px 20px !important;

            border: none !important;
        }


        /* Button hover */

        button:hover {
            transform: scale(1.05);

            box-shadow:
                0 8px 25px rgba(88, 101, 232, 0.35);
        }


            /* Text inside white cards */

            .stApp div[data-testid="stColumn"] {
                color: #111827 !important;
            }

            .stApp div[data-testid="stColumn"] h1,
            .stApp div[data-testid="stColumn"] h2,
            .stApp div[data-testid="stColumn"] h3,
            .stApp div[data-testid="stColumn"] h4,
            .stApp div[data-testid="stColumn"] p,
            .stApp div[data-testid="stColumn"] span,
            .stApp div[data-testid="stColumn"] label {
                color: #111827 !important;
            }


        </style>
    """, unsafe_allow_html=True)