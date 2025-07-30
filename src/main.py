import streamlit as st
from exception import CustomException
from logger import logging
from gmail_reader import get_service, extract_email_details, get_unread_emails
from cleaning import clean_email_body
from classifier import load_clusters, classify_email
from cluster_editor import add_new_cluster, get_clusters, delete_cluster

#  Import reply generator
from reply_generator import load_profile, load_model_ollama, generate_reply

# Load profile and model once
profile = load_profile()
model_name = load_model_ollama()

# Load Gmail and Clusters
service = get_service()
unread_messages = get_unread_emails(service)
clusters = load_clusters()

# --- Streamlit UI ---
st.title("📧 Auto Email Classifier + Responder")

# Section 1: Display emails
st.header("Unread Emails")
if not unread_messages:
    st.success("✅ No unread messages.")
else:
    st.info(f"Found {len(unread_messages)} unread messages.")

    for msg in unread_messages:
        msg_id = msg['id']
        email_data = extract_email_details(service, msg_id)
        category = classify_email(email_data['subject'], email_data['body'], clusters)
        auto_reply = next((c["auto_reply"] for c in clusters["clusters"] if c["name"] == category), False)


        with st.expander(f"📨 {email_data['subject']}"):
            st.markdown(f"**From:** {email_data['from']}")
            st.markdown(f"**Date:** {email_data['date']}")
            st.markdown(f"**Category:** `{category}`")
            st.text_area("Body Preview", clean_email_body(email_data['body'][:500]), height=150)
            
            if auto_reply:

                #  reply generation button
                if st.button(f"⚡ Generate Reply to '{email_data['subject']}'", key=msg_id):
                    try:
                        reply = generate_reply(
                            email_body=email_data['body'],
                            sender=email_data['from'],
                            profile=profile,
                            model_name=model_name
                        )
                        st.success("Reply Generated:")
                        st.text_area("📤 Suggested Reply", reply, height=150)
                    except Exception as e:
                        st.error(f"❌ Error generating reply: {str(e)}")

# Section 2: Add new cluster
st.header("➕ Add New Cluster")
with st.form("cluster_form"):
    new_cluster_name = st.text_input("Cluster Name")
    new_keywords = st.text_input("Keywords (comma-separated)")
    auto_reply = st.checkbox("Enable Auto Reply", value=False)
    submitted = st.form_submit_button("Add Cluster")

    if submitted:
        if not new_cluster_name.strip() or not new_keywords.strip():
            st.error("Please provide both cluster name and keywords.")
        else:
            new_cluster = {
                "name": new_cluster_name.strip(),
                "keywords": [kw.strip().lower() for kw in new_keywords.split(",")],
                "auto_reply": auto_reply
            }

            success, msg = add_new_cluster(new_cluster)
            if success:
                st.success(msg)
            else:
                st.warning(msg)

# --- DISPLAY EXISTING CLUSTERS ---
st.header("🧠 Existing Clusters")

clusters, _ = get_clusters()

if clusters:
    display_options = [f"{c['name']} — {', '.join(c['keywords'])}" for c in clusters]
    selected_display = st.selectbox("Select a cluster to delete:", display_options)

    selected_cluster_name = selected_display.split(" — ")[0]

    if st.button("❌ Delete Selected Cluster"):
        delete_cluster(selected_cluster_name)
        st.success(f"Cluster '{selected_cluster_name}' deleted successfully.")
else:
    st.info("No clusters available.")
