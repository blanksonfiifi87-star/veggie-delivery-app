import streamlit as st
import pandas as pd
import pydeck as pdk
import random

st.set_page_config(page_title="FreshVeggies Express", layout="wide")

# Mock Database Initialization
if "orders" not in st.session_state:
    st.session_state.orders = pd.DataFrame([
        {"Order ID": 101, "Item": "Tomatoes (2kg)", "Customer": "Ama K.", "Lat": 5.530, "Lon": -0.620, "Status": "Pending", "Driver": "Unassigned"},
        {"Order ID": 102, "Item": "Spinach & Onions", "Customer": "Kojo M.", "Lat": 5.535, "Lon": -0.628, "Status": "Out for Delivery", "Driver": "Kwame (Driver 1)"},
    ])

if "demand_zones" not in st.session_state:
    # Simulated high-demand areas (latitude, longitude, demand intensity)
    st.session_state.demand_zones = pd.DataFrame([
        {"lat": 5.532, "lon": -0.622, "weight": 8},
        {"lat": 5.538, "lon": -0.625, "weight": 12},
        {"lat": 5.528, "lon": -0.618, "weight": 5},
    ])

# Navigation
st.title("🥬 FreshVeggies Logistics & Store")
role = st.sidebar.selectbox("Select View Portal", ["Shop Owner Dashboard", "Delivery Driver App", "Customer Shop"])

# --- VIEW 1: SHOP OWNER DASHBOARD ---
if role == "Shop Owner Dashboard":
    st.header("Shop Owner Management Console")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 High-Demand Zones & Delivery Map")
        # Heatmap layer for high demand areas
        heatmap_layer = pdk.Layer(
            "HeatmapLayer",
            data=st.session_state.demand_zones,
            get_position=["lon", "lat"],
            get_weight="weight",
            radius_pixels=60,
        )
        # Scatter layer for active orders
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=st.session_state.orders,
            get_position=["Lon", "Lat"],
            get_color="[200, 30, 0, 160]",
            get_radius=80,
            pickable=True
        )
        
        view_state = pdk.ViewState(latitude=5.532, longitude=-0.622, zoom=13)
        st.pydeck_chart(pdk.Deck(layers=[heatmap_layer, scatter_layer], initial_view_state=view_state, tooltip={"text": "Order: {Item}\nStatus: {Status}"}))

    with col2:
        st.subheader("📦 Manage Orders & Assign Drivers")
        df = st.session_state.orders
        st.dataframe(df[["Order ID", "Item", "Status", "Driver"]], hide_index=True)
        
        selected_id = st.selectbox("Select Order ID to Assign", df["Order ID"])
        driver_name = st.text_input("Driver Name", "Kwame")
        
        if st.button("Assign Driver"):
            st.session_state.orders.loc[st.session_state.orders["Order ID"] == selected_id, "Driver"] = driver_name
            st.session_state.orders.loc[st.session_state.orders["Order ID"] == selected_id, "Status"] = "Assigned"
            st.success(f"Assigned Order #{selected_id} to {driver_name}")

# --- VIEW 2: DELIVERY DRIVER APP ---
elif role == "Delivery Driver App":
    st.header("🚚 Driver Delivery Portal")
    driver_filter = st.selectbox("Select Your Name", ["Kwame (Driver 1)", "Unassigned"])
    
    my_orders = st.session_state.orders[st.session_state.orders["Driver"] == driver_filter]
    
    if my_orders.empty:
        st.info("No active deliveries assigned to you right now.")
    else:
        for idx, row in my_orders.iterrows():
            with st.card() if hasattr(st, "card") else st.container():
                st.write(f"**Order #{row['Order ID']}** - {row['Item']}")
                st.write(f"Customer: {row['Customer']} | Status: **{row['Status']}**")
                
                new_status = st.selectbox(f"Update Status for #{row['Order ID']}", ["Assigned", "Out for Delivery", "Delivered"], key=f"status_{row['Order ID']}")
                if st.button(f"Update Order #{row['Order ID']}", key=f"btn_{row['Order ID']}"):
                    st.session_state.orders.loc[st.session_state.orders["Order ID"] == row["Order ID"], "Status"] = new_status
                    st.success("Status Updated!")

# --- VIEW 3: CUSTOMER SHOP ---
elif role == "Customer Shop":
    st.header("🛒 Order Fresh Vegetables")
    
    veg_choice = st.selectbox("Choose Veggie Pack", ["Tomato Basket", "Leafy Greens Mix", "Onion & Pepper Combo"])
    cust_name = st.text_input("Your Name")
    
    if st.button("Place Order"):
        new_id = random.randint(103, 999)
        # Random location offset near store for demo
        new_order = {
            "Order ID": new_id,
            "Item": veg_choice,
            "Customer": cust_name if cust_name else "Guest",
            "Lat": 5.532 + random.uniform(-0.01, 0.01),
            "Lon": -0.622 + random.uniform(-0.01, 0.01),
            "Status": "Pending",
            "Driver": "Unassigned"
        }
        st.session_state.orders = pd.concat([st.session_state.orders, pd.DataFrame([new_order])], ignore_index=True)
        
        # Log location as demand
        new_demand = {"lat": new_order["Lat"], "lon": new_order["Lon"], "weight": 5}
        st.session_state.demand_zones = pd.concat([st.session_state.demand_zones, pd.DataFrame([new_demand])], ignore_index=True)
        
        st.success(f"Order placed successfully! Order ID: #{new_id}")
