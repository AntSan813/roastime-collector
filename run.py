from roastprofiler.app import app

url = "http://127.0.0.1:5077"

if __name__ == "__main__":
    import threading
    import webbrowser
    import sys

    def open_browser():
        webbrowser.open(url)

    def run_app():
        # Set debug=False and use_reloader=False to prevent the reloader from causing issues
        app.run(debug=False, use_reloader=False, port=5077)

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_app)
    flask_thread.daemon = (
        True  # This ensures the thread will exit when the main program exits
    )
    flask_thread.start()

    # Open the browser after a short delay
    threading.Timer(1, open_browser).start()

    # Keep the main thread alive (blocking, not spinning) until interrupted.
    try:
        while flask_thread.is_alive():
            flask_thread.join(timeout=1)
    except KeyboardInterrupt:
        print("Application interrupted by user.")
        sys.exit(0)
