from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = "farzan"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello MVP"})


if __name__ == "__main__":
    app.run(debug=True)
