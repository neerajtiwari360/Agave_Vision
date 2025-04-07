from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML templates as strings
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Flask UI Sample</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container mt-5">
    <h1 class="mb-4">Welcome to Flask UI Sample</h1>
    <form method="POST" action="/submit">
        <div class="mb-3">
            <label for="name" class="form-label">Enter your name:</label>
            <input type="text" class="form-control" id="name" name="name" required>
        </div>
        <button type="submit" class="btn btn-primary">Submit</button>
    </form>
</div>
</body>
</html>
"""

result_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Submission Result</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container mt-5">
    <h2 class="mb-3">Thank you!</h2>
    <p class="lead">Hello, <strong>{{ name }}</strong>. Your form was submitted successfully.</p>
    <a href="/" class="btn btn-secondary mt-3">Go Back</a>
</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    return render_template_string(result_html, name=name)

if __name__ == '__main__':
    app.run(debug=True)
