import streamlit as st
from exception import CustomException
from logger import logging
from gmail_reader import get_service, extract_all_email_details, get_unread_emails
from cleaning import clean_email_body
from classifier import load_clusters, classify_email
from cluster_editor import add_new_cluster, get_clusters, delete_cluster
from reply_generator import load_profile, load_model_ollama, generate_reply

profile = load_profile()
model_name = load_model_ollama()

# Load Gmail 
service = get_service()
unread_messages = get_unread_emails(service, 10)


@st.cache_data
def load_resources(_service,unread_messages): 
    # Load Clusters
    all_email_data = extract_all_email_details(service, unread_messages)
    clusters = load_clusters()
    return all_email_data, clusters


# Load css styling
def inject_custom_css():
    with open("C:\\Users\\priyansh\\Downloads\\AutoEmail\\src\\style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



inject_custom_css()
all_email_data, clusters = load_resources(service,unread_messages)



# --- Streamlit UI ---
st.title("📧 Auto Email Classifier + Responder")


# Filter toggle: All vs Auto-Reply Only
view_mode = st.radio("📂 View Emails", ["Show All", "Filtered (Auto-Reply Enabled)"], horizontal=True)


# Section 1: Display emails
st.header("Unread Emails")

if not unread_messages:
    st.success("✅ No unread messages.")
else:
    if (view_mode!="Filtered (Auto-Reply Enabled)"):
        st.info(f"Found {len(unread_messages)} unread messages.")

    for email_data in all_email_data:
       
        category = classify_email(email_data['subject'], email_data['body'], clusters)
        auto_reply = next((c["auto_reply"] for c in clusters["clusters"] if c["name"] == category), False)
        
        if (auto_reply=="true"):
            auto_reply=True
        if (auto_reply=="false"):
            auto_reply=False
            
        # Filter emails based on user selection
        if view_mode == "Filtered (Auto-Reply Enabled)" and not auto_reply:
            continue  # Skip emails without auto-reply

        with st.expander(f"📨 {email_data['subject']}"):
            
            st.markdown('<div class="cluster-card">', unsafe_allow_html=True)
            
            st.markdown(f"**From:** {email_data['from']}")
            st.markdown(f"**Date:** {email_data['date']}")
            st.markdown(f"**Category:** `{category}`")
            st.text_area("Body Preview", clean_email_body(email_data['body']), height=150)

            # Reply generation button
            if st.button(f"⚡ Generate Reply to '{email_data['subject']}'"):
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
            st.markdown('</div>', unsafe_allow_html=True)

# Section 2: Add new cluster
with st.expander("➕ Add New Cluster"):
    st.subheader("Add New Cluster")
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
with st.expander("Existing Clusters"):
    st.subheader("Existing Clusters")
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
