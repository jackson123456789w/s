from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Welcome to My Flask App</h1><p>This is the homepage.</p>"

@app.route('/about')
def about():
    return "<h2>About Page</h2><p>This is a simple Flask application.</p>"

if __name__ == '__main__':
    app.run(debug=True)
