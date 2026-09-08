import streamlit as st
import pandas as pd
import pydeck as pdk
import random
from supabase import create_client

st.set_page_config(page_title="FreshVeggies Express", layout="wide")

# Initialize Supabase connection using Streamlit secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Fetch active orders directly from Supabase
def fetch_orders():
    response = supabase.table("orders").select("*").execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=["id", "item", "customer", "lat", "lon", "status", "driver"])
    return pd.DataFrame(data)

st.title("🥬 FreshVeggies Logistics & Store")
role = st.sidebar.selectbox("Select View Portal", ["Shop Owner Dashboard", "Delivery Driver App", "Customer Shop"])

df_orders = fetch_orders()

# --- VIEW 1: SHOP OWNER DASHBOARD ---
if role == "Shop Owner Dashboard":
    st.header("Shop Owner Management Console")
    
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
            # Center map on average coordinate of orders
            view_state = pdk.ViewState(latitude=df_orders["lat"].mean(), longitude=df_orders["lon"].mean(), zoom=12)
            st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip={"text": "Item: {item}\nStatus: {status}"}))
        else:
            st.info("No active orders on the map yet.")

    with col2:
        st.subheader("📦 Order List & Driver Assignment")
        if not df_orders.empty:
            st.dataframe(df_orders[["id", "item", "customer", "status", "driver"]], hide_index=True)
            
            selected_id = st.selectbox("Assign Driver to Order ID", df_orders["id"])
            driver_name = st.text_input("Driver Name", "Kwame")
            
            if st.button("Assign Driver"):
                supabase.table("orders").update({"driver": driver_name, "status": "Assigned"}).eq("id", selected_id).execute()
                st.success(f"Assigned Order #{selected_id} to {driver_name}")
                st.rerun()
        else:
            st.info("Waiting for new orders...")

# --- VIEW 2: DELIVERY DRIVER APP ---
elif role == "Delivery Driver App":
    st.header("🚚 Driver Delivery Portal")
    driver_name_input = st.text_input("Enter Your Name to View Assigned Runs", "Kwame")
    
    if not df_orders.empty:
        my_orders = df_orders[df_orders["driver"] == driver_name_input]
        
        if my_orders.empty:
            st.info(f"No active deliveries assigned to {driver_name_input}.")
        else:
            for idx, row in my_orders.iterrows():
                st.write(f"**Order #{row['id']}** — {row['item']}")
                st.write(f"Customer: {row['customer']} | Current Status: **{row['status']}**")
                
                new_status = st.selectbox(f"Update Status for #{row['id']}", ["Assigned", "Out for Delivery", "Delivered"], key=f"status_{row['id']}")
                if st.button(f"Update Order #{row['id']}", key=f"btn_{row['id']}"):
                    supabase.table("orders").update({"status": new_status}).eq("id", row["id"]).execute()
                    st.success("Status Updated!")
                    st.rerun()

# --- VIEW 3: CUSTOMER SHOP ---
elif role == "Customer Shop":
    st.header("🛒 Order Fresh Vegetables")
    
    veg_choice = st.selectbox("Choose Veggie Pack", ["Tomato Basket", "Leafy Greens Mix", "Onion & Pepper Combo"])
    cust_name = st.text_input("Your Name")
    
    if st.button("Place Order"):
        # Generate random coordinate near store location for demo tracking
        new_order = {
            "item": veg_choice,
            "customer": cust_name if cust_name else "Guest",
            "lat": 6.688 + random.uniform(-0.01, 0.01),
            "lon": -1.624 + random.uniform(-0.01, 0.01),
            "status": "Pending",
            "driver": "Unassigned"
        }
        supabase.table("orders").insert(new_order).execute()
        st.success("Order placed successfully! The shop owner and drivers can now see it live.")
        st.rerun()
