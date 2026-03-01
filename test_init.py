try:
    print("Importing create_app...")
    from app import create_app
    print("Calling create_app...")
    app = create_app()
    print("App created successfully.")
    with app.app_context():
        print("Checking DB...")
        from app.models import Event
        count = Event.query.count()
        print(f"Event count: {count}")
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
