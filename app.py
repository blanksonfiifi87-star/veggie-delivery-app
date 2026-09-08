import streamlit as st
import pandas as pd
import pydeck as pdk
import random
from supabase import create_client

st.set_page_config(page_title="FreshVeggies Express", layout="wide")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def fetch_orders():
    response = supabase.table("orders").select("*").execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=["id", "item", "customer", "lat", "lon", "status", "driver"])
    return pd.DataFrame(data)

def fetch_drivers():
    response = supabase.table("users").select("username").eq("role", "Driver").execute()
    data = response.data
    if not data:
        return ["Unassigned"]
    return [d["username"] for d in data]

# Authenticate user from Supabase database
def login_user(username, password):
    response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    if response.data:
        return response.data[0] # Returns user dict containing role
    return None

# Manage Login Session State
if "user" not in st.session_state:
    st.session_state["user"] = None

st.title("🥬 FreshVeggies Express")

# Navigation Mode Selection
portal_type = st.sidebar.radio("Navigation", ["🛒 Customer Shop", "🔐 Staff Login"])

df_orders = fetch_orders()

# --- 1. PUBLIC CUSTOMER SHOP ---
if portal_type == "🛒 Customer Shop":
    st.header("Order Fresh Vegetables")
    
    veg_choice = st.selectbox("Choose Veggie Pack", ["Tomato Basket", "Leafy Greens Mix", "Onion & Pepper Combo"])
    cust_name = st.text_input("Your Name / Phone Number")
    
    if st.button("Place Order"):
        new_order = {
            "item": veg_choice,
            "customer": cust_name if cust_name else "Guest",
            "lat": 6.688 + random.uniform(-0.01, 0.01),
            "lon": -1.624 + random.uniform(-0.01, 0.01),
            "status": "Pending",
            "driver": "Unassigned"
        }
        supabase.table("orders").insert(new_order).execute()
        st.success("Order placed successfully! The shop will process your delivery soon.")
        st.rerun()

# --- 2. PROTECTED STAFF LOGIN & PORTAL ---
elif portal_type == "🔐 Staff Login":
    
    # Show Login Screen if not logged in
    if st.session_state["user"] is None:
        st.subheader("Staff Account Login")
        
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Sign In")
            
            if submit_button:
                user_account = login_user(username_input.lower().strip(), password_input)
                if user_account:
                    st.session_state["user"] = user_account
                    st.success(f"Welcome back, {user_account['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")

    # Display Dashboard once authenticated
    else:
        current_user = st.session_state["user"]
        st.sidebar.write(f"Logged in as: **{current_user['username']}** ({current_user['role']})")
        
        if st.sidebar.button("Logout"):
            st.session_state["user"] = None
            st.rerun()

        # FIIFI'S OWNER DASHBOARD
        if current_user["role"] == "Owner":
            st.header("Shop Owner Management Console")
            
            # Form to register a new driver
            with st.expander("➕ Register a New Driver Account"):
                with st.form("add_driver_form"):
                    new_driver_username = st.text_input("New Driver Username")
                    new_driver_password = st.text_input("New Driver Password", type="password")
                    add_driver_btn = st.form_submit_button("Create Driver Account")
                    
                    if add_driver_btn:
                        if new_driver_username and new_driver_password:
                            try:
                                supabase.table("users").insert({
                                    "username": new_driver_username.lower().strip(),
                                    "password": new_driver_password,
                                    "role": "Driver"
                                }).execute()
                                st.success(f"Driver '{new_driver_username}' created successfully! They can now log in.")
                                st.rerun()
                            except Exception as e:
                                st.error("Error creating driver. Username might already exist.")
                        else:
                            st.warning("Please provide both a username and password.")

            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📍 Live Delivery Map")
                if not df_orders.empty:
                    scatter_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=df_orders,
                        get_position=["lon", "lat"],
                        get_color="[200, 30, 0, 160]",
                        get_radius=100,
                        pickable=True
                    )
                    view_state = pdk.ViewState(latitude=df_orders["lat"].mean(), longitude=df_orders["lon"].mean(), zoom=12)
                    st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip={"text": "Item: {item}\nStatus: {status}"}))
                else:
                    st.info("No active orders on the map yet.")

            with col2:
                st.subheader("📦 Order Management")
                if not df_orders.empty:
                    st.dataframe(df_orders[["id", "item", "customer", "status", "driver"]], hide_index=True)
                    
                    driver_list = fetch_drivers()
                    selected_id = st.selectbox("Assign Driver to Order ID", df_orders["id"])
                    driver_name = st.selectbox("Select Driver", driver_list)
                    
                    if st.button("Assign Driver"):
                        supabase.table("orders").update({"driver": driver_name, "status": "Assigned"}).eq("id", selected_id).execute()
                        st.success(f"Assigned Order #{selected_id} to {driver_name}")
                        st.rerun()
                else:
                    st.info("Waiting for incoming orders...")

        # DRIVER VIEW
        elif current_user["role"] == "Driver":
            st.header(f"🚚 Driver Portal: {current_user['username']}")
            
            if not df_orders.empty:
                my_orders = df_orders[df_orders["driver"] == current_user["username"]]
                
                if my_orders.empty:
                    st.info(f"No active deliveries assigned to {current_user['username']}.")
                else:
                    for idx, row in my_orders.iterrows():
                        st.write(f"**Order #{row['id']}** — {row['item']}")
                        st.write(f"Customer: {row['customer']} | Status: **{row['status']}**")
                        
                        new_status = st.selectbox(f"Update Status for #{row['id']}", ["Assigned", "Out for Delivery", "Delivered"], key=f"status_{row['id']}")
                        if st.button(f"Update Order #{row['id']}", key=f"btn_{row['id']}"):
                            supabase.table("orders").update({"status": new_status}).eq("id", row["id"]).execute()
                            st.success("Status Updated!")
                            st.rerun()
