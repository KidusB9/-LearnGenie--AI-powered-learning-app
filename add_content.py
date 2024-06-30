from app import app, db, Content

def add_content(title, description, content):
    new_content = Content(title=title, description=description, content=content)
    db.session.add(new_content)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # Add your content here
        title = "Example Title"
        description = "Example Description"
        content = "This is an example content for the learning platform."

        add_content(title, description, content)
        print("Content added successfully!")
