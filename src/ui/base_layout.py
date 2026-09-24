import streamlit as st


def style_background_home():

    st.markdown("""
        <style>

        /* Main background */
        .stApp {
            background:
                radial-gradient(circle at 10% 15%, #C8CEFF 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, #AEB8FF 0%, transparent 22%),
                radial-gradient(circle at 50% 50%, #F5F6FF 0%, #EEF0FF 70%);
            background-attachment: fixed;
        }


        /* Soft background effect */
        .stApp::before {
            content: "";
            position: fixed;
            width: 350px;
            height: 350px;
            top: -120px;
            left: -100px;
            background: #B8C0FF;
            border-radius: 50%;
            filter: blur(60px);
            opacity: 0.45;
            z-index: 0;
        }


        .stApp::after {
            content: "";
            position: fixed;
            width: 350px;
            height: 350px;
            bottom: -150px;
            right: -100px;
            background: #9FAAFF;
            border-radius: 50%;
            filter: blur(70px);
            opacity: 0.45;
            z-index: 0;
        }


        /* Student / Teacher cards */
        .stApp div[data-testid="stColumn"] {
            background: #FFFFFF !important;
            padding: 2.5rem !important;
            border-radius: 2rem !important;

            box-shadow:
                0 15px 35px rgba(88, 101, 232, 0.12);

            transition: transform 0.25s ease,
                        box-shadow 0.25s ease;
        }


        /* Card hover */
        .stApp div[data-testid="stColumn"]:hover {
            transform: translateY(-6px);

            box-shadow:
                0 20px 45px rgba(88, 101, 232, 0.18);
        }

        </style>
    """, unsafe_allow_html=True)


def style_background_dashboard():

    st.markdown("""
        <style>

        .stApp {
            background:
                radial-gradient(circle at 10% 15%, #C8CEFF 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, #AEB8FF 0%, transparent 22%),
                #EEF0FF;

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

            color: #5865E8 !important;

            text-align: center;
        }


        /* Secondary heading */

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;

            font-size: 2rem !important;

            line-height: 0.9 !important;

            margin-bottom: 0rem !important;

            color: #5865E8 !important;
        }


        /* Normal text */

        h3,
        h4,
        p {
            font-family: 'Outfit', sans-serif !important;
        }


        /* Primary button */

        button {
            border-radius: 1.5rem !important;

            background-color: #5865E8 !important;

            color: white !important;

            padding: 10px 20px !important;

            border: none !important;

            transition: transform 0.25s ease,
                        box-shadow 0.25s ease !important;
        }


        /* Secondary button */

        button[kind="secondary"] {
            border-radius: 1.5rem !important;

            background-color: #7C83F6 !important;

            color: white !important;

            padding: 10px 20px !important;

            border: none !important;
        }


        /* Tertiary button */

        button[kind="tertiary"] {
            border-radius: 1.5rem !important;

            background-color: #1F2937 !important;

            color: white !important;

            padding: 10px 20px !important;

            border: none !important;
        }


        /* Button hover */

        button:hover {
            transform: scale(1.05);

            box-shadow:
                0 8px 20px rgba(88, 101, 232, 0.25);
        }

        </style>
    """, unsafe_allow_html=True)