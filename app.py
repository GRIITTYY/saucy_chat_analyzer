# import libraries and packages
import pandas as pd
import re
import plotly.express as px
import zipfile
import os
import logging
import nltk
logging.basicConfig(level=logging.DEBUG)
import streamlit as st
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = set(stopwords.words("english"))

# set streamlit config as wide
st.set_page_config(
        page_title="Saucy (Home)",
        page_icon= "🔥",
        layout="wide"
    ) 


# Sidebar for navigation
with st.sidebar:
    app_pages = option_menu(
                            "Menu", 
                            ["Saucy", "More Insights", "coming soon..."], 
                            icons=["house", "bar-chart-line"], 
                            menu_icon="justify"
                            ,
                            styles={
            "container": {"background-color": "#fafafa"},
            "nav-link": {"font-size": "17px", "text-align": "justify", "margin": "0px", "--hover-color": "#eee"}})
st.sidebar.success("Select a Page above")


# File uploader in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload Your Whatsapp Chat (zip files only!)", type="zip")
st.sidebar.caption("Please be rest assured that we don't collect or process your data in anyway")

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
            

def get_week_of_month(day):
    week_num = day / 7
    if week_num <= 1:
        return "Week 1"
    elif week_num <= 2:
        return "Week 2"
    elif week_num <= 3:
        return "Week 3"
    else:
        return "Week 4"
    


if uploaded_file == None:
    st.title("Welcome to the Saucy chat Analyzer")
    st.image("saucy.jpeg")

    st.warning("Please upload a chat file to proceed with the analysis")
    st.caption("Use the upload button in the sidebar")

if uploaded_file:

    st.sidebar.image("saucy.jpeg")
        
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
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(' ')
                with col2:
                    st.image("error.jpeg")
                with col3:
                    st.write(' ')
                st.error("No valid whatsapp chat data found in your uploaded zip file.")
                st.warning("Please upload a valid whatsapp chat file to proceed with the analysis")
                st.stop()

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
            df['timecategory'] = df['hour'].apply(categorize_time)
        
            # Extract year column
            df["year"] = df['datetime'].dt.isocalendar().year
            df["month"] = df['datetime'].dt.month_name()
            df['day'] = df['datetime'].dt.day
            # df['week'] = df['day'].apply(get_week_of_month).astype(str)
            df['week'] = df['day'].apply(get_week_of_month)



    index_to_drop = df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == '' or message == ' '").index
    df.drop(index=index_to_drop, inplace=True)
    ice_breaker = df['sender'].iloc[0]

    if app_pages == "Saucy":
        st.header("Let's get to insighting!!!🤓🤓")

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
            st.info(f"{ice_breaker} broke the ice on this chat")
        else:
            st.warning("Pick the correct answer to see the results! 😁")

        times = list(set(df['hour']))
        times.insert(0, "Choose...")

        hour_message_count = df['hour'].value_counts().reset_index()
        hour_message_count["timecategory"] = hour_message_count['hour'].apply(categorize_time)

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
            category_count = df["timecategory"].value_counts().reset_index().sort_values("count", ascending=False)
            st.success(f"You mostly chat in the {category_count['timecategory'].iloc[0]} ⚡")
        with  col2:
            fig = px.bar(hour_message_count, x='hour', y='count', title="Total Messages per Hour", labels={"count":"Total Messages", "hour":"Clock Hour", 'timecategory':"Period of Day"}, template="plotly_dark", color='timecategory')
            fig.update_layout(yaxis={"showgrid":False})
            st.plotly_chart(fig)
            st.caption("Feel free to zoom-in, pan and download the chart above")


        
        st.divider()
        st.markdown("""
                    <style> .centered-subheader {text-align: center; color:gwhite; font-size:25px; background-color:pink} </style>
                    """, unsafe_allow_html=True)
        st.markdown('<p class="centered-subheader">Below are the top 20 most used words of each user</p>', unsafe_allow_html=True)
        people = sorted(list(set(df["sender"].dropna())))
        if len(people) == 2:
            # person_1 = people[0]
            # person_2 = people[1]
            st.sidebar.radio("Pick your identity", [i for i in people])
        else:
            st.sidebar.write("Messages were not exchanged back and forth between two people in this chat.")

            # Remove non-alphanumeric characters from messages
        df['cleaned_message'] = df['message'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x))

        # Lowercase the messages for uniformity
        df['cleaned_message'] = df['cleaned_message'].str.lower().str.split()

        # Initialize a dictionary to hold word counts for each sender
        word_count = {}
        increment = 0
        
        columns = st.columns(2)

        # Loop through each sender to calculate word counts and generate word clouds
        for sender in people:
            new_df = df.query("sender == @sender")
            index_to_drop = new_df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == '' or message == ' ' or message == '<Media omitted>'").index
            new_df.drop(index=index_to_drop, inplace=True)

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
            
            
            with columns[increment]:
                increment += 1
                # Display the plot in Streamlit
                st.pyplot(fig)
                st.caption("You can see the number of times each words above appear for each participant of this chat")
                # top_words.columns = ['Word', 'Number of appearance']
                st.dataframe(top_words)

        st.info("Navigate to the More Insights Page to get extra fresh and updated insights 😁😁📊")


    elif app_pages == "More Insights":
        st.header("Here's more Sauce!! 🥳") 
        # st.sidebar.caption("Please be rest assured that we don't collect or process your data in any way")
        people = list(set(df["sender"].dropna()))

        if df is not None:
            if len(people) < 2:
                st.warning("Messages were not exchanged back and forth between two people in this chat.")
            else:
                guess_ice_breaker = st.selectbox(f"Who broke the ice?", ["Choose..."] + [i for i in people])
                if guess_ice_breaker == ice_breaker:
                    st.success("Sharp! 👍🏾✅")
                else:
                    st.warning("Oops! Almost there")
                st.write("and")
                guess_media_sender = st.selectbox(f"Can you guess who sent the most media? 🤔🤔", ["Choose..."] + [i for i in people])
                
                result_df = pd.DataFrame({
                        "Names": [],
                        "Total Media": []
                    })
                
                @st.cache_data
                def media_sender(data, people_list):
                    for i in range(len(people_list)):
                        sender_df = data[data["sender"] == people[i]]
                        total_media = sender_df['message'].str.count("<Media omitted>").sum()
                        result_df.loc[i, 'Names'] = people[i]
                        result_df.loc[i, "Total Media"] = total_media

                    
                    media_count = []
                    for i in range(len(result_df["Total Media"])):
                        media_count.append(result_df["Total Media"].iloc[i])

                    if len(media_count) == 2:
                        for i in range(len(media_count)):
                            if media_count[0] > media_count[1]:
                                winner = result_df['Names'].iloc[0]
                            elif media_count[1] > media_count[0]:
                                winner = result_df['Names'].iloc[1]
                            else:
                                winner = "It's a tie!"
                    
                    return result_df, winner
                
                result_df, winner = media_sender(df, people)

                if guess_media_sender != "Choose...":
                    if guess_media_sender == winner:
                        st.success("Yay!!! You guessed correctly 🎉🎉")
                    else:
                        st.warning("Oops! Not quite right! 🤭")
                    
                    if winner != "It's a tie!":
                        pass
                    else:
                        st.info("It's a tie! You both sent the same number of media 🤭🤭🤭")
                        index_to_drop = df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == ''").index
                        df.drop(index=index_to_drop, inplace=True)
                        ice_breaker = df['sender'].iloc[0]
                        st.info(f"Lol, {df['sender']} broke the ice on this entire chat")

                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.pie(result_df, values='Total Media', names='Names', color_discrete_sequence=px.colors.qualitative.Set1,
                                        title=f'Total Number of Media exchanged ({df["message"].str.count("<Media omitted>").sum()})')
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig)
                        st.success(f"{winner} sent more media files in this chat")
                    
                    with col2:
                        result_df = pd.DataFrame({
                        "Names": [],
                        "Total Messages": []
                    })
                        
                        for i in range(len(people)):
                            x = people[i]
                            i_df = df.query("sender == @x")
                            index_to_drop = i_df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == '' or message == ' ' or message == '<Media omitted>'").index
                            i_df.drop(index=index_to_drop, inplace=True)
                            result_df.loc[i, "Names"] = people[i]
                            result_df.loc[i, "Total Messages"] = len(i_df['message'])

                        fig = px.pie(result_df, values="Total Messages", names='Names',
                                     color_discrete_sequence = px.colors.qualitative.Bold,
                                        title=f'Total Number of Messages exchanged ({len(df["message"])})')
                        fig.update_traces(textposition='inside', textinfo='percent+label+value')
                        st.plotly_chart(fig)

                        i = list(result_df["Total Messages"].nlargest(1).index)[0]
                        st.info(f"{result_df['Names'][i]} sent more messages in this chat")

                    st.markdown("""
                    <style> .centered-summary {text-align: center; color:gwhite; font-size:25px; background-color:pink} </style>
                    """, unsafe_allow_html=True)
                    st.markdown('<p class="centered-summary">Now below is summary of some  key informations</p>', unsafe_allow_html=True)
                    
                    people_filter = st.selectbox("Pick one:", ["All"] + [i for i in people])

                    col1, col2, col3, col4, col5= st.columns(5)

                    if people_filter == "All":
                        with col1:
                            total_links = df['message'].str.contains("https").sum()
                            col1.metric(label="Total Links sents", value= total_links)
                        with col2:
                            most_active_hour = df['hour'].value_counts().nlargest(1).index[0]
                            st.metric(label="Most active Hour", value=f"{most_active_hour} Hour")
                        with col3:
                            # for sender in people:
                            new_df = df.copy()
                            index_to_drop = new_df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == '' or message == ' ' or message == '<Media omitted>'").index
                            new_df.drop(index=index_to_drop, inplace=True)
                            new_df['cleaned_message'] = new_df['message'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x))
                            # Lowercase the messages for uniformity
                            new_df['cleaned_message'] = new_df['cleaned_message'].str.lower().str.split()
                            # Flatten the list of all words in the column, excluding stop words
                            all_words = [word for tokens in new_df['cleaned_message'] for word in tokens if word not in stop_words]
                            # Use Counter to count all words
                            most_common_word = Counter(all_words).most_common(1)[0][0]
                            st.metric(label="Most Common word", value=most_common_word)
                        with col4:
                            del_count = df['message'][(df["message"] == 'You deleted this message') | (df['message'] == 'This message was deleted')].count()
                            st.metric(label="Total number of deleted messages", value= del_count)
                        with col5:
                            edit_count = df.query("message.str.contains('<This message was edited>')")["message"].count()
                            st.metric(label="Total number of edited messages", value= edit_count)


                             
                    elif people_filter != "All":
                        new_df = df.copy()
                        y = new_df.copy()
                        x = people_filter
                        with col1:
                            sender_df = df.query("sender == @x")
                            total_links = sender_df['message'].str.contains("https").sum()
                            col1.metric(label="Total Links sents", value= total_links)
                        with col2:
                            sender_df = df.query("sender == @x")
                            most_active_hour = sender_df['hour'].value_counts().nlargest(1).index[0]
                            st.metric(label="Most active Hour", value=f"{most_active_hour} Hour")
                        with col3:
                            new_df = new_df.query("sender == @x")
                            index_to_drop = new_df.query("message.str.contains('Tap to learn more.') or message == 'null' or message == '' or message == ' ' or message == '<Media omitted>'").index
                            new_df.drop(index=index_to_drop, inplace=True)
                            new_df['cleaned_message'] = new_df['message'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x))
                            # Lowercase the messages for uniformity
                            new_df['cleaned_message'] = new_df['cleaned_message'].str.lower().str.split()
                            # Flatten the list of all words in the column, excluding stop words
                            all_words = [word for tokens in new_df['cleaned_message'] for word in tokens if word not in stop_words]
                            # Use Counter to count all words
                            most_common_word = Counter(all_words).most_common(1)[0][0]
                            st.metric(label="Most Common word", value=most_common_word)
                        with col4:
                            new_df = y.query('sender == @x')
                            del_count = new_df['message'][(df["message"] == 'You deleted this message') | (df['message'] == 'This message was deleted')].count()
                            st.metric(label="Total number of deleted messages", value= del_count)
                        with col5:
                            new_df = y.query('sender == @x')
                            edit_count = new_df.query("message.str.contains('<This message was edited>')")["message"].count()
                            st.metric(label="Total number of edited messages", value= edit_count)

                            
                    st.divider()

                    st.success("Sweet Analytics below 😁😁😁")
                    # FOR THE PACKED VISUALS
                    col1, col2 = st.columns(2)
                    with col1:
                        year_filter = st.selectbox(label='Select year', options=['All time'] + list(set(df['year'])))
                    with col2:
                        month_filter = st.selectbox(label="Select month", options = ["All"] + list(set(df['month'])))
                    
                    # with col3:
                    #     day_filter = st.selectbox(label="select day", options=["All"] + list(set(df['day'])))
                    
                    # with col4:
                    #     period_filter = st.selectbox(label="Select period", options = ["All"] + list(set(df['timecategory'])))
                    
                    month_order = ["January", "February", "March", "April", "May", "June", 
                                        "July", "August", "September", "October", "November", "December"]


                    if year_filter == 'All time':
                        if month_filter == "All":
                            freq_df = df.copy()
                            freq_df = freq_df.query('month == @month_filter')
                            freq_df = df['month'].value_counts().reset_index()
                            fig = px.bar(freq_df, x='month', y='count', category_orders={'month':month_order}, 
                                        title="Total Number Of Messages Per Month", 
                                        labels={'month':"Month", 'count':"Total Messages"}, text_auto=True)
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)

                            freq_df = df.groupby(['month','week'])['message'].count().reset_index().rename(columns={"message":"count"})
                            fig = px.bar(freq_df, x='month', y='count', title="Total Number Of Messages Per Month & Per Week", 
                                            color='week', labels={'month':"Month", 'count':"Total Messages"},
                                            color_discrete_sequence=px.colors.qualitative.Set1,
                                            text_auto=True,
                                            category_orders={'month':month_order})
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)

                            freq_df = df.groupby(['month','timecategory'])['message'].count().reset_index().rename(columns={"message":"count"})
                            fig = px.bar(freq_df, x='month', y='count', title="Total Number Of Messages Per Month & Per Period Of Day", 
                                            color='timecategory', labels={'month':"Month", 'count':"Total Messages"},
                                            color_discrete_sequence = px.colors.qualitative.Bold,
                                            text_auto=True,
                                            category_orders={'month':month_order})
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)
                        elif month_filter in list(set(df['month'])):
                            freq_df = df.copy()
                            freq_df = freq_df.query('month == @month_filter')
                            freq_df = freq_df['month'].value_counts().reset_index()
                            st.metric(label=f"Total Number Of Messages in all of {month_filter} (ALL TIME)",
                                      value=freq_df['count'])
                            # fig = px.bar(freq_df, x='month', y='count', category_orders={'month':month_order}, 
                            #             title=f"Total Number Of Messages in all of {month_filter} (ALL TIME)", 
                            #             labels={'month':"Month", 'count':"Total Messages"}, text_auto=True)
                            # fig.update_layout(yaxis={"showgrid":False})
                            # st.plotly_chart(fig)


                            col1, col2 = st.columns(2)
                            with col1:
                                freq_df = df.copy()
                                freq_df = freq_df.query('month == @month_filter')
                                freq_df = freq_df.groupby(['month','week'])['message'].count().reset_index().rename(columns={"message":"count"})
                                fig = px.pie(freq_df, names='week', values='count', title=f"Total Number Of Messages Per Week in all of {month_filter} (ALL TIME)", 
                                                color='week', labels={'month':"Month", 'count':"Total Messages"},
                                                color_discrete_sequence=px.colors.qualitative.Set1,
                                                category_orders={'month':month_order})
                                fig.update_traces(textposition='outside', textinfo='percent+label+value')
                                fig.update_layout(yaxis={"showgrid":False})
                                st.plotly_chart(fig)

                            with col2:
                                freq_df = df.copy()
                                freq_df = freq_df.query('month == @month_filter')
                                freq_df = freq_df.groupby(['month','timecategory'])['message'].count().reset_index().rename(columns={"message":"count"})
                                fig = px.bar(freq_df, x='timecategory', y='count', title=f"Total Number Of Messages Per Period Of Day in all of {month_filter} (ALL TIME)", 
                                                color='timecategory', labels={'month':"Month", 'count':"Total Messages"},
                                                color_discrete_sequence = px.colors.qualitative.Bold,
                                                text_auto=True,
                                                category_orders={'month':month_order})
                                fig.update_layout(yaxis={"showgrid":False})
                                st.plotly_chart(fig)

                    
                    
                    else:
                        freq_df = df.query('year == @year_filter')
                        x = freq_df.copy()
                        if month_filter == "All":
                            freq_df = freq_df['month'].value_counts().reset_index()
                            fig = px.bar(freq_df, x='month', y='count', category_orders={'month':month_order}, 
                                        title=f"Total Number Of Messages Per Month in {year_filter}", 
                                        labels={'month':"Month", 'count':"Total Messages"}, text_auto=True)
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)

                        
                            freq_df = x.groupby(['month','week'])['message'].count().reset_index().rename(columns={"message":"count"})
                            fig = px.bar(freq_df, x='month', y='count', title=f"Total Number Of Messages Per Month & Per Week in {year_filter}", 
                                            color='week', labels={'month':"Month", 'count':"Total Messages"},
                                            color_discrete_sequence=px.colors.qualitative.Set1,
                                            text_auto=True,
                                            category_orders={'month':month_order})
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)

                            freq_df = x.groupby(['month','timecategory'])['message'].count().reset_index().rename(columns={"message":"count"})
                            fig = px.bar(freq_df, x='month', y='count', title=f"Total Number Of Messages Per Month & Per Period Of Day in {year_filter}", 
                                            color='timecategory', labels={'month':"Month", 'count':"Total Messages"},
                                            color_discrete_sequence = px.colors.qualitative.Bold,
                                            text_auto=True,
                                            category_orders={'month':month_order})
                            fig.update_layout(yaxis={"showgrid":False})
                            st.plotly_chart(fig)
                        elif month_filter in list(set(x['month'])):
                            freq_df = x.query('month == @month_filter')
                            freq_df = freq_df['month'].value_counts().reset_index()
                            st.metric(label=f"Total Number Of Messages in {month_filter} {year_filter}",
                                      value=freq_df['count'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                freq_df = x.query('month == @month_filter')
                                freq_df = freq_df.groupby(['month','week'])['message'].count().reset_index().rename(columns={"message":"count"})
                                fig = px.pie(freq_df, names='week', values='count', title=f"Total Number Of Messages Per Week in {month_filter} {year_filter}", 
                                                color='week', labels={'month':"Month", 'count':"Total Messages"},
                                                color_discrete_sequence=px.colors.qualitative.Set1,
                                                category_orders={'month':month_order})
                                fig.update_traces(textposition='outside', textinfo='percent+label+value')
                                fig.update_layout(yaxis={"showgrid":False})
                                st.plotly_chart(fig)

                            with col2:
                                freq_df = x.query('month == @month_filter')
                                freq_df = freq_df.groupby(['month','timecategory'])['message'].count().reset_index().rename(columns={"message":"count"})
                                fig = px.bar(freq_df, x='timecategory', y='count', title=f"Total Number Of Messages Per Period Of Day in {month_filter} {year_filter}", 
                                                color='timecategory', labels={'month':"Month", 'count':"Total Messages"},
                                                color_discrete_sequence = px.colors.qualitative.Bold,
                                                text_auto=True,
                                                category_orders={'month':month_order})
                                fig.update_layout(yaxis={"showgrid":False})
                                st.plotly_chart(fig)
























                        #     freq_df = freq_df['month'].value_counts().reset_index()
                        #     fig = px.bar(freq_df, x='month', y='count', category_orders={'month':month_order}, title="Total Number Of Messages Per Month", labels={'month':"Month", 'count':"Total Messages"}, text_auto=True)
                        #     fig.update_layout(yaxis={"showgrid":False})
                        #     st.plotly_chart(fig)
                        # else:
                        #     freq_df = freq_df.query('month == @filter3')
                        #     freq_df = freq_df.groupby(['week', 'timecategory'])['message'].count().reset_index().rename(columns={"message":"count"})
                        #     fig = px.bar(freq_df, x='week', y='count', barmode='group', title="Total Number Of Messages Per Week", 
                        #                   color='timecategory', labels={'week':"Week Number", 'count':"Total Messages"},
                        #                   color_discrete_sequence = px.colors.qualitative.Bold)
                        #     fig.update_layout(yaxis={"showgrid":False})
                        #     st.plotly_chart(fig)

                        







        
                else:
                    st.info("Pick the correct answer to see the results! 😁")
        else:
            st.warning("No chat data available. Please upload a chat file on the 'Saucy' page first.")










        
        
    

            
    
    
