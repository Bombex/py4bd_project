import streamlit as st
from streamlit_extras.app_logo import add_logo

add_logo(
    ".streamlit/mandarin.png",
    height=250
)

st.title('About')

"""You can improve the animal species search model by submitting datasets of animal images. 
Please make sure that the species are defined correctly.
"""
st.title('The process of submitting a dataset')

"""
The process of submitting a photo:
1. Folders with the Latin (scientific) name of species
2. Photos of animals in .JPG format attached to the corresponding folders
3. Upload the images to Google Drive or any other cloud storage
4. Go to our [Google Form](https://docs.google.com/forms/d/e/1FAIpQLScPs999lGn_cPlfLMHlB9jNZUXgrIwJLTtLG8p8zKsD1bBxJg/viewform?usp=sharing) and fill it out.
"""