import streamlit as st
import easyocr
import cv2
import numpy as np
import pandas as pd
import re
import psycopg2
from PIL import Image
import io


database = psycopg2.connect(host="localhost", user="postgres", password="Jaya9698", port=5432, database="bizcard")
jk = database.cursor()
reader = easyocr.Reader(['en'], gpu = False)

st.set_page_config(page_title="Bizcard_Data_Extraction", page_icon="",layout="wide")

st.title("BizCardX: Extracting Business Card Data with OCR")

tab1, tab2, tab3, tab4 =st.tabs(["Home","Upload","View/modify","About"])

with tab1:
    st.subheader("Welcome to the Business Card Information Extraction Application! ")
    st.markdown("* This application is designed to make your life easier when it comes to extracting relevant information from business cards. With just a few clicks, you can upload an image of a business card and have the important details extracted using easyOCR."
                " Once the image is uploaded, our powerful OCR technology will analyze it and retrieve essential information such as the company name, cardholder name, designation, mobile number, email address, website URL, area, city, state, and pin code. The extracted information will be neatly displayed in the graphical user interface (GUI) for your convenience.")
    st.markdown("* Our application goes a step further by allowing you to save the extracted information into a database. You can store multiple entries from the corresponding extracted details. This way, you can easily access and manage your business card information whenever you need it."
                " In addition to saving information, the application provides you with the ability to read, update, and delete data directly through the user-friendly Streamlit interface. Whether you want to review a specific entry, make changes to contact details, or remove outdated information, it's just a click away.")
    st.markdown("* Experience our Business Card Information Extraction Application and Say goodbye to manual data entry and embrace an effortless way to manage your business cards.")

def card_extract(extract):
    for i in range(len(extract)):
        extract[i] = extract[i].rstrip(' ')
        extract[i] = extract[i].rstrip(',')
    result = ' '.join(extract)

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    website_pattern = r'[www|WWW|wwW]+[\.|\s]+[a-zA-Z0-9]+[\.|\][a-zA-Z]+'
    phone_pattern = r'(?:\+)?\d{3}-\d{3}-\d{4}'
    phone_pattern2 = r"(?:\+91[-\s])?(?:\d{4,5}[-\s])?\d{3}[-\s]?\d{4}"
    name_pattern = r'[A-Za-z]+\b'
    designation_pattern = r'\b[A-Za-z\s]+\b'
    address_pattern = r'\d+\s[A-Za-z\s,]+'
    pincode_pattern = r'\b\d{6}\b'

    name = designation = company = email = website = primary = secondary = address = pincode = None

    try:
        email = re.findall(email_pattern, result)[0]
        result = result.replace(email, '')
        email = email.lower()
    except IndexError:
        email = None
    try:
        website = re.findall(website_pattern, result)[0]
        result = result.replace(website, '')
        website = re.sub('[WWW|www|wwW]+ ', 'www.', website)
        website = website.lower()
    except IndexError:
        webstie = None
    phone = re.findall(phone_pattern, result)
    if len(phone) == 0:
        phone = re.findall(phone_pattern2, result)
    primary = None
    secondary = None
    if len(phone) > 1:
        primary = phone[0]
        secondary = phone[1]
        for i in range(len(phone)):
            result = result.replace(phone[i], '')
    elif len(phone) == 1:
        primary = phone[0]
        result = result.replace(phone[0], '')

    try:
        pincode = int(re.findall(pincode_pattern, result)[0])
        result = result.replace(str(pincode), '')
    except:
        pincode = 0
    name = extract[0]
    result = result.replace(name, '')
    designation = extract[1]
    result = result.replace(designation, '')
    address = ''.join(re.findall(address_pattern, result))
    result = result.replace(address, '')
    company = extract[-1]
    result = result.replace(company, '')

    info = [name, designation, company, email, website, primary, secondary, address, pincode, result]
    return (info)

with tab2:
    uploaded_file = st.file_uploader("Choose a image file",type=["jpg", "jpeg", "png"])
    if uploaded_file != None:
        image = cv2.imdecode(np.fromstring(uploaded_file.read(), np.uint8), 1)
        col1, col2, col3 = st.columns([2,1,2])
        with col1:
            st.image(image)
        with col3:
            result = reader.readtext(image, detail=0)
            info = card_extract(result)
            ls_name = st.text_input('Name:',info[0])
            ls_desig = st.text_input('Designation:', info[1])
            ls_Com = st.text_input('Company:', info[2])
            ls_mail = st.text_input('Email ID:', info[3])
            ls_url = st.text_input('Website:', info[4])
            ls_m1 = st.text_input('Primary Contact:', info[5])
            ls_m2 = st.text_input('Secondary Contact:', info[6])
            ls_add = st.text_input('Address:', info[7])
            ls_pin = st.number_input('Pincode:', info[8])
            ls_oth = st.text_input('Others(this will not stored):', info[9])
            a = st.button("upload")
            if a:
                jk.execute(
                    "CREATE TABLE IF NOT EXISTS business_cards (name VARCHAR(255), designation VARCHAR(255), "
                    "company VARCHAR(255), email VARCHAR(255), website VARCHAR(255), primary_no VARCHAR(255), "
                    "secondary_no VARCHAR(255), address VARCHAR(255), pincode int, image bytea)")
                query = "INSERT INTO business_cards (name, designation, company, email, website, primary_no, secondary_no, " \
                      "address, pincode, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (ls_name, ls_desig, ls_Com, ls_mail, ls_url, ls_m1, ls_m2, ls_add, ls_pin, psycopg2.Binary(image))
                jk.execute(query, val)
                database.commit()
                st.success('Contact stored successfully in database', icon="✅")

with tab3:
    col1, col2, col3 = st.columns([2,2,4])
    with col1:
        jk.execute('select name from business_cards')
        y = jk.fetchall()
        contact = [x[0] for x in y]
        contact.sort()
        selected_contact = st.selectbox('Name',contact)
    with col2:
        mode_list = ['','View','Modify','Delete']
        selected_mode = st.selectbox('Mode',mode_list,index = 0)

    if selected_mode == 'View':
        col5,col6 = st.columns(2)
        with col5:
            jk.execute(f"select name, designation, company, email, website, primary_no, secondary_no, "
                         f"address, pincode from business_cards where name = '{selected_contact}'")
            y = jk.fetchall()
            st.table(pd.Series(y[0],index=['Name', 'Designation', 'Company', 'Email ID', 'Website', 'Primary Contact', 'Secondary Contact', 'Address', 'Pincode'],name='Card Info'))

    elif selected_mode == 'Modify':
        jk.execute(f"select name, designation, company, email, website, primary_no, secondary_no, "
                     f"address, pincode from business_cards where name = '{selected_contact}'")
        info = jk.fetchone()
        col5, col6 = st.columns(2)
        with col5:
            ls_name = st.text_input('Name:', info[0])
            ls_desig = st.text_input('Designation:', info[1])
            ls_Com = st.text_input('Company:', info[2])
            ls_mail = st.text_input('Email ID:', info[3])
            ls_url = st.text_input('Website:', info[4])
            ls_m1 = st.text_input('Primary Contact:', info[5])
            ls_m2 = st.text_input('Secondary Contact:', info[6])
            ls_add = st.text_input('Address:', info[7])
            ls_pin = st.number_input('Pincode:', info[8])
        a = st.button("Update")
        if a:
            query = f"update business_cards set name = %s, designation = %s, company = %s, email = %s, website = %s, " \
                    f"primary_no = %s, secondary_no = %s, address = %s, pincode = %s where name = '{selected_contact}'"
            val = (ls_name, ls_desig, ls_Com, ls_mail, ls_url, ls_m1, ls_m2, ls_add, ls_pin)
            jk.execute(query, val)
            database.commit()
            st.success('Contact updated successfully in database', icon="✅")

    elif selected_mode == 'Delete':
        st.markdown(
            f'__<p style="text-align:left; font-size: 20px; color: #FAA026">You are trying to remove {selected_contact} '
            f'contact from database.</P>__',
            unsafe_allow_html=True)
        warning_content = """
            **Warning:**
            This action will permanently delete the contact from the database and cannot be recovered. 
            Please review and confirm..
        """
        st.warning(warning_content)
        confirm = st.button('Confirm')
        if confirm:
            query = f"DELETE FROM business_cards where name = '{selected_contact}'"
            jk.execute(query)
            database.commit()
            st.success('Contact removed successfully from database', icon="✅")

with tab4:
    st.markdown('__<p style="text-align:left; font-size: 20px; color: #FFC107">Applications and Packages Used :</P>__',
                    unsafe_allow_html=True)
    st.write("  * Python")
    st.write("  * PostgresSql")
    st.write("  * Streamlit")
    st.write("  * Pandas, Psycopg2, EasyOCR, Re, CV2")
    st.markdown('__<p style="text-align:left; font-size: 20px; color: #FFC107">Contact me with :</P>__',
                unsafe_allow_html=True)
    st.write("LinkedIn : https://www.linkedin.com/in/jaya-krishna-s-aab674196/")
    st.write("Email ID : jkbioinfo99@gmail.com")
    st.write("Github : https://github.com/JayaKrishanS")
