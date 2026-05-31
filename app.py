# ============================================================================
# FLASK TODO APP - Main Application File
# ============================================================================
# This is the main entry point for our Flask application. It sets up:
# - Flask application instance
# - SQLite database connection and initialization
# - All route handlers (URL endpoints)
# - Database models via SQLAlchemy ORM
#
# Learning Note: Flask is a lightweight web framework. Routes map URLs to
# Python functions. Each function returns HTML that gets sent to the browser.
# ============================================================================

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================
# Create a Flask application instance. The __name__ variable tells Flask
# where to look for templates and static files (same directory as this script)
app = Flask(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# SQLite is a lightweight, file-based database. Using sqlite:/// creates
# a file called 'todos.db' in the same directory as this script.
# Check_same_thread=False allows multiple threads to access the database
# (useful for development, should be True in production)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress unnecessary warnings

# Create SQLAlchemy database instance. This allows us to define models
# (database tables as Python classes) and interact with the database
db = SQLAlchemy(app)

# ============================================================================
# DATABASE MODELS
# ============================================================================
# A "model" is a Python class that represents a database table.
# Each attribute becomes a column in the table.
# SQLAlchemy handles converting Python code to SQL automatically.

class Todo(db.Model):
    """
    Todo Model - Represents a single todo item in the database
    
    Attributes:
        id (int): Primary key - unique identifier for each todo
        title (str): The text content of the todo
        description (str): Optional longer description
        completed (bool): Whether the todo is done (default: False)
        created_at (datetime): When the todo was created (auto-set)
        due_date (date): Optional due date for the todo
    
    Table name: 'todo' (auto-generated from class name, lowercased)
    """
    
    # Column definitions
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each todo
    title = db.Column(db.String(120), nullable=False)  # Title is required
    description = db.Column(db.Text, default='')  # Optional longer text
    completed = db.Column(db.Boolean, default=False)  # Track completion status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Auto timestamp
    due_date = db.Column(db.Date, nullable=True)  # Optional deadline
    
    def __repr__(self):
        """
        String representation of a Todo object.
        Useful for debugging - shows what's in memory without printing entire object
        """
        return f'<Todo {self.id}: {self.title}>'
    
    def to_dict(self):
        """
        Convert a Todo object to a dictionary.
        Useful for JSON responses and passing data to templates.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None
        }


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================
# This function creates all database tables if they don't already exist.
# It uses the 'app_context' because SQLAlchemy needs to know which Flask app
# instance to work with.

def init_db():
    """
    Initialize the database by creating all tables defined in our models.
    Called once when the app starts.
    """
    with app.app_context():
        db.create_all()
        print("✓ Database initialized - tables created")


# ============================================================================
# FLASK ROUTES (URL ENDPOINTS)
# ============================================================================
# Each @app.route() decorator maps a URL pattern to a function.
# When someone visits that URL, the function runs and returns a response.

@app.route('/')
def index():
    """
    Home page route - displays all todos
    
    URL: http://localhost:5000/
    Method: GET (fetching/viewing data)
    
    Process:
    1. Query the database for all Todo objects
    2. Render the 'index.html' template with the todos
    3. The template loops through todos and displays them as HTML
    """
    # Query all todos from database, ordered by most recent first
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    
    # Render the index.html template, passing the todos list
    # Jinja2 (the templating engine) will replace {{ variable }} with values
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
def add_todo():
    """
    Add a new todo to the database
    
    URL: http://localhost:5000/add
    Method: POST (sending/creating data)
    Form Fields Expected:
        - title: The todo title (required)
        - description: Optional longer description
    
    Process:
    1. Extract form data from the POST request
    2. Create a new Todo object with that data
    3. Add it to the database session
    4. Commit (save) to database
    5. Redirect back to home page to see the new todo
    """
    # Get form data from the POST request
    # request.form is a dictionary-like object containing form fields
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    
    # Simple validation - title is required
    if not title:
        # TODO: Add flash message for user feedback
        return redirect(url_for('index'))
    
    # Create a new Todo instance (this doesn't save to database yet)
    new_todo = Todo(title=title, description=description)
    
    # Add the new todo to the database session (queue it for saving)
    db.session.add(new_todo)
    
    # Commit the session - this executes the INSERT query
    db.session.commit()
    
    # Redirect to home page (shows the new todo in the list)
    return redirect(url_for('index'))


@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    """
    Toggle a todo's completion status (mark done/undone)
    
    URL: http://localhost:5000/toggle/1
    Method: POST
    URL Parameter:
        - todo_id: The ID of the todo to toggle
    
    Process:
    1. Find the todo by ID in the database
    2. Flip its completed status (True -> False or False -> True)
    3. Save the change
    4. Return JSON response (for AJAX requests from the browser)
    
    TODO: Add error handling for non-existent todos
    """
    # Query the database for a todo with the given ID
    # .get() returns the object or None if not found
    todo = db.session.get(Todo, todo_id)
    
    if not todo:
        # If todo doesn't exist, return error response
        return jsonify({'error': 'Todo not found'}), 404
    
    # Toggle the completed status (flip True/False)
    todo.completed = not todo.completed
    
    # Save the change to database
    db.session.commit()
    
    # Return JSON response with updated todo data
    # jsonify() converts Python dicts to JSON format
    return jsonify({
        'success': True,
        'todo': todo.to_dict()
    })


@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """
    Delete a todo from the database
    
    URL: http://localhost:5000/delete/1
    Method: POST
    URL Parameter:
        - todo_id: The ID of the todo to delete
    
    Process:
    1. Find the todo by ID
    2. Delete it from the database
    3. Redirect back to home page
    
    Safety Note: In a real app, you'd want user authentication and 
    verification to prevent accidental or malicious deletions.
    """
    # Find the todo to delete
    todo = Todo.query.get(todo_id)
    
    if not todo:
        return redirect(url_for('index'))
    
    # Remove (delete) the todo from the database session
    db.session.delete(todo)
    
    # Commit the deletion
    db.session.commit()
    
    # Redirect back to home page
    return redirect(url_for('index'))

#Edit
@app.route('/edit/<int:todo_id>', methods = ['GET', 'POST'])
def edit_todo(todo_id):
    todo = Todo.query.get(todo_id) #get todo from the database

    if not todo:
        return redirect(url_for('index')) # If todo doesn't exist, return home

    #get the todo from the POST
    if request.method == 'POST':
        #update todo in the database
        todo.title = request.form.get('title', '').strip() # returns '' if form doesn't exist
        todo.description = request.form.get('description', '').strip()

        if not todo.title:
            return redirect(url_for('edit_todo', todo_id=todo_id))
        
        #write to db
        db.session.commit()

        #redirect to homepage
        return redirect(url_for('index'))

    #handle GET request
    else:
        #render edit.html with the current data from the todo variable
        return render_template('edit.html', todo=todo)

@app.route('/api/todos')
def api_todos():
    """
    API endpoint - returns all todos as JSON
    
    URL: http://localhost:5000/api/todos
    Method: GET
    Response Format: JSON
    
    Useful for:
    - AJAX requests from JavaScript
    - Mobile app integration
    - Data export
    
    TODO: Add filtering options (completed, search, date range)
    """
    # Query all todos and convert each to a dictionary
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    
    # Return as JSON with proper content-type header
    return jsonify([todo.to_dict() for todo in todos])


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================
# This code only runs if this file is executed directly (not imported)

if __name__ == '__main__':
    # Initialize the database when app starts
    init_db()
    
    # Start the Flask development server
    # debug=True enables:
    #   - Auto-reload when code changes
    #   - Better error messages
    #   - Interactive debugger
    # host='0.0.0.0' allows access from other machines
    # port=5000 is the default Flask port
    app.run(debug=True, host='0.0.0.0', port=5000)
