# import libraries and packages
import pandas as pd
import re
import plotly.express as px
import zipfile
import os
import logging
logging.basicConfig(level=logging.DEBUG)
import streamlit as st
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu


# set streamlit config as wide
st.set_page_config(
        page_title="Saucy (Home)",
        page_icon= "🔥",
        layout="wide"
    ) 


# Sidebar for navigation
with st.sidebar:
    app_pages = option_menu("Menu", ["Saucy", "More Insights", "coming soon..."], icons=["house", "bar-chart-line"], menu_icon="justify")
    # st.sidebar.selectbox("Insights waiting to be discovered", ["SAUCY", "More Insights", "Loading..."])
st.sidebar.caption("Select a Page above")


# File uploader in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload Your Whatsapp Chat (zip files only!)", type="zip")
st.sidebar.caption("Please be rest assured that we don't collect or process your data in anyway")

if uploaded_file == None:
    st.title("Welcome to the Saucy chat Analyzer")
    st.image("saucy.jpeg")

    st.warning("Please upload a chat file to proceed with the analysis")
    st.caption("Use the upload button in the sidebar")

if uploaded_file:

    m_start =  0
    m_end = 12
    a_start = 12
    a_end =  17
    e_start = 17
    e_end = 20

    # Define time ranges
    def categorize_time(time):
        if time >= m_start and time < m_end:
            return 'Morning'
        elif time >= a_start and time < a_end:
            return 'Afternoon'
        elif time >= e_start and time < e_end :
            return 'Evening'
        else:
            return 'Night'
                
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            # Get a list of all files in the zip archive
            file_list = zip_ref.namelist()  
            # Find a .txt file
            txt_files = [f for f in file_list if f.endswith('.txt')]
            if txt_files:
                target_file = txt_files[0]  # Extract the first .txt file found
                zip_ref.extract(target_file) 
                logging.debug("Unzipped Successfully")
                text_file_path = target_file
                logging.debug("Done with txt file")
            else:
                st.error("No .txt files found in the zip archive.")

        # Open the txt file and read content to a variable
            with open(text_file_path, 'r', encoding='utf-8') as file:
                chat_data = file.readlines()
            # delete the file
            os.remove(text_file_path)
            logging.debug("Text successfully extracted")

            # create dictionary to store contents before paring to a dataframe
            chat_dict = {
                "datetime": [],
                "sender": [],
                "message" : []
                }
                
            #  set regex pattern to use for extraction
            datetime_pattern = r"(\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{1,2})"
            sender_pattern = r"- (.*?):"
            message_pattern = r": (.+)"
            logging.info("Regex just ready to go")
            
            for line in chat_data:
                date_match = re.search(datetime_pattern, line)
                sender_match = re.search(sender_pattern, line)
                message_match = re.search(message_pattern, line)
                
                if date_match:
                    chat_dict["datetime"].append(date_match.group(1))
                else:
                    chat_dict["datetime"].append(None)
                    
                if sender_match:
                    chat_dict["sender"].append(sender_match.group(1))
                else:
                    chat_dict["sender"].append(None)
                    
                if message_match:
                    chat_dict["message"].append(message_match.group(1))
                else:
                    chat_dict["message"].append(line.strip())
        
            logging.debug("Dictionary created, ready for the DataFrame now")
        
            # Create the DataFrame
            df = pd.DataFrame(chat_dict)
            logging.debug("DataFrame created, about to clean the dates now")
        
            df["datetime"] = df["datetime"].ffill()
            logging.info("Datetime filled down successfully")
        
            df["sender"] = df["sender"].ffill()
            logging.info("Sender filled down successfully")
        
            # Convert 'datetime' column to datetime datatype
            df['datetime'] = pd.to_datetime(df['datetime'], format='%m/%d/%y, %H:%M')
            logging.debug("Datetime conversion successful")
        
        
            # Extract date name
            df["datename"] = df['datetime'].dt.strftime("%A, %d %B %Y")
        
            # Extract only time
            df['time'] = df['datetime'].dt.time  # Extract time
        
            # Extract clock hour
            df['hour'] = df['datetime'].dt.hour
        
            # Add category column
            df['time_category'] = df['hour'].apply(categorize_time)
        
            # Extract year column
            df["year"] = df['datetime'].dt.isocalendar().year
            df["month"] = df['datetime'].dt.month_name()


    if app_pages == "Saucy":
        st.header("Let's get to insighting!!!🤓🤓")
        index_to_drop = df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == ''").index
        df.drop(index=index_to_drop, inplace=True)
        ice_breaker = df['sender'].iloc[0]
        st.session_state.ice_breaker = ice_breaker

        years = list(set(df["year"]))
        years.sort()
        months = list(set(df['month']))
        months.insert(0, "Choose...")

        month_answer = df["month"].iloc[0]
        guess_month = st.selectbox(f"Can you guess the month in {years[0]} the chat started?", options=months)
        
        if guess_month and guess_month == month_answer:
            st.success(f"YES!\n This entire chat started on {df["datename"].iloc[0]}")
            st.markdown("Below is a sneak peek into the start of this saucy insight.🔥🔥")
            st.dataframe(df[["sender", "message", "datename"]].head())
            st.info(f"{df["sender"].iloc[0]} broke the ice on this chat")
        else:
            st.warning("Pick the correct answer to see the results! 😁")

        times = list(set(df['hour']))
        times.insert(0, "Choose...")

        hour_message_count = df['hour'].value_counts().reset_index()
        hour_message_count["time_category"] = hour_message_count['hour'].apply(categorize_time)

        guess_time_answer = hour_message_count.nlargest(1, "count").iloc[0, 0]

        guess_time = st.selectbox("Can you guess this chat's most active times/hours?", options= times)

        if guess_time and guess_time == guess_time_answer:
            st.success("Correct!")
        st.divider()

        col1, col2 = st.columns([1,1])
        with col1:
            st.info("Here are bars representing hours of everyday and the total number of messages exchanged for each respective hours.")
            st.header("👉")
            # top_3 = df['datetime'].dt.hour.value_counts().head(3).index
            top_3 = hour_message_count.nlargest(3, "count").iloc[:3, 0]
            st.info("And your chat's most active hours are the:")
            st.markdown(f"1) {top_3[0]}hr")
            st.markdown(f"2) {top_3[1]}hr")
            st.markdown(f"3) and the {top_3[2]}hr")
            category_count = df["time_category"].value_counts().reset_index().sort_values("count", ascending=False)
            st.success(f"You mostly chat in the {category_count['time_category'].iloc[0]} ⚡")
        with  col2:
            fig = px.bar(hour_message_count, x='hour', y='count', title="Total Messages per Hour", labels={"count":"Total Messages", "hour":"Clock Hour", 'time_category':"Period of Day"}, template="plotly_dark", color='time_category')
            st.plotly_chart(fig)
            st.caption("Feel free to zoom-in, pan and download the chart above")


        
        st.divider()
        st.markdown("""
                    <style> .centered-subheader {text-align: center; color:gwhite; font-size:25px; background-color:pink} </style>
                    """, unsafe_allow_html=True)
        st.markdown('<p class="centered-subheader">Below are the top 20 most used words of each user</p>', unsafe_allow_html=True)
        people = sorted(list(set(df["sender"].dropna())))
        if len(people) == 2:
            person_1 = people[0]
            person_2 = people[1]
            st.sidebar.radio("Pick your identity",[person_1, person_2])

            # Remove non-alphanumeric characters from messages
        df['cleaned_message'] = df['message'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x))

        # Lowercase the messages for uniformity
        df['cleaned_message'] = df['cleaned_message'].str.lower().str.split()

        stop_words = ['very',
                    'our',
                    "hasn't",
                    'some',
                    'her',
                    's',
                    'he',
                    'while',
                    'if',
                    'from',
                    'had',
                    'who',
                    'being',
                    'any',
                    "needn't",
                    'with',
                    'than',
                    've',
                    'down',
                    'a',
                    'has',
                    'before',
                    "isn't",
                    'further',
                    'll',
                    'each',
                    'between',
                    "wouldn't",
                    'below',
                    'it',
                    'these',
                    'this',
                    'mightn',
                    'ours',
                    'they',
                    "don't",
                    'under',
                    'but',
                    'how',
                    'nor',
                    "wasn't",
                    'there',
                    'can',
                    'once',
                    "shouldn't",
                    'couldn',
                    "weren't",
                    'did',
                    'hadn',
                    'hers',
                    "hadn't",
                    'where',
                    'its',
                    'only',
                    'same',
                    "didn't",
                    'to',
                    'other',
                    'wasn',
                    'up',
                    'be',
                    'why',
                    'out',
                    "you'll",
                    'so',
                    'what',
                    'few',
                    't',
                    'that',
                    'will',
                    'and',
                    'in',
                    'she',
                    'haven',
                    'ourselves',
                    'aren',
                    'after',
                    'into',
                    'ma',
                    "haven't",
                    'an',
                    'through',
                    'or',
                    'weren',
                    'don',
                    'theirs',
                    'off',
                    'does',
                    'was',
                    'when',
                    'needn',
                    'shouldn',
                    "won't",
                    'just',
                    "you've",
                    "you're",
                    'having',
                    'should',
                    'himself',
                    'again',
                    "should've",
                    'both',
                    'such',
                    'is',
                    'during',
                    "couldn't",
                    'am',
                    "she's",
                    'ain',
                    "shan't",
                    'by',
                    'your',
                    "doesn't",
                    'more',
                    'about',
                    'been',
                    'i',
                    'my',
                    'y',
                    'the',
                    'over',
                    'were',
                    'doing',
                    'too',
                    'because',
                    'own',
                    'whom',
                    'on',
                    'yourselves',
                    'above',
                    'wouldn',
                    'hasn',
                    're',
                    'you',
                    "you'd",
                    'those',
                    'herself',
                    "that'll",
                    'him',
                    'of',
                    'most',
                    'their',
                    'then',
                    'no',
                    'isn',
                    'until',
                    'd',
                    'we',
                    "mustn't",
                    'for',
                    'them',
                    'myself',
                    'now',
                    'here',
                    'didn',
                    'm',
                    'which',
                    'do',
                    'yours',
                    'as',
                    "aren't",
                    'his',
                    'won',
                    'are',
                    'against',
                    'me',
                    'mustn',
                    'all',
                    'doesn',
                    'not',
                    'have',
                    'o',
                    "mightn't",
                    'shan',
                    'itself',
                    'yourself',
                    "it's",
                    'themselves',
                    'at', 
                    "im",
                    "media",
                    "omitted"]

    

        # Initialize a dictionary to hold word counts for each sender
        word_count = {}
        i = 0
        
        columns = st.columns(2)

        # Loop through each sender to calculate word counts and generate word clouds
        for sender in people:
            new_df = df.query("sender == @sender")

            # Flatten the list of all words in the column, excluding stop words
            all_words = [word for tokens in new_df['cleaned_message'] for word in tokens if word not in stop_words]

            # Use Counter to count all words
            word_counts = Counter(all_words)
            
            # Convert Counter to DataFrame and sort by count
            word_count[sender] = pd.DataFrame(word_counts.items(), columns=['words', 'count']).sort_values(by='count', ascending=False)

            # Get the top 10 words
            top_words = word_count[sender].nlargest(20, 'count')

            # Generate the word cloud from the top words
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(dict(zip(top_words['words'], top_words['count'])))

            # Plot the word cloud
            fig, ax = plt.subplots(figsize=(4,2))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')  # Turn off the axis
            ax.set_title(f"{sender}'s most used words", fontsize=10)
            
            
            with columns[i]:
                i += 1
                # Display the plot in Streamlit
                st.pyplot(fig)
                st.caption("You can see the number of times each words above appear for each participant of this chat")
                top_words.columns = ['Word', 'Number of appearance']
                st.dataframe(top_words)

        st.info("Navigate to the More Insights Page to get extra fresh and updated insights 😁😁📊")


    elif app_pages == "More Insights":
        st.header("Here's more Sauce!! 🥳") 
        # st.sidebar.caption("Please be rest assured that we don't collect or process your data in any way")
        people = list(set(df["sender"].dropna()))
        ice_breaker = st.session_state.ice_breaker

        if df is not None:

            if len(people) < 2:
                st.warning("This chat doesn't have enough participants for analysis. Please upload a chat with at least two participants.")
            else:
                sender_1, sender_2 = people[:2]

                guess_media_sender = st.selectbox(f"Can you guess who sent the most media? 🤔🤔", ["Choose...", sender_1, sender_2])
                st.write("and")
                guess_ice_breaker = st.selectbox(f"Who broke the ice?", ["Choose...", sender_1, sender_2])
                @st.cache_data
                def media_sender(data, s1, s2):
                    sender_1_df = data[data["sender"] == s1]
                    sender_2_df = data[data["sender"] == s2]
                    s1_total_media = sender_1_df['message'].str.count("<Media omitted>").sum()
                    s2_total_media = sender_2_df['message'].str.count("<Media omitted>").sum()

                    result_df = pd.DataFrame({
                        "Names": [s1, s2],
                        "Total Media": [s1_total_media, s2_total_media]
                    })
                    
                    if s1_total_media > s2_total_media:
                        winner = s1
                    elif s1_total_media < s2_total_media:
                        winner = s2
                    else:
                        winner = "It's a tie!"
                    
                    return result_df, winner
                
                result_df, winner = media_sender(df, sender_1, sender_2)

                if guess_media_sender != "Choose...":
                    if guess_media_sender == winner:
                        st.success("Yay!!! You guessed correctly 🎉🎉")
                    else:
                        st.warning("Oops! Not quite right! 🤭")
                    
                    if winner != "It's a tie!":
                        st.success(f"{winner} sent more media files in this chat")
                    else:
                        st.info("It's a tie! You both sent the same number of media 🤭🤭🤭")

                    st.info(f"Lol, {ice_breaker} broke the ice on this entire chat")
                    
                    st.markdown("---")

                    fig = px.bar(result_df, x='Total Media', y='Names', orientation='h', color="Names", 
                                    title=f'Total Number of Media sent ({df["message"].str.count("<Media omitted>").sum()})')
                    st.plotly_chart(fig)

                else:
                    st.info("Pick the correct answer to see the results! 😁")
        else:
            st.warning("No chat data available. Please upload a chat file on the 'Saucy' page first.")










        
        
    

            
    
    
