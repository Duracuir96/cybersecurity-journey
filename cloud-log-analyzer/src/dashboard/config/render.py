# src/dashboard/config/render.py

import streamlit as st


def html(markup):
    """
    Renders raw HTML in Streamlit safely.

    Streamlit passes the string through its Markdown parser, which mis-reads
    lines that start with Markdown block characters ("* ", "#", "-", "N.").
    Collapsing everything to a single line removes all line-starts, so the
    HTML is never turned into bullets, headings or code blocks. HTML is
    whitespace-insensitive between tags, so rendering is unchanged.

    Do NOT use this for pre-formatted content whose line breaks matter
    (e.g. RULE LOGIC code blocks) — render those with st.markdown directly.

    Input  : markup (str) — an HTML string
    Output : None — renders directly into Streamlit
    """
    cleaned = " ".join(line.strip() for line in markup.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)