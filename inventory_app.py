import streamlit as st
import pandas as pd
import warnings
from datetime import datetime, timedelta
import json
warnings.filterwarnings("ignore")

# --- PAGE CONFIG ---
st.set_page_config(page_title="FIFO Inventory Tracker", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "inventory_data" not in st.session_state:
    st.session_state["inventory_data"] = []

if "settings" not in st.session_state:
    st.session_state["settings"] = {
        "max_discount": 50,
        "critical_days": 3,
        "warning_days": 7,
        "moderate_days": 14,
        "discount_critical": 50,
        "discount_warning": 30,
        "discount_moderate": 15,
        "currency_symbol": "$"
    }

# --- HELPER FUNCTIONS ---
def calculate_days_until_expiry(expiry_date_str):
    """Calculate days remaining until expiry"""
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        today = datetime.today()
        days_left = (expiry_date - today).days
        return days_left
    except:
        return 0

def calculate_discount(days_left, settings=None):
    """Calculate discount percentage based on days until expiry"""
    if settings is None:
        settings = st.session_state["settings"]
    
    if days_left <= 0:
        return settings["max_discount"], "Expired"
    elif days_left <= settings["critical_days"]:
        return settings["discount_critical"], "Critical"
    elif days_left <= settings["warning_days"]:
        return settings["discount_warning"], "Warning"
    elif days_left <= settings["moderate_days"]:
        return settings["discount_moderate"], "Moderate"
    else:
        return 0, "Fresh"

def calculate_discounted_price(original_price, discount_percent, currency="$"):
    """Calculate price after discount"""
    discounted = original_price * (1 - discount_percent / 100)
    return f"{currency}{discounted:.2f}"

def get_inventory_stats():
    """Get comprehensive inventory statistics"""
    if not st.session_state["inventory_data"]:
        return {
            "total_items": 0,
            "total_quantity": 0,
            "expired": 0,
            "critical": 0,
            "warning": 0,
            "fresh": 0,
            "total_value": 0,
            "potential_loss": 0
        }
    
    df = pd.DataFrame(st.session_state["inventory_data"])
    stats = {
        "total_items": len(df),
        "total_quantity": df["Quantity"].sum(),
        "expired": 0,
        "critical": 0,
        "warning": 0,
        "fresh": 0,
        "total_value": 0,
        "potential_loss": 0
    }
    
    for _, row in df.iterrows():
        days_left = calculate_days_until_expiry(row["Expiry Date"])
        discount, status = calculate_discount(days_left)
        
        item_value = row["Price"] * row["Quantity"]
        stats["total_value"] += item_value
        
        if status == "Expired":
            stats["expired"] += 1
            stats["potential_loss"] += item_value
        elif status == "Critical":
            stats["critical"] += 1
            stats["potential_loss"] += item_value * (discount / 100)
        elif status == "Warning":
            stats["warning"] += 1
        else:
            stats["fresh"] += 1
    
    return stats

# --- NAVIGATION BAR ---
nav = st.radio("", ["Home", "Inventory", "Reports", "Settings"], horizontal=True)
st.markdown("---")

# --- HOME PAGE ---
if nav == "Home":
    st.markdown("## 📦 FIFO Inventory Tracker Dashboard")
    st.markdown("---")
    
    # Get statistics
    stats = get_inventory_stats()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", stats["total_items"])
    with col2:
        st.metric("Total Quantity", stats["total_quantity"])
    with col3:
        st.metric("Total Value", f"${stats['total_value']:.2f}")
    with col4:
        st.metric("Potential Loss", f"${stats['potential_loss']:.2f}", 
                 delta=f"-{stats['potential_loss']:.2f}" if stats['potential_loss'] > 0 else None,
                 delta_color="inverse")
    
    st.markdown("---")
    
    # Status Overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Inventory Status")
        if stats["total_items"] > 0:
            status_data = {
                "Fresh": stats["fresh"],
                "Moderate Risk": stats["warning"],
                "Critical": stats["critical"],
                "Expired": stats["expired"]
            }
            st.bar_chart(status_data)
        else:
            st.info("No inventory data to display. Add items in the Inventory tab.")
    
    with col2:
        st.markdown("### ⚠️ Priority Alerts")
        if st.session_state["inventory_data"]:
            alerts = []
            for item in st.session_state["inventory_data"]:
                days_left = calculate_days_until_expiry(item["Expiry Date"])
                discount, status = calculate_discount(days_left)
                
                if status in ["Expired", "Critical", "Warning"]:
                    icon = "🔴" if status == "Expired" else "🟠" if status == "Critical" else "🟡"
                    alerts.append({
                        "icon": icon,
                        "product": item["Product Name"],
                        "batch": item["Batch Number"],
                        "days": days_left,
                        "discount": discount
                    })
            
            # Sort by urgency (days left)
            alerts.sort(key=lambda x: x["days"])
            
            if alerts:
                for alert in alerts[:5]:  # Show top 5 alerts
                    if alert["days"] <= 0:
                        st.error(f"{alert['icon']} **{alert['product']}** (Batch #{alert['batch']}) – EXPIRED! Discount: {alert['discount']}%")
                    else:
                        st.warning(f"{alert['icon']} **{alert['product']}** (Batch #{alert['batch']}) – {alert['days']} days left. Discount: {alert['discount']}%")
            else:
                st.success("✅ No critical alerts. All items are fresh!")
        else:
            st.info("No alerts. Add inventory items to track expiry dates.")
    
    st.markdown("---")
    
    # Current Inventory Table with Dynamic Discounts
    st.markdown("### 🛒 Current Inventory with Live Pricing")
    
    if st.session_state["inventory_data"]:
        inventory_df = pd.DataFrame(st.session_state["inventory_data"])
        
        # Calculate dynamic fields
        inventory_df["Days Until Expiry"] = inventory_df["Expiry Date"].apply(calculate_days_until_expiry)
        inventory_df["Discount %"], inventory_df["Status"] = zip(*inventory_df["Days Until Expiry"].apply(calculate_discount))
        inventory_df["Original Price"] = inventory_df["Price"].apply(lambda x: f"${x:.2f}")
        inventory_df["Discounted Price"] = inventory_df.apply(
            lambda row: calculate_discounted_price(row["Price"], row["Discount %"]), axis=1
        )
        inventory_df["Total Value"] = inventory_df.apply(
            lambda row: f"${row['Price'] * row['Quantity'] * (1 - row['Discount %']/100):.2f}", axis=1
        )
        
        # Display table
        display_df = inventory_df[[
            "Product Name", "Batch Number", "Quantity", "Days Until Expiry", 
            "Status", "Original Price", "Discount %", "Discounted Price", "Total Value"
        ]]
        
        # Color code by status
        def highlight_status(row):
            if row["Status"] == "Expired":
                return ['background-color: #ffcccc'] * len(row)
            elif row["Status"] == "Critical":
                return ['background-color: #ffe6cc'] * len(row)
            elif row["Status"] == "Warning":
                return ['background-color: #ffffcc'] * len(row)
            else:
                return ['background-color: #ccffcc'] * len(row)
        
        st.dataframe(display_df.style.apply(highlight_status, axis=1), use_container_width=True)
        
        # Summary
        st.markdown("#### 💡 Quick Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Expired Items:** {stats['expired']}")
        with col2:
            st.warning(f"**Items Needing Discount:** {stats['critical'] + stats['warning']}")
        with col3:
            st.success(f"**Fresh Items:** {stats['fresh']}")
    else:
        st.info("No items in inventory yet. Go to the **Inventory** tab to add products.")

# --- INVENTORY PAGE ---
elif nav == "Inventory":
    st.markdown("## 📝 Inventory Management")
    st.markdown("---")
    
    # Add New Item Section
    st.markdown("### ➕ Add New Inventory Item")
    
    with st.form("inventory_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            product_name = st.text_input("Product Name*", placeholder="e.g., Milk")
            product_id = st.text_input("Product ID*", placeholder="e.g., PRD-001")
            price = st.number_input("Unit Price ($)*", min_value=0.01, value=1.0, step=0.01, format="%.2f")
        
        with col2:
            batch_number = st.text_input("Batch Number*", placeholder="e.g., BATCH-2024-001")
            quantity = st.number_input("Quantity*", min_value=1, value=1, step=1)
            shelf_life = st.number_input("Shelf Life (days)", min_value=1, value=7, step=1, 
                                        help="Total shelf life from production date")
        
        with col3:
            expiry_date = st.date_input("Expiry Date*", min_value=datetime.today())
            category = st.selectbox("Category", ["Dairy", "Produce", "Meat", "Bakery", "Beverages", "Other"])
            location = st.text_input("Storage Location", placeholder="e.g., Refrigerator A1")
        
        notes = st.text_area("Notes (Optional)", placeholder="Additional information about this item...")
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            submitted = st.form_submit_button("➕ Add Item", use_container_width=True)
        with col2:
            clear = st.form_submit_button("🔄 Clear", use_container_width=True)
    
    if submitted:
        if not product_name or not product_id or not batch_number:
            st.error("⚠️ Please fill in all required fields marked with *")
        else:
            # Check for duplicate Product ID
            if any(item["Product ID"] == product_id for item in st.session_state["inventory_data"]):
                st.error(f"⚠️ Product ID '{product_id}' already exists. Please use a unique ID.")
            else:
                new_item = {
                    "Product Name": product_name,
                    "Product ID": product_id,
                    "Batch Number": batch_number,
                    "Expiry Date": expiry_date.strftime("%Y-%m-%d"),
                    "Quantity": int(quantity),
                    "Price": float(price),
                    "Shelf Life": int(shelf_life),
                    "Category": category,
                    "Location": location,
                    "Notes": notes,
                    "Date Added": datetime.today().strftime("%Y-%m-%d")
                }
                st.session_state["inventory_data"].append(new_item)
                st.success(f"✅ {product_name} (ID: {product_id}) successfully added to inventory!")
                st.balloons()
    
    st.markdown("---")
    
    # Current Inventory Display and Management
    st.markdown("### 📦 Current Inventory")
    
    if st.session_state["inventory_data"]:
        inventory_df = pd.DataFrame(st.session_state["inventory_data"])
        
        # Add search and filter
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            search = st.text_input("🔍 Search", placeholder="Search by name, ID, or batch...")
        with col2:
            category_filter = st.multiselect("Filter by Category", 
                                            options=inventory_df["Category"].unique(),
                                            default=None)
        with col3:
            status_filter = st.multiselect("Filter by Status", 
                                          options=["Fresh", "Moderate", "Warning", "Critical", "Expired"],
                                          default=None)
        
        # Apply filters
        filtered_df = inventory_df.copy()
        
        if search:
            filtered_df = filtered_df[
                filtered_df["Product Name"].str.contains(search, case=False) |
                filtered_df["Product ID"].str.contains(search, case=False) |
                filtered_df["Batch Number"].str.contains(search, case=False)
            ]
        
        if category_filter:
            filtered_df = filtered_df[filtered_df["Category"].isin(category_filter)]
        
        # Calculate dynamic fields
        filtered_df["Days Until Expiry"] = filtered_df["Expiry Date"].apply(calculate_days_until_expiry)
        filtered_df["Discount %"], filtered_df["Status"] = zip(*filtered_df["Days Until Expiry"].apply(calculate_discount))
        
        if status_filter:
            filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
        
        filtered_df["Discounted Price"] = filtered_df.apply(
            lambda row: calculate_discounted_price(row["Price"], row["Discount %"]), axis=1
        )
        
        # Display inventory with edit/delete options
        st.markdown(f"**Showing {len(filtered_df)} of {len(inventory_df)} items**")
        
        for idx, row in filtered_df.iterrows():
            with st.expander(f"**{row['Product Name']}** - {row['Product ID']} | Status: {row['Status']} | Discount: {row['Discount %']}%"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Batch:** {row['Batch Number']}")
                    st.write(f"**Category:** {row['Category']}")
                    st.write(f"**Quantity:** {row['Quantity']}")
                with col2:
                    st.write(f"**Original Price:** ${row['Price']:.2f}")
                    st.write(f"**Discounted Price:** {row['Discounted Price']}")
                    st.write(f"**Total Value:** ${row['Price'] * row['Quantity'] * (1 - row['Discount %']/100):.2f}")
                with col3:
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Days Left:** {row['Days Until Expiry']}")
                    st.write(f"**Shelf Life:** {row['Shelf Life']} days")
                with col4:
                    st.write(f"**Location:** {row['Location']}")
                    st.write(f"**Date Added:** {row['Date Added']}")
                    if row['Notes']:
                        st.write(f"**Notes:** {row['Notes']}")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                        st.session_state["inventory_data"].pop(idx)
                        st.rerun()
                with col2:
                    if st.button(f"📝 Edit", key=f"edit_{idx}"):
                        st.info("Edit functionality: Use delete and re-add for now.")
        
        # Export option
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"inventory_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            if st.button("🗑️ Clear All", type="secondary"):
                if st.session_state.get("confirm_clear"):
                    st.session_state["inventory_data"] = []
                    st.session_state["confirm_clear"] = False
                    st.rerun()
                else:
                    st.session_state["confirm_clear"] = True
                    st.warning("Click again to confirm clearing all inventory!")
    else:
        st.info("📭 No items in inventory yet. Add your first item using the form above!")

# --- REPORTS PAGE ---
elif nav == "Reports":
    st.markdown("## 📊 Inventory Analytics & Reports")
    st.markdown("---")
    
    if not st.session_state["inventory_data"]:
        st.info("📭 No inventory data available. Please add items in the **Inventory** tab to generate reports.")
    else:
        df = pd.DataFrame(st.session_state["inventory_data"])
        
        # Calculate metrics
        df["Days Until Expiry"] = df["Expiry Date"].apply(calculate_days_until_expiry)
        df["Discount %"], df["Status"] = zip(*df["Days Until Expiry"].apply(calculate_discount))
        df["Original Total Value"] = df["Price"] * df["Quantity"]
        df["Discounted Total Value"] = df.apply(
            lambda row: row["Price"] * row["Quantity"] * (1 - row["Discount %"] / 100), axis=1
        )
        df["Potential Loss"] = df["Original Total Value"] - df["Discounted Total Value"]
        
        # Summary Metrics
        st.markdown("### 📈 Financial Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Inventory Value", f"${df['Original Total Value'].sum():.2f}")
        with col2:
            st.metric("Value After Discounts", f"${df['Discounted Total Value'].sum():.2f}")
        with col3:
            st.metric("Total Discount Impact", f"${df['Potential Loss'].sum():.2f}",
                     delta=f"-{(df['Potential Loss'].sum() / df['Original Total Value'].sum() * 100):.1f}%",
                     delta_color="inverse")
        with col4:
            avg_discount = df["Discount %"].mean()
            st.metric("Average Discount", f"{avg_discount:.1f}%")
        
        st.markdown("---")
        
        # Charts Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Items by Status")
            status_counts = df["Status"].value_counts()
            st.bar_chart(status_counts)
            
            st.markdown("### 💰 Value by Category")
            category_value = df.groupby("Category")["Discounted Total Value"].sum().sort_values(ascending=False)
            st.bar_chart(category_value)
        
        with col2:
            st.markdown("### ⏰ Expiry Timeline")
            expiry_bins = pd.cut(df["Days Until Expiry"], 
                                bins=[-float('inf'), 0, 3, 7, 14, 30, float('inf')],
                                labels=["Expired", "0-3 days", "4-7 days", "8-14 days", "15-30 days", "30+ days"])
            expiry_counts = expiry_bins.value_counts()
            st.bar_chart(expiry_counts)
            
            st.markdown("### 📦 Top Products by Quantity")
            top_products = df.nlargest(5, "Quantity")[["Product Name", "Quantity"]].set_index("Product Name")
            st.bar_chart(top_products)
        
        st.markdown("---")
        
        # Detailed Report Table
        st.markdown("### 📋 Detailed Inventory Report")
        
        # Add sorting and filtering
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("Sort by", ["Days Until Expiry", "Discount %", "Status", "Product Name", "Potential Loss"])
        with col2:
            sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
        
        ascending = (sort_order == "Ascending")
        sorted_df = df.sort_values(by=sort_by, ascending=ascending)
        
        # Display comprehensive table
        report_df = sorted_df[[
            "Product Name", "Product ID", "Batch Number", "Category", "Quantity",
            "Expiry Date", "Days Until Expiry", "Status", "Discount %",
            "Price", "Original Total Value", "Discounted Total Value", "Potential Loss"
        ]].copy()
        
        # Format currency columns
        report_df["Price"] = report_df["Price"].apply(lambda x: f"${x:.2f}")
        report_df["Original Total Value"] = report_df["Original Total Value"].apply(lambda x: f"${x:.2f}")
        report_df["Discounted Total Value"] = report_df["Discounted Total Value"].apply(lambda x: f"${x:.2f}")
        report_df["Potential Loss"] = report_df["Potential Loss"].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(report_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Critical Items Section
        st.markdown("### 🚨 Critical Action Items")
        
        critical_items = df[df["Status"].isin(["Expired", "Critical"])]
        
        if len(critical_items) > 0:
            st.error(f"⚠️ {len(critical_items)} items require immediate attention!")
            
            for _, item in critical_items.iterrows():
                with st.expander(f"🔴 {item['Product Name']} - {item['Status']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Product ID:** {item['Product ID']}")
                        st.write(f"**Batch:** {item['Batch Number']}")
                        st.write(f"**Days Left:** {item['Days Until Expiry']}")
                    with col2:
                        st.write(f"**Quantity:** {item['Quantity']}")
                        st.write(f"**Current Discount:** {item['Discount %']}%")
                        st.write(f"**Potential Loss:** ${item['Potential Loss']:.2f}")
                    with col3:
                        st.write("**Recommended Actions:**")
                        if item["Days Until Expiry"] <= 0:
                            st.write("- Remove from inventory immediately")
                            st.write("- Dispose according to regulations")
                        else:
                            st.write(f"- Apply {item['Discount %']}% discount")
                            st.write("- Promote with special signage")
                            st.write("- Consider bundling with popular items")
        else:
            st.success("✅ No critical items. All inventory is in good condition!")
        
        st.markdown("---")
        
        # Export Options
        st.markdown("### 📥 Export Reports")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            full_csv = report_df.to_csv(index=False)
            st.download_button(
                label="📄 Full Report (CSV)",
                data=full_csv,
                file_name=f"inventory_report_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            critical_csv = df[df["Status"].isin(["Expired", "Critical"])].to_csv(index=False)
            st.download_button(
                label="🚨 Critical Items (CSV)",
                data=critical_csv,
                file_name=f"critical_items_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col3:
            summary_data = {
                "Metric": ["Total Items", "Total Value", "Discounted Value", "Potential Loss", "Expired Items", "Critical Items"],
                "Value": [
                    len(df),
                    f"${df['Original Total Value'].sum():.2f}",
                    f"${df['Discounted Total Value'].sum():.2f}",
                    f"${df['Potential Loss'].sum():.2f}",
                    len(df[df["Status"] == "Expired"]),
                    len(df[df["Status"] == "Critical"])
                ]
            }
            summary_csv = pd.DataFrame(summary_data).to_csv(index=False)
            st.download_button(
                label="📊 Summary (CSV)",
                data=summary_csv,
                file_name=f"summary_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# --- SETTINGS PAGE ---
elif nav == "Settings":
    st.markdown("## ⚙️ System Settings")
    st.markdown("---")
    
    st.markdown("### 🎯 Discount Configuration")
    st.write("Configure how discounts are calculated based on expiry dates.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Expiry Thresholds (Days)")
        critical_days = st.number_input(
            "Critical Threshold",
            min_value=1,
            max_value=7,
            value=st.session_state["settings"]["critical_days"],
            help="Items expiring within this many days get the highest discount"
        )
        warning_days = st.number_input(
            "Warning Threshold",
            min_value=critical_days + 1,
            max_value=14,
            value=st.session_state["settings"]["warning_days"],
            help="Items expiring within this many days get a moderate discount"
        )
        moderate_days = st.number_input(
            "Moderate Threshold",
            min_value=warning_days + 1,
            max_value=30,
            value=st.session_state["settings"]["moderate_days"],
            help="Items expiring within this many days get a small discount"
        )
    
    with col2:
        st.markdown("#### Discount Percentages")
        discount_critical = st.slider(
            "Critical Discount (%)",
            min_value=0,
            max_value=100,
            value=st.session_state["settings"]["discount_critical"],
            help=f"Discount for items expiring in ≤{critical_days} days"
        )
        discount_warning = st.slider(
            "Warning Discount (%)",
            min_value=0,
            max_value=discount_critical,
            value=st.session_state["settings"]["discount_warning"],
            help=f"Discount for items expiring in ≤{warning_days} days"
        )
        discount_moderate = st.slider(
            "Moderate Discount (%)",
            min_value=0,
            max_value=discount_warning,
            value=st.session_state["settings"]["discount_moderate"],
            help=f"Discount for items expiring in ≤{moderate_days} days"
        )
        max_discount = st.slider(
            "Max Discount for Expired Items (%)",
            min_value=0,
            max_value=100,
            value=st.session_state["settings"]["max_discount"],
            help="Maximum discount for already expired items"
        )
    
    st.markdown("---")
    
    # Display Configuration Preview
    st.markdown("### 📋 Configuration Preview")
    config_preview = pd.DataFrame({
        "Status": ["Expired", "Critical", "Warning", "Moderate", "Fresh"],
        "Days Until Expiry": [
            "≤ 0",
            f"1-{critical_days}",
            f"{critical_days+1}-{warning_days}",
            f"{warning_days+1}-{moderate_days}",
            f"> {moderate_days}"
        ],
        "Discount %": [
            max_discount,
            discount_critical,
            discount_warning,
            discount_moderate,
            0
        ]
    })
    st.table(config_preview)
    
    # Save Settings
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.session_state["settings"]["critical_days"] = critical_days
            st.session_state["settings"]["warning_days"] = warning_days
            st.session_state["settings"]["moderate_days"] = moderate_days
            st.session_state["settings"]["discount_critical"] = discount_critical
            st.session_state["settings"]["discount_warning"] = discount_warning
            st.session_state["settings"]["discount_moderate"] = discount_moderate
            st.session_state["settings"]["max_discount"] = max_discount
            st.success("✅ Settings saved successfully!")
            st.balloons()
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.session_state["settings"] = {
                "max_discount": 50,
                "critical_days": 3,
                "warning_days": 7,
                "moderate_days": 14,
                "discount_critical": 50,
                "discount_warning": 30,
                "discount_moderate": 15,
                "currency_symbol": "$"
            }
            st.success("✅ Settings reset to defaults!")
            st.rerun()
    
    st.markdown("---")
    
    # Data Management
    st.markdown("### 💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Data")
        if st.session_state["inventory_data"]:
            # Export as JSON
            json_data = json.dumps({
                "inventory": st.session_state["inventory_data"],
                "settings": st.session_state["settings"],
                "export_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2)
            
            st.download_button(
                label="📦 Export All Data (JSON)",
                data=json_data,
                file_name=f"inventory_backup_{datetime.today().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("No inventory data to export.")
    
    with col2:
        st.markdown("#### Import Data")
        uploaded_file = st.file_uploader("Choose a JSON backup file", type=['json'])
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                
                if st.button("📥 Import Data", type="primary", use_container_width=True):
                    if "inventory" in import_data:
                        st.session_state["inventory_data"] = import_data["inventory"]
                    if "settings" in import_data:
                        st.session_state["settings"] = import_data["settings"]
                    st.success("✅ Data imported successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error importing file: {str(e)}")
    
    st.markdown("---")
    
    # System Information
    st.markdown("### ℹ️ System Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Inventory Items", len(st.session_state["inventory_data"]))
    with col2:
        if st.session_state["inventory_data"]:
            total_value = sum(item["Price"] * item["Quantity"] for item in st.session_state["inventory_data"])
            st.metric("Total Inventory Value", f"${total_value:.2f}")
        else:
            st.metric("Total Inventory Value", "$0.00")
    with col3:
        st.metric("Last Updated", datetime.today().strftime("%Y-%m-%d"))
    
    st.markdown("---")
    
    # About Section
    with st.expander("ℹ️ About FIFO Inventory Tracker"):
        st.markdown("""
        **FIFO Inventory Tracker v2.0**
        
        A comprehensive inventory management system with dynamic discount calculations based on expiry dates.
        
        **Features:**
        - Real-time inventory tracking
        - Automatic discount calculation based on expiry dates
        - Comprehensive reporting and analytics
        - Data export/import capabilities
        - Configurable discount thresholds
        
        **How it works:**
        1. Add products with expiry dates in the Inventory tab
        2. System automatically calculates discounts based on days until expiry
        3. View real-time analytics and alerts on the Home tab
        4. Generate detailed reports in the Reports tab
        5. Configure discount rules in Settings
        
        **Discount Algorithm:**
        - Products are categorized based on days until expiry
        - Discounts are automatically applied to minimize waste
        - Settings can be customized to match business needs
        
        For support or feature requests, please contact your system administrator.
        """)
    
    # Danger Zone
    with st.expander("⚠️ Danger Zone"):
        st.warning("**Warning:** The following actions are irreversible!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Inventory Data", type="secondary", use_container_width=True):
                if st.session_state.get("confirm_clear_all"):
                    st.session_state["inventory_data"] = []
                    st.session_state["confirm_clear_all"] = False
                    st.success("✅ All inventory data cleared!")
                    st.rerun()
                else:
                    st.session_state["confirm_clear_all"] = True
                    st.error("⚠️ Click again to confirm!")
        
        with col2:
            if st.button("🔄 Reset Everything", type="secondary", use_container_width=True):
                if st.session_state.get("confirm_reset_all"):
                    st.session_state["inventory_data"] = []
                    st.session_state["settings"] = {
                        "max_discount": 50,
                        "critical_days": 3,
                        "warning_days": 7,
                        "moderate_days": 14,
                        "discount_critical": 50,
                        "discount_warning": 30,
                        "discount_moderate": 15,
                        "currency_symbol": "$"
                    }
                    st.session_state["confirm_reset_all"] = False
                    st.success("✅ System reset complete!")
                    st.rerun()
                else:
                    st.session_state["confirm_reset_all"] = True
                    st.error("⚠️ Click again to confirm!")
