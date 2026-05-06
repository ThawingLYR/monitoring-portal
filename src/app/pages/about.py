# Imports
import streamlit as st

from src.app.version import VERSION

# Set page configuration
st.set_page_config(page_title="About", layout="wide")
st.title("About")

st.write("empty page")

st.write("This application runs on version: {}".format(VERSION))
