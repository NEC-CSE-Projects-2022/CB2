import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from predict import preprocess_and_predict

# --- Flask App Setup ---
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- ROUTES ---
@app.route("/")
def home():
    return render_template("home.html", active="home")


@app.route("/about")
def about():
    return render_template("about.html", active="about")


@app.route("/methodology")
def methodology():
    return render_template("methodology.html", active="methodology")


@app.route("/upload")
def upload():
    return render_template("upload.html", active="upload")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    submitted = False
    if request.method == "POST":
        submitted = True
    return render_template("contact.html", active="contact", submitted=submitted)

#modhatidi
# --- PREDICT ROUTE ---
@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return render_template("upload.html", active="upload", error="No file uploaded")

    file = request.files["file"]

    if file.filename == "":
        return render_template("upload.html", active="upload", error="No selected file")

    if not allowed_file(file.filename):
        return render_template("upload.html", active="upload", error="Only CSV files allowed")

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Run ML Prediction
    try:
        results = preprocess_and_predict(filepath)
    except Exception as e:
        return render_template("upload.html", active="upload", error=str(e))

    return render_template("result.html", active="upload", results=results)




# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
