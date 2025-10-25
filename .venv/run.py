from back import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=20000, debug=True)
