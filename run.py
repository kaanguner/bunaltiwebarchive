# run.py
from app import create_app # Import the factory function from app/__init__.py

# Create the app instance using the factory
app = create_app()

if __name__ == "__main__":
    # Run the Flask development server
    # host='0.0.0.0' makes it accessible within Codespaces network and externally if port forwarded
    # port=5000 is the default Flask port (can be changed)
    # debug=True enables interactive debugger and auto-reloading on code changes
    print("Starting Flask development server...")
    app.run(host='0.0.0.0', port=5000, debug=True)