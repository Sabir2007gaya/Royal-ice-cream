import streamlit as st
from pymongo import MongoClient
from datetime import datetime

# Connect to DB
@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client[st.secrets["mongodb"]["database"]]
    return db
db = get_db()

# Global for helpline number
HELPLINE = "+91-XXXXXXXXXX"

def main():
    st.title("Welcome to Royal Ice Cream")
    st.write(f"📞 Helpline: {HELPLINE}")

    option = st.selectbox("Choose an option:", ["User", "Admin", "Terms and Conditions"])
    if option == "Terms and Conditions":
        terms_and_conditions()
    elif option == "Admin":
        admin_login()
    elif option == "User":
        user_login()

def terms_and_conditions():
    st.header("Terms and Conditions")
    st.write("Add your detailed terms & conditions here.")

def send_otp(input_value, mode):
    st.info(f"OTP sent to {input_value} ({mode}). (Simulation)")
    # Integrate with Twilio/SMTP for real OTP

# Admin registration & login
def admin_login():
    st.header("Admin Login")
    mode = st.radio("Login via", ["Mobile Number", "Email"], key="admin_mode")
    input_value = st.text_input("Enter contact value", key="admin_contact")
    if st.button("Send OTP (Admin)", key="send_otp_admin"):
        send_otp(input_value, mode)
        st.session_state["admin_logged_in"] = True
    if st.session_state.get("admin_logged_in"):
        admin_dashboard()

def admin_dashboard():
    st.header("Admin Dashboard")

    # 1. User registration (by admin)
    st.subheader("Register New User")
    first_name = st.text_input("First Name (Admin)", key="reg_first_name_admin")
    last_name = st.text_input("Last Name (Admin)", key="reg_last_name_admin")
    age = st.number_input("Age (Admin)", min_value=1, max_value=120, key="reg_age_admin")
    if st.button("Create User", key="create_user_admin"):
        db.users.insert_one({"first_name": first_name, "last_name": last_name, "age": age, "created_by": "admin"})
        st.success("User created!")
    
    # 2. Product management
    st.subheader("Manage Products")
    col1, col2 = st.columns(2)
    with col1:
        prod_name = st.text_input("Flavour/Product Name", key="admin_prod_name")
        price = st.number_input("Price (₹)", min_value=1, key="admin_prod_price")
        qty = st.number_input("Total Qty", min_value=1, key="admin_prod_qty")
        if st.button("Add Product", key="add_product_admin"):
            db.products.insert_one({"name": prod_name, "price": price, "total_qty": qty, "remaining_qty": qty, "daily_sale": 0, "likes": 0, "added_on": datetime.now()})
            st.success("Product added!")

    with col2:
        remove_prod = st.text_input("Product name to remove", key="admin_remove_prod")
        if st.button("Remove Product", key="remove_product_admin"):
            db.products.delete_one({"name": remove_prod})
            st.warning("Product removed!")
    
    # 3. Product analytics
    st.subheader("Product Analytics")
    products = list(db.products.find())
    if products:
        fav_sell = max(products, key=lambda x: x.get("daily_sale", 0))
        fav_like = max(products, key=lambda x: x.get("likes", 0))
        st.markdown(
            f"**Most Sold:** {fav_sell['name']} ({fav_sell['daily_sale']} sold) :star:  \n"
            f"**Most Liked:** {fav_like['name']} ({fav_like['likes']} likes) :heart:"
        )
        for idx, p in enumerate(products):
            st.write(
                f"Flavor: {p['name']} | Total Qty: {p['total_qty']} | Remaining: {p['remaining_qty']} | Price: ₹{p['price']} "
                f"| Daily Sale: {p['daily_sale']} | {'🔥' if p['name'] == fav_sell['name'] else ''}{'❤️' if p['name'] == fav_like['name'] else ''}"
            )
            # Discount suggestion
            if p["daily_sale"] == 0:
                st.info(f"📉 Suggest Discount on {p['name']}")
    else:
        st.info("No products found.")

# User registration & login
def user_login():
    st.header("User Registration/Login")
    mode = st.radio("Login/Register via", ["Mobile Number", "Email"], key="user_mode")
    input_value = st.text_input("Enter contact value (User)", key="user_contact")
    if st.button("Send OTP (User)", key="send_otp_user"):
        send_otp(input_value, mode)
        st.session_state["user_logged_in"] = True
    
    # Only if logged in
    if st.session_state.get("user_logged_in"):
        user_dashboard(input_value)

def user_dashboard(user_contact):
    st.subheader("Your Details")
    if not db.users.find_one({"contact": user_contact}):
        # Registration
        first_name = st.text_input("First Name", key="user_first_name")
        last_name = st.text_input("Last Name", key="user_last_name")
        age = st.number_input("Age", min_value=1, max_value=120, key="user_age")
        location = st.text_input("Location", key="user_location")
        if st.button("Register", key="user_register"):
            db.users.insert_one({
                "contact": user_contact, "first_name": first_name,
                "last_name": last_name, "age": age, "location": location
            })
            st.success("Registered!")
    else:
        st.success("Logged in successfully!")

    # Product catalog
    st.subheader("Products")
    products = list(db.products.find())
    cart, wishlist = [], []
    for idx, p in enumerate(products):
        pname_key = p['name'].replace(" ", "_")
        st.write(
            f"{p['name']} | Price: ₹{p['price']} | Remaining: {p['remaining_qty']}"
        )
        if st.button(f"Add {p['name']} to Cart", key=f"cart_{pname_key}_{idx}"):
            cart.append(p["name"])
        if st.button(f"Add {p['name']} to Wishlist", key=f"wishlist_{pname_key}_{idx}"):
            wishlist.append(p["name"])
        rating = st.slider(f"Rate {p['name']}", 1, 5, 3, key=f"rate_{pname_key}_{idx}")
        feedback = st.text_input(f"Feedback for {p['name']}", key=f"feed_{pname_key}_{idx}")
        if st.button(f"Submit Feedback for {p['name']}", key=f"feedback_{pname_key}_{idx}"):
            db.feedback.insert_one({
                "user": user_contact,
                "product": p["name"],
                "rating": rating,
                "text": feedback,
                "date": datetime.now()
            })
            db.products.update_one({"name": p["name"]}, {"$inc": {"likes": 1}})
            st.success("Feedback submitted.")

        # Discount highlight
        if p.get("daily_sale", 0) == 0:
            st.info(f"Discount available on {p['name']}!")

    # Cart and Wishlist display
    st.subheader("Cart")
    st.write(cart)
    st.subheader("Wishlist")
    st.write(wishlist)

    # Invoice
    if st.button("Place Order", key="user_place_order"):
        order_id = db.orders.insert_one({
            "user": user_contact,
            "cart": cart,
            "timestamp": datetime.now(),
            "payment": "Pending"
        }).inserted_id

        st.success("Order placed successfully!")
        st.write("---")
        st.write(f"Invoice ID: {order_id}")
        st.write(f"Payment method: (Online/Offline)")
        st.write("Thanks for choosing Royal Ice Cream and visit again!")

if __name__ == "__main__":
    main()
