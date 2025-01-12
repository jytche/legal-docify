import streamlit as st
import requests
import json

st.set_page_config(page_title="Legal Docify", layout="wide")

st.title("Legal Docify")
st.subheader("Create a summary for your legal matter in under a minute!")

col1, col2, col3, col4 = st.columns([2,0.2,3,0.2])

try:
    with open("placeholder.json", "r") as file:
        placeholder_data = json.load(file)
except FileNotFoundError:
    placeholder_data = {"error": "Could not find placeholder.json file."}

placeholder_text = json.dumps(placeholder_data, indent=4)

with col1:
    json_input = st.text_area(
        "Paste your JSON payload here (expected format provided):",
        height=200,
        placeholder=placeholder_text
    )

    uploaded_file = st.file_uploader("Or upload a JSON file:", type="json")

    if uploaded_file:
        json_input = uploaded_file.read().decode("utf-8")

    if st.button("Process Documents"):
        if json_input:
            try:
                payload = json.loads(json_input)

                st.info("Processing your data...")
                response = requests.post("http://127.0.0.1:8000/process-docs", json=payload)

                if response.status_code == 200:
                    result = response.json()
                    st.success("Processing complete!")

                    st.session_state.result = result

                else:
                    st.error(f"Error: {response.status_code}")
                    st.write(response.text)
            except json.JSONDecodeError:
                st.error("Invalid JSON format.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please provide a JSON payload.")

with col3:
    if "result" in st.session_state:
        result = st.session_state.result

        st.subheader("Summary")
        with st.expander("View Full Summary", expanded=True):
            st.write(result.get("summary", "No summary available"))

        st.subheader("Metadata")
        with st.expander("View Full Metadata", expanded=True):
            st.write(result.get("metadata", "No metadata available"))
    else:
        st.info("Results will appear here after processing.")

# Footer
st.markdown("---")
st.markdown("Powered by justice.")
