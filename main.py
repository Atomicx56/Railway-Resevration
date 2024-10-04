import streamlit as st
import sqlite3
import pandas as pd

# Initialize database connection
conn = sqlite3.connect('railway_system.db')
c = conn.cursor()

# Create required tables if not available
def create_DB_if_Not_available():
    """Creates necessary database tables if they don't exist."""
    c.execute('''CREATE TABLE IF NOT EXISTS users
               (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trains
               (train_number TEXT PRIMARY KEY, train_name TEXT, departure_date TEXT, starting_destination TEXT, ending_destination TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS seats
               (train_number TEXT, seat_number INTEGER, seat_type TEXT, booked INTEGER, passenger_name TEXT, passenger_age INTEGER, passenger_gender TEXT, FOREIGN KEY (train_number) REFERENCES trains(train_number))''')
    conn.commit()

# Function to add new train
def add_train(train_number, train_name, departure_date, starting_destination, ending_destination):
    """Adds a new train to the database."""
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, starting_destination, ending_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, starting_destination, ending_destination))
    conn.commit()

# Function to create seat table for a train
def create_seat_table(train_number):
    """Creates a seat table for a specific train."""
    for i in range(1, 51):
        seat_type = categorize_seat(i)
        c.execute(f'''INSERT INTO seats (train_number, seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?,?,?,?,?,?,?)''',
                  (train_number, i, seat_type, 0, "", "", ""))
    conn.commit()

# Function to categorize seat
def categorize_seat(seat_number):
    """Categorizes a seat based on its number."""
    if (seat_number % 10) in [0, 4, 5, 9]:
        return "Window"
    elif (seat_number % 10) in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"

# Function to allocate the next available seat of a given type
def allocate_next_available_seat(train_number, seat_type):
    """Allocates the next available seat of a given type for a train."""
    seat_query = c.execute(
        f"SELECT seat_number FROM seats WHERE train_number = ? AND booked=0 and seat_type=? ORDER BY seat_number ASC", (train_number, seat_type))
    result = seat_query.fetchone()
    return result[0] if result else None

# Function to book a ticket
def book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    """Books a ticket for a passenger on a train."""
    seat_number = allocate_next_available_seat(train_number, seat_type)
    if seat_number:
        c.execute(f"UPDATE seats SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE train_number=? AND seat_number=?", (
            passenger_name, passenger_age, passenger_gender, train_number, seat_number))
        conn.commit()
        st.success(f"Successfully booked seat {seat_number} ({seat_type}) for {passenger_name}.")
    else:
        st.error("No available seats for booking.")

# Function to cancel ticket
def cancel_ticket(train_number, seat_number):
    """Cancels a ticket for a specific seat on a train."""
    c.execute(f"UPDATE seats SET booked=0, passenger_name='', passenger_age='', passenger_gender='' WHERE train_number=? AND seat_number=?", (train_number, seat_number))
    conn.commit()
    st.success(f"Successfully canceled seat {seat_number} on train {train_number}.")

# Function to search train by train number
def search_train_by_train_number(train_number):
    """Searches for a train by its train number."""
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    return train_query.fetchone()

# Function to view seats
def view_seats(train_number):
    """Views the seats and their availability for a given train."""
    seat_query = c.execute(
        f'''SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats WHERE train_number = ? ORDER BY seat_number ASC''',
        (train_number,))
    result = seat_query.fetchall()
    if result:
        seat_data = pd.DataFrame(result, columns=['Seat Number', 'Seat Type', 'Booked', 'Passenger Name', 'Passenger Age', 'Passenger Gender'])
        st.dataframe(seat_data)
    else:
        st.error(f"No seats found for train {train_number}.")

# Signup function
def signup(username, password, role):
    """Signs up a new user to the system."""
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        st.success("Successfully signed up!")
    except sqlite3.Error as e:
        st.error(f"Error signing up user: {e}")

# Login function
def login(username, password):
    """Logs in a user."""
    user_query = c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return user_query.fetchone()

# Logout function
def logout():
    """Logs the user out and clears the session."""
    st.session_state['user'] = None
    st.session_state['role'] = None
    st.sidebar.success("You have been logged out.")

# Customer panel
def enhanced_customer_options():
    """Improved customer panel options."""
    st.header("Customer Panel")
    customer_choice = st.selectbox("Customer Options", ["Book Ticket", "Cancel Ticket", "View Trains", "Logout"])
    if customer_choice == "Book Ticket":
        book_ticket_ui()
    elif customer_choice == "Cancel Ticket":
        cancel_ticket_ui()
    elif customer_choice == "View Trains":
        view_trains()
    elif customer_choice == "Logout":
        logout()

# Function to book ticket UI
def book_ticket_ui():
    """UI for booking a ticket."""
    st.header("Book Ticket")
    train_number = st.text_input("Train Number")
    passenger_name = st.text_input("Passenger Name")
    passenger_age = st.number_input("Passenger Age", min_value=0)
    passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
    seat_type = st.selectbox("Seat Type", ["Window", "Aisle", "Middle"])
    
    if st.button("Book Ticket"):
        book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

# Function to cancel ticket UI
def cancel_ticket_ui():
    """UI for canceling a ticket."""
    st.header("Cancel Ticket")
    train_number = st.text_input("Train Number")
    seat_number = st.number_input("Seat Number", min_value=1)
    
    if st.button("Cancel Ticket"):
        cancel_ticket(train_number, seat_number)

# View all trains function
def view_trains():
    """Displays all available trains."""
    train_data = pd.read_sql_query("SELECT * FROM trains", conn)
    st.dataframe(train_data)

# Admin panel
def admin_options():
    """Admin panel for managing trains."""
    st.header("Admin Panel")
    admin_choice = st.selectbox("Admin Options", ["Add Train", "Delete Train", "View Trains", "Logout"])
    if admin_choice == "Add Train":
        with st.form("add_train_form"):
            train_number = st.text_input("Train Number")
            train_name = st.text_input("Train Name")
            departure_date = st.date_input("Departure Date")
            starting_destination = st.text_input("Starting Destination")
            ending_destination = st.text_input("Ending Destination")
            submitted = st.form_submit_button("Add Train")
            if submitted:
                add_train(train_number, train_name, departure_date, starting_destination, ending_destination)
                create_seat_table(train_number)
                st.success("Train added successfully!")
    elif admin_choice == "Delete Train":
        train_number = st.text_input("Enter Train Number to Delete:")
        if st.button("Delete Train"):
            c.execute("DELETE FROM trains WHERE train_number = ?", (train_number,))
            c.execute("DELETE FROM seats WHERE train_number = ?", (train_number,))
            conn.commit()
            st.success(f"Train {train_number} deleted successfully.")
    elif admin_choice == "View Trains":
        view_trains()
    elif admin_choice == "Logout":
        logout()

# Main function
def main():
    """Main app function with enhanced UI and logout support."""
    st.title("Railway Reservation System")

    choice = st.sidebar.selectbox("Login/Signup", ["Login", "Sign Up"])

    if "user" not in st.session_state:
        st.session_state['user'] = None
        st.session_state['role'] = None

    if choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user_data = login(username, password)
            if user_data:
                st.session_state['user'] = username
                st.session_state['role'] = user_data[2]  # Role (customer or admin)
                st.sidebar.success(f"Logged in as {username}")
            else:
                st.sidebar.error("Invalid credentials. Please try again.")
    elif choice == "Sign Up":
                username = st.sidebar.text_input("Username")
                password = st.sidebar.text_input("Password", type="password")
                role = st.sidebar.selectbox("Role", ["customer", "admin"])
        if st.sidebar.button("Sign Up"):
            signup(username, password, role)

    if st.session_state['user']:
        st.sidebar.title(f"Logged in as {st.session_state['user']}")
        st.sidebar.button("Logout", on_click=logout)
        if st.session_state['role'] == "admin":
            admin_options()
        else:
            enhanced_customer_options()

if __name__ == "__main__":
    create_DB_if_Not_available()
    main()

# Close the connection after all operations are done
conn.close()

      
