import streamlit as st
import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('railway_system.db')
c = conn.cursor()

# Session state variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

# Create necessary database tables if they don't exist
def create_DB_if_Not_available():
    """Creates necessary database tables if they don't exist."""
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS trains
                 (train_number TEXT PRIMARY KEY, train_name TEXT, departure_date TEXT, starting_destination TEXT, ending_destination TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS seats
                 (train_number TEXT, seat_number INTEGER, seat_type TEXT, booked INTEGER, passenger_name TEXT, passenger_age INTEGER, passenger_gender TEXT, 
                  FOREIGN KEY (train_number) REFERENCES trains(train_number))''')

create_DB_if_Not_available()

# Sign Up function
def signup(username, password, role):
    """Allows users to sign up with a username, password, and role."""
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        st.sidebar.error("Username already exists. Please try a different one.")
    else:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        st.sidebar.success("Sign up successful! You can log in now.")

# Login function
def login(username, password):
    """Allows users to log in by verifying credentials."""
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    if result:
        st.session_state['logged_in'] = True
        st.session_state['user_role'] = result[2]  # Assign role to session state
        st.sidebar.success("Login successful!")
    else:
        st.sidebar.error("Invalid username or password.")

# Logout function
def logout():
    """Logs out the user and resets session state."""
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.sidebar.success("Logged out successfully.")

# Train-related functions
def add_train(train_number, train_name, departure_date, starting_destination, ending_destination):
    """Adds a new train to the database."""
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, starting_destination, ending_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, starting_destination, ending_destination))
    conn.commit()

def delete_train(train_number, departure_date):
    """Deletes a train from the database."""
    c.execute("DELETE FROM trains WHERE train_number = ? AND departure_date = ?", (train_number, departure_date))
    conn.commit()

def book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    """Books a ticket for a passenger on a train."""
    seat_query = c.execute(f"SELECT seat_number FROM seats WHERE train_number = ? AND seat_type = ? AND booked = 0 LIMIT 1", (train_number, seat_type))
    seat = seat_query.fetchone()

    if seat:
        seat_number = seat[0]
        c.execute(f"UPDATE seats SET booked = 1, passenger_name = ?, passenger_age = ?, passenger_gender = ? WHERE train_number = ? AND seat_number = ?",
                  (passenger_name, passenger_age, passenger_gender, train_number, seat_number))
        conn.commit()
        st.success(f"Seat {seat_number} booked successfully for {passenger_name}.")
    else:
        st.error("No available seats for booking.")

def cancel_ticket(train_number, seat_number):
    """Cancels a booked ticket."""
    c.execute(f"UPDATE seats SET booked = 0, passenger_name = NULL, passenger_age = NULL, passenger_gender = NULL WHERE train_number = ? AND seat_number = ?", 
              (train_number, seat_number))
    conn.commit()
    st.success(f"Seat {seat_number} cancelled successfully.")

def view_seats(train_number):
    """Displays all seats for a train."""
    seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats WHERE train_number = ?", (train_number,))
    seats = seat_query.fetchall()
    
    if seats:
        df = pd.DataFrame(seats, columns=["Seat Number", "Seat Type", "Booked", "Passenger Name", "Passenger Age", "Passenger Gender"])
        st.dataframe(df)
    else:
        st.error("No seats available for this train.")

# Train administration functions (only for admin)
def train_functions():
    """Displays train-related functionalities based on user role."""
    st.title("Train Administration" if st.session_state['user_role'] == 'admin' else "Ticket Booking")

    if st.session_state['user_role'] == "admin":
        functions = st.sidebar.selectbox("Admin Functions", ["Add Train", "Delete Train", "View Seats"])

        if functions == "Add Train":
            st.header("Add a New Train")
            train_number = st.text_input("Train Number")
            train_name = st.text_input("Train Name")
            departure_date = st.date_input("Departure Date")
            starting_destination = st.text_input("Starting Destination")
            ending_destination = st.text_input("Ending Destination")
            if st.button("Add Train"):
                if train_number and train_name and starting_destination and ending_destination:
                    add_train(train_number, train_name, departure_date, starting_destination, ending_destination)
                    st.success(f"Train {train_name} added successfully!")
                else:
                    st.error("Please fill all fields to add a train.")
        
        elif functions == "Delete Train":
            st.header("Delete a Train")
            train_number = st.text_input("Enter Train Number to Delete")
            departure_date = st.date_input("Departure Date")
            if st.button("Delete Train"):
                delete_train(train_number, departure_date)
                st.success(f"Train {train_number} deleted successfully.")

        elif functions == "View Seats":
            st.header("View Seats for a Train")
            train_number = st.text_input("Enter Train Number")
            if st.button("View Seats"):
                view_seats(train_number)

    else:
        functions = st.sidebar.selectbox("Customer Functions", ["Book Ticket", "Cancel Ticket", "View Seats"])
        
        if functions == "Book Ticket":
            st.header("Book a Ticket")
            train_number = st.text_input("Enter Train Number")
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.number_input("Passenger Age", min_value=1)
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.selectbox("Seat Type", ["Aisle", "Middle", "Window"])
            if st.button("Book Ticket"):
                book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif functions == "Cancel Ticket":
            st.header("Cancel a Ticket")
            train_number = st.text_input("Enter Train Number")
            seat_number = st.number_input("Enter Seat Number", min_value=1)
            if st.button("Cancel Ticket"):
                cancel_ticket(train_number, seat_number)

        elif functions == "View Seats":
            st.header("View Seats for a Train")
            train_number = st.text_input("Enter Train Number")
            if st.button("View Seats"):
                view_seats(train_number)

# Main app logic
if st.session_state['logged_in']:
    st.sidebar.title(f"Logged in as {st.session_state['user_role']}")
    if st.sidebar.button("Logout"):
        logout()
    train_functions()

else:
    st.sidebar.title("Login or Sign Up")

    choice = st.sidebar.selectbox("Choose Action", ["Login", "Sign Up"])
    
    if choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            login(username, password)

    elif choice == "Sign Up":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        role = st.sidebar.selectbox("Role", ["customer", "admin"])
        if st.sidebar.button("Sign Up"):
            signup(username, password, role)

# Close the database connection at the end of the session
conn.close()

