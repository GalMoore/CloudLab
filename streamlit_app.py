import openai
import streamlit as st
import PyPDF2
import pandas as pd
from io import BytesIO
import json
import time
import tiktoken
import plotly.express as px
import matplotlib.pyplot as plt
import re

# If you want to apply  style uncomment and refresh
# with open( "style.css" ) as css:
#     st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

# st.markdown('<h1 style="font-size:40px;">:sun_behind_cloud::microscope: CloudLab</h1>', unsafe_allow_html=True)
st.title(":sun_behind_cloud::microscope: CloudLab ") # : Your Health Vault 
    
# Set the title of the Streamlit application
# st.title(":sun_behind_cloud::microscope: CloudLab ") # : Your Health Vault 
st.markdown("**:violet[Upload your PDF files on the left sidebar]** and watch the graphs populate below.")

# Set the OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai_password"]

#####################################################
################ CHAT ##############################
# Initialize the session state for the OpenAI model if it doesn't exist, with a default value of "gpt-3.5-turbo-16k"
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] =  "gpt-3.5-turbo-16k" # "gpt-4"

# Initialize the session state for the messages if it doesn't exist, as an empty list
if "messages" not in st.session_state:
    st.session_state.messages = []

# Wait for the user to input a message
if prompt := st.chat_input("What would you like to know about these documents?"):
    # If the user inputs a message, clear previous messages and append the new one with the role "user"
    st.session_state.messages = [{"role": "user", "content": prompt}]
    # Display the user's message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare for the assistant's message
    with st.chat_message("assistant"):
        # Create a placeholder for the assistant's message
        message_placeholder = st.empty()
        # Initialize an empty string to build up the assistant's response
        full_response = ""
        # Generate the assistant's response using OpenAI's chat model, with the current session's messages as context
        # The response is streamed, which means it arrives in parts that are appended to the full_response string
        for response in openai.ChatCompletion.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        ):
            # Append the content of the new part of the response to the full_response string
            full_response += response.choices[0].delta.get("content", "")
            # Update the assistant's message placeholder with the current full_response string, appending a "▌" to indicate it's still typing
            message_placeholder.markdown(full_response + "▌")
        # Once the full response has been received, update the assistant's message placeholder without the "▌"
        message_placeholder.markdown(full_response)
    # Append the assistant's full response to the session's messages with the role "assistant"
    st.session_state.messages.append({"role": "assistant", "content": full_response})

#################################################################

# Add a file uploader to the sidebar for the user to upload files
uploaded_files = st.sidebar.file_uploader("",accept_multiple_files=True, type=['pdf'])

# # Initialize the number of uploaded files in session state
# if 'num_uploaded_files' not in st.session_state:
#     st.session_state.num_uploaded_files = 0

# # When a new PDF is uploaded:
# if len(uploaded_files) != st.session_state.num_uploaded_files:
#     st.session_state.new_pdf_uploaded = True
#     st.session_state.num_uploaded_files = len(uploaded_files)
# else:
#     st.session_state.new_pdf_uploaded = False

# if st.session_state.new_pdf_uploaded:    
# Initialize an empty list to store the extracted text from the uploaded files
data = []
filenames = []
# Loop over each uploaded file
if uploaded_files:
    st.sidebar.write("You have uploaded the following files:")
    for file in uploaded_files:
        st.sidebar.write(file.name)
        # Open the file as a stream
        file_stream = BytesIO(file.read())
        # Create a PDF file reader object
        pdf_reader = PyPDF2.PdfFileReader(file_stream)
        text = ""
        # Loop over each page in the PDF and extract the text
        for page in range(pdf_reader.getNumPages()):
            text += pdf_reader.getPage(page).extract_text()
        # Append the text to the data list
        data.append(text)
        # Append the filename to the filenames list
        filenames.append(file.name)

# Create a DataFrame
df = pd.DataFrame(data, columns=['Text'], index=filenames)

# Convert text to lowercase
df['Text'] = df['Text'].str.lower()

##############################################################
# DEBUG 1 #
# st.write(df)  # This line will display the initial dataframe on the Streamlit UI. 
# The dataframe contains the text extracted from uploaded PDF documents. 

# # check if 'df' exists and is not empty
# if 'df' in locals() and not df.empty:
#     # Check if 'Text' column exists in the DataFrame
#     if 'Text' in df.columns:
#         # st.success('Extracted text from pdfs of lab results', icon="✅")
#         st.markdown('<small><p style="color:green;">✅ Extracted text from pdfs of lab results</p></small>', unsafe_allow_html=True)
#         st.markdown('<small><p style="color:gray;">We are processing your data... Allow up to 10 seconds per page</p></small>', unsafe_allow_html=True)


########### ANONIMIZE DATA (CHOP OFF IDENTIFYING TEXT ###########
#################################################################
def remove_lines(text):
    # find the index of 'blood gas analysis' in the text
    start_index = re.search('blood gas analysis', text, re.IGNORECASE)
    # return the substring from 'blood gas analysis' to the end
    if start_index:
        return text[start_index.start():]
    else:
        return text
# Apply the function to the 'Text' column and store the result in a new column 'Clean_Text'
df['Text'] = df['Text'].apply(remove_lines)
##################################################################

############ DEINFE EXAMPLE_DOCUMENT FOR ONE SHORT LEARNING #########
# hard code the doc from 14/3/23
example_document = """blood gas analysis
acid/base balance
ph 7.458     14/03/2023 14/03/2023
pco2 40.9  mmhg   14/03/2023 14/03/2023
po2 56.0  mmhg   14/03/2023 14/03/2023
hco3 (bicarbonate)-calc. 28.3  mmol/l   14/03/2023 14/03/2023
base excess 4.1  mmol/l   14/03/2023 14/03/2023

co-oxymetry
hematocrit 29 l % 40 - 52 *[.........]  14/03/2023 14/03/2023
hemoglobin 10.0 l g/dl 13.5 - 17.5*[.........]  14/03/2023 14/03/2023
saturation, o2 88.4 l % 94.0 - 98.0*[.........]  14/03/2023 14/03/2023

oxyhemoglobin 88.0  %   14/03/2023 14/03/2023
carboxyhemoglobin 0.2 l % 1.0 - 2.0*[.........]  14/03/2023 14/03/2023
תחום ייחוס למבוגרים לא מעשנים
methemoglobin 0.3 l % 0.5 - 1.3*[.........]  14/03/2023 14/03/2023
deoxyhemoglobin 11.5  %   14/03/2023 14/03/2023

electrolytes
sodium 140  meq/l 136 - 148 [..*......]  14/03/2023 14/03/2023
potassium 3.9  meq/l 3.5 - 5.2 [..*......]  14/03/2023 14/03/2023
potassium - לא נשללה המוליזה ל
calcium, ionized 0.39 l mmol/l1.00 - 1.20*[.........]  14/03/2023 14/03/2023
גורם לערכים נמוכים של קלציום יוניעודף הפרין
האחרות, מומלץ לחזור עלומשנה את תוצאות הבדיקות
הבדיקה ולהמנע מעודף הפרין
chloride 98  meq/l 98 - 110 [*........]  14/03/2023 14/03/2023
anion gap 17.2  meq/l10.0 - 22.0 [.....*...]  14/03/2023 14/03/2023

metabolites
glucose 147 h mg/dl 70 - 100 [.........]* 14/03/2023 14/03/2023
תחום יחוס לנבדקים בצום בלבד
lactate 13  mg/dl 6 - 18  [.....*...]  14/03/2023 14/03/2023

.יש להתייחס למסמך במלואו. העתקת חלקים ממנו למסמכים אחרים עלולה לפגוע במשמעות התוצאה/ות
https://www .sheba.co.il/ המעבדות_אגף   :מידע אודות הבדיקות ניתן למצוא באתר שיבא
דוח תוצאות 01:12 14/03/2023-ב    4.11.0 גירסה  labos  הופק ע"יכל הזכויות שמורות """
##########################################################

########### DEFINE DESIRED OUTPUT FOR ONE SHORT LEARNING #########
example_outcome_values = {
    "ph": 7.458, "pco2": 40.9, "po2": 56.0, "hco3 (bicarbonate)-calc.": 28.3, "base excess": 4.1,
    "hematocrit": 29, "hemoglobin": 10.0, "saturation, o2": 88.4, "oxyhemoglobin": 88.0, "carboxyhemoglobin": 0.2,
    "methemoglobin": 0.3, "deoxyhemoglobin": 11.5, "sodium": 140, "potassium": 3.9, "calcium, ionized": 0.39,
    "chloride": 98, "anion gap": 17.2, "glucose": 147, "lactate": 13,
}
####################################################################

###### DEFINE PROMPT #########
bot_description = "You are an Israeli nurse in ICU with 20 years experience."

instruction = "look through the document and look at each value in the\
                        example. Think step by step. Only if you \
                        can find the value in this document tell me what the reading is. \
                        if there is no value for a particular test, leave it blank. \
                        for the results that you have found, return a dictionary with the lab results like this:"
###############################

########### CHAT FUINCTION ##############
def get_chat_responses(df, example_document, example_outcome = example_outcome_values, \
                       output_as_dict=True, name_of_new_col="Messages", \
                       bot_description=bot_description, instruction=instruction, zero_shot_instruction =" " ):
    MAX_ATTEMPTS = 3     # Maximum number of attempts to get a valid dictionary from ChatCompletion
    df[f'{name_of_new_col}'] = pd.Series(dtype=object) # Initialize a new column 'Messages' with dtype object
    for index, row in df.iterrows():
        document_text = row['Text']
        for attempt in range(MAX_ATTEMPTS):
            print(f"Attempt {attempt+1}: collecting text from document in df and sending query to chatgpt ", index)

            try:
                # OpenAI API, passing it the pre-formatted system message and user message
                chat_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        # System message sets the role of the AI and gives instructions
                        {"role": "system", "content": f"{bot_description}. \
                        When I give you a text string \
                        that includes a lab report like this: {example_document}, {instruction} {example_outcome}\
                        "},
                        # User message gives the text string that the AI should process
                        {"role": "user", "content": f"{zero_shot_instruction} {document_text}"}
                    ]
                )

                # print(chat_response)
                content = chat_response["choices"][0]["message"]["content"]
                if output_as_dict:
                    # Replace single quotes in the string with double quotes for JSON compatibility
                    content = content.replace("'", '"')
                    # Try to load the string as a JSON object (equivalent to a Python dictionary)
                    content_dict = json.loads(content)
                    # If successful, store the dictionary directly in the 'name_of_new_col' column of the current row
                    df.at[index, f'{name_of_new_col}'] = content_dict
                else:
                    # If output_as_dict is False, just store the string directly
                    df.at[index, f'{name_of_new_col}'] = content
                break
            except openai.error.ServiceUnavailableError:
                print(f"ServiceUnavailableError, retrying in 5 seconds...")
                time.sleep(5)  # Wait for 5 seconds before next retry
            except json.JSONDecodeError as e:  # If an error occurs during loading
                print(f"Unable to parse message into a dictionary: {e}")
                if attempt == MAX_ATTEMPTS - 1:  # If this was the last attempt
                    print(f"Max attempts reached. Saving message as-is.")
                    df.at[index, f'{name_of_new_col}'] = content  # Save the message as-is
    return df

##########################################################################################

######### GET DICT OF TEST VALUES ONLY #################
df = get_chat_responses(df, example_document, example_outcome=example_outcome_values, output_as_dict=True,\
                        name_of_new_col="Messages", \
                        bot_description = bot_description ,instruction =instruction)
#########################################################

########## TURN DICT VALUES INTO COLUMNS ################
expanded_df = df['Messages'].apply(pd.Series)
# Now, you might want to join this back with your original dataframe:
df_final = pd.concat([df.drop(['Messages'], axis=1), expanded_df], axis=1)
#########################################################
 # check if 'df' exists and is not empty
if 'df_final' in locals() and not df_final.empty:
    # Check if 'Messages' column exists in the DataFrame
    if 'Messages' in df_final.columns:
        # st.success('Extracted the lab values using gpt into a string in df', icon="✅")
        st.markdown('<small><p style="color:green;">✅ Extracted the lab values using gpt into a string in df</p></small>', unsafe_allow_html=True)

##############################################################
# This line will display the updated dataframe on the Streamlit UI after the values 
# from the 'Messages' column have been extracted into their own respective columns. 
# DEBUG 3 #
# st.write(df)

################## EXTRACT DATE ########################
example_date =  "14-03-2023 01:12"
instruction_date = "find the date and time of this document and return a string with the date and time. Do not write any words\
just write the date and time exactly as it appears in this formatted example :"
# instruction_date = "find the date and time of this document and return a string with the date and time. Do not write any words\
# just write the date and time exactly as it appears in this formatted example :",

df_final = get_chat_responses(df_final, example_document, example_outcome=example_date, output_as_dict=False,\
                              name_of_new_col="document_date", bot_description = bot_description ,\
                              instruction = instruction_date)

########## EXTRACT DATE TIME FROM CHATGPT RESPONSE #######
from datetime import datetime
import re

# The regular expression pattern for a date in the "dd-mm-yyyy" or "dd/mm/yyyy" format
date_pattern = r"\d{2}[/-]\d{2}[/-]\d{4}"
# The regular expression pattern for a time in the "hh:mm" format
time_pattern = r"\d{2}:\d{2}"

# Iterate over the DataFrame
for index, row in df_final.iterrows():
    # Extract the original date from the Date column
    original_date_str = row['document_date']
    try:
        # Search for the date and time in the original string
        date_match = re.search(date_pattern, original_date_str)
        time_match = re.search(time_pattern, original_date_str)

        if date_match and time_match:
            # If a date and time are found, extract them
            date_str = date_match.group().replace("/", "-")  # Replace slashes with dashes
            time_str = time_match.group()

            # Combine the date and time strings
            date_time_str = f'{date_str} {time_str}'

            # Convert the combined string to a datetime object
            date = datetime.strptime(date_time_str, '%d-%m-%Y %H:%M')

            # Add the cleaned date to the Date_clean column
            df_final.at[index, 'Date_clean'] = date
        else:
            # If no date or time is found, print a message
            print(f"No date or time found in string {original_date_str} at index {index}")
    except ValueError:
        # In case the date or time string does not match the expected format
        print(f"Could not parse date and time string {original_date_str} at index {index}")
##############################################################

######### HARD CODE THE NORMAL RANGES  ##############
blood_test_ranges_flat = {
    "pH": None, "pCO2": None, "pO2": None, "HCO3 (Bicarbonate)-calc.": None,
    "Base Excess": None, "Hematocrit": (40.0, 52.0), "Hemoglobin": (13.5, 17.5), "Saturation, O2": (94.0, 98.0),
    "Oxyhemoglobin": None, "Carboxyhemoglobin": (1.0, 2.0), "Methemoglobin": (0.5, 1.3), "Deoxyhemoglobin": None,
    "Sodium": (136, 148), "Potassium": (3.5, 5.2), "Calcium, Ionized": (1.00, 1.20), "Chloride": (98, 110),
    "Anion Gap": (10.0, 22.0), "Glucose": (70, 100), "Lactate": (6, 18),
}

####### HARD CODE DESCRIPTIONS #####
descriptions = {
    "ph": "pH is like a thermometer for your body but for acidity and basicity. Lower values mean more acidity, higher values mean less. It’s dangerous if it goes too high or too low. Normal range: **7.35 - 7.45**.",
    "pco2": "pCO2 is like a marker of how well your lungs remove carbon dioxide. Higher values can indicate your body is having trouble getting rid of it. Normal range: **35 - 45 mmHg**.",
    "po2": "pO2 measures the pressure of oxygen in your blood. If it's too low, your body might not be getting enough oxygen. Normal range: **75 - 100 mmHg**.",
    "hco3 (bicarbonate)-calc.": "Bicarbonate helps keep your blood from becoming too acidic or too basic. If it’s too high or low, it can mean there’s an imbalance. Normal range: **22 - 28 mEq/L**.",
    "base excess": "Base excess measures whether your blood is too acidic (negative values) or too basic (positive values). It’s like the body’s way of saying it needs to balance its pH. Normal range: **-2 to +2 mEq/L**.",
    "hematocrit": "Hematocrit is like a ratio of your blood that's made up of red blood cells. Higher numbers could mean dehydration or other conditions, lower could mean anemia. Normal range: **Men: 38.8 - 50.0%, Women: 34.9 - 44.5%**.",
    "hemoglobin": "Hemoglobin is a special stuff in your red blood cells that carries oxygen. If it’s low, you might be tired and breathless. Normal range: **Men: 13.5 - 17.5 g/dL, Women: 12.0 - 15.5 g/dL**.",
    "saturation, o2": "O2 Saturation is how much of your hemoglobin is carrying oxygen. It’s like your blood’s fuel gauge for oxygen. Normal range: **94 - 100%**.",
    "oxyhemoglobin": "Oxyhemoglobin is the hemoglobin that's carrying oxygen. The more you have, the more oxygen your body is carrying. Normal range can vary.",
    "carboxyhemoglobin": "Carboxyhemoglobin is the hemoglobin that's carrying carbon monoxide. High levels can be dangerous. Normal range: **Less than 1.5%**.",
    "methemoglobin": "Methemoglobin is a form of hemoglobin that can't carry oxygen well. If this number is high, you might have methemoglobinemia. Normal range: **0 - 2%**.",
    "deoxyhemoglobin": "Deoxyhemoglobin is the hemoglobin that's not carrying oxygen. The lower this number, the more of your hemoglobin is carrying oxygen. Normal range can vary.",
    "sodium": "Sodium is a type of salt that your body uses to control blood pressure and help your nerves and muscles work correctly. Normal range: **135 - 145 mEq/L**.",
    "potassium": "Potassium is a mineral that helps your nerves and muscles work right. Too much or too little can cause problems. Normal range: **3.5 - 5.0 mEq/L**.",
    "calcium, ionized": "Calcium is a mineral your body needs to build strong bones and teeth, and it helps your muscles and nerves work too. Normal range: **4.5 - 5.6 mg/dL**.",
    "chloride": "Chloride is another type of salt in your blood along with sodium and potassium. It helps balance acidity and alkalinity in your body. Normal range: **96 - 106 mEq/L**.",
    "anion gap": "Anion Gap is a complex calculation that can help your doctor figure out what’s causing an acid-base imbalance in your body. Normal range: **3 - 11 mEq/L**.",
    "glucose": "Glucose is the fuel your body uses to produce energy. Too much could mean you have diabetes. Normal range (fasting): **70 - 100 mg/dL**.",
    "lactate": "Lactate is a product your body makes when it’s short on oxygen. Higher levels could mean a problem with oxygen delivery to your tissues. Normal range: **0.5 - 2.2 mmol/L**.",
    "DateTime": "This isn't a lab value, but rather when the values were taken. It's important because it can show changes over time."
}
#####################################

########## HARD  CODE COLS OF INTEREST #######
cols = ["ph", "pco2", "po2", "hco3 (bicarbonate)-calc.", "base excess", "hematocrit",
        "hemoglobin", "saturation, o2", "oxyhemoglobin", "carboxyhemoglobin",
        "methemoglobin", "deoxyhemoglobin", "sodium", "potassium", "calcium, ionized",
        "chloride", "anion gap", "glucose", "lactate", "Date_clean"]
###############################################


############## SHOW ON GUI DF #################
df_subset_temp = df_final[[col for col in cols if col in df_final.columns]]
if not df_subset_temp.empty:
    
    st.divider()
    st.subheader('Here is a summary of your pdf files in a dataframe')
    df_subset_temp['Date_clean'] = pd.to_datetime(df_subset_temp['Date_clean'], format="%yyyy-%mm-%dd %H:%M")
    df_subset_temp = df_subset_temp.sort_values(by="Date_clean")
    st.write(df_subset_temp)
else:
    # st.write("No data to display.Browse files and upload multiple pdf files")
    print("No data to display. Browse and upload pdf files")
#################################################

############### PLOPT THE GRAPHS #############
if 'Date_clean' in df_final.columns:
    df_final['Date_clean'] = pd.to_datetime(df_final['Date_clean'], format="%yyyy-%mm-%dd %H:%M")
blood_test_ranges_flat = {k.lower(): v for k, v in blood_test_ranges_flat.items()}



if 'df_final' in locals() and not df_final.empty:
        
    # Only consider the columns in the cols list
    for col in cols[:-1]:  # Exclude 'Date_clean'
        # If the column is in the DataFrame
        if col in df_final.columns:
            # Convert empty strings to NaN
            df_final[col] = df_final[col].apply(lambda x: np.nan if str(x).strip() == '' else x)
    
            # Drop the rows with missing or NaN values
            df_subset = df_final[[col, 'Date_clean']].dropna()
    
            # Sort df_subset by 'Date_clean'
            df_subset = df_subset.sort_values('Date_clean')
    
            # If the subset DataFrame is not empty
            if not df_subset.empty:
                # Fetch and print description
                description = descriptions.get(col, 'No description available.')
                # print(f"\n{col}:\n{description}\n")
                # st.write(f"\n{col}:\n{description}\n")
                st.markdown(f"**{col}**: {description}")
                
                # Create a new figure
                plt.figure(figsize=(10, 5))
                # Scatter plot column vs. Date_clean
                plt.scatter(df_subset['Date_clean'], df_subset[col])
                # Plot a thin light blue line connecting the points
                plt.plot(df_subset['Date_clean'], df_subset[col], color='lightblue', linewidth=1)
                # Set the title and labels
                plt.title(f'Trend of {col} over time')
                plt.xlabel('Date')
                plt.ylabel(col)
    
                # If there are reference ranges for this test
                if blood_test_ranges_flat.get(col):
                    lower_limit, upper_limit = blood_test_ranges_flat[col]
                    # Add horizontal lines for the reference ranges
                    plt.axhline(y=lower_limit, color='r', linestyle=':', linewidth=0.5)
                    plt.axhline(y=upper_limit, color='r', linestyle=':', linewidth=0.5)
    
                    # Extend the y-axis limits by 20% on either side of the larger of the range and the actual data
                    data_min, data_max = df_subset[col].min(), df_subset[col].max()
                    ylim_lower = min(data_min, lower_limit)*0.8
                    ylim_upper = max(data_max, upper_limit)*1.2
                    plt.ylim([ylim_lower, ylim_upper])
    
                    # Add texts above the reference lines
                    plt.text(df_subset['Date_clean'].min(), lower_limit + 0.01*(ylim_upper - ylim_lower),
                             "normal range (lower limit)", color='black', fontsize=8, va='bottom')
                    plt.text(df_subset['Date_clean'].min(), upper_limit + 0.01*(ylim_upper - ylim_lower),
                             "normal range (upper limit)", color='black', fontsize=8, va='bottom')
    
                # Show the plot
                st.pyplot(plt)

        # # Plot
        # if len(df_subset) > 0:  # check if dataframe after dropping NaN values is not empty
        #     st.markdown(f"**{col}**: {descriptions.get(col, '')}")
        #     fig = px.scatter(df_subset, x='DateTime', y=col)
        #     st.plotly_chart(fig)
        #     st.divider()

else:
    # st.write("No PDF loaded. Please load a PDF file.")
    print("No PDF loaded. Please load a PDF file.")
    
    


# ### RESET TO FALSE UNTIL NEW PDF UPLOADED
# st.session_state.new_pdf_uploaded = False
