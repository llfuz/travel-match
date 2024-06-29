import streamlit as st
import os
from ics import Calendar, Event
from datetime import datetime, timedelta
import json
from openai import OpenAI
import requests
from streamlit_lottie import st_lottie

def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_coding = load_lottiefile("ani.json")
lottie_coding1 = load_lottiefile("ani2.json")

# Create two columns
col1, col2, col3= st.columns([1, 2, 1])
with col1:
    activities = {
        "Art": st.checkbox("Art"),
        "Museums": st.checkbox("Museums"),
        "Outdoor Activities": st.checkbox("Outdoor Activities"),
        "Indoor Activities": st.checkbox("Indoor Activities"),
        "Good for Kids": st.checkbox("Good for Kids"),
        "Good for Young People": st.checkbox("Good for Young People"),
        "Elderly Friendly": st.checkbox("Elderly Friendly"),
        "Water parks": st.checkbox("Water parks"),
        "Amusement parks": st.checkbox("Amusement parks")
    }

# Place the Lottie animation in the first column
with col3:
    st_lottie(
        lottie_coding,
        speed=1,
        reverse=False,
        loop=True,
        quality="high", # medium ; high
        height=None,
        width=None,
        key=None,
    )
    st_lottie(
        lottie_coding1,
        speed=1,
        reverse=False,
        loop=True,
        quality="high", # medium ; high
        height=None,
        width=None,
        key=None,
    )

# Initialize OpenAI API
openai = OpenAI(api_key="")

# Streamlit app title
st.title("Welcome to Travel Match")

# Place the text inputs and other elements in the second column
with col2:
    # User inputs
    city = st.text_input("Enter the city you're visiting:")
    start_date = st.date_input("Select the start date for your trip:", value=datetime.today())
    end_date = st.date_input("Select the end date for your trip:",
                             value=start_date + timedelta(days=1),
                             min_value=start_date)

    # Calculate the number of days
    days = (end_date - start_date).days
    # Activity checkboxes

    # Generate Itinerary button
    if st.button("Generate Itinerary"):
        # Build the prompt for the chatbot
        prompt = f"You are a travel expert. Give me an itinerary for {city} for {days} days, starting at 10am and ending at 8pm each day, with a 30-minute buffer between each activity. I like to"
        for activity, selected in activities.items():
            if selected:
                prompt += f" {activity.lower()},"
        prompt = prompt.rstrip(",")  # Remove trailing comma
        prompt += ". Limit the length of output JSON string to 1200 characters. Generate a structured JSON representation for the travel itinerary."

        # Call OpenAI API to get the itinerary
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=3000
        )

        # Parse the response
        paraphrased_text = response.choices[0].message.content
        st.text(paraphrased_text)  # Debugging: print the raw response

        try:
            itinerary = json.loads(paraphrased_text)
            st.json(itinerary)  # Debugging: display the parsed JSON

            if "days" not in itinerary:
                raise KeyError("The key 'days' is missing from the itinerary JSON")

            # Display the itinerary
            for day in itinerary["days"]:
                st.header(f"Day {day['day']}")
                for activity in day["activities"]:
                    st.subheader(activity["title"])
                    st.write(f"Description: {activity['description']}")
                    st.write(f"Location: {activity['location']}")
                    st.write(f"Time: {activity['start_time']} - {activity['end_time']}")
                    st.write(f"Link: {activity['link']}")
                    st.write("\n")

            # Generate the iCalendar file
            cal = Calendar()
            for day, activities in enumerate(itinerary.get("days", []), start=1):
                for activity in activities.get("activities", []):
                    event = Event()
                    event.name = activity.get("title", "")
                    event.description = activity.get("description", "")
                    event.location = activity.get("location", "")
                    event.begin = start_date + timedelta(days=day - 1,
                                                         hours=int(activity.get("start_time", "10:00").split(":")[0]),
                                                         minutes=int(activity.get("start_time", "10:00").split(":")[1][:2]))
                    event.end = start_date + timedelta(days=day - 1,
                                                       hours=int(activity.get("end_time", "20:00").split(":")[0]),
                                                       minutes=int(activity.get("end_time", "20:00").split(":")[1][:2]))
                    cal.events.add(event)

            cal_content = str(cal)

            def get_download_link(content, filename):
                """Generates a download link for the given content."""
                b64_content = content.encode().decode("utf-8")
                href = f'<a href="data:text/calendar;charset=utf-8,{b64_content}" download="{filename}">Download {filename}</a>'
                return href

            st.success("Itinerary ready to export!")
            st.markdown(get_download_link(cal_content, "Itinerary.ics"), unsafe_allow_html=True)

        except json.JSONDecodeError:
            st.error("Failed to parse itinerary JSON. Please try again.")
        except KeyError as e:
            st.error(f"Missing key in the itinerary JSON: {e}")