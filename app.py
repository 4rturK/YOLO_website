from flask import Flask, render_template, request, send_from_directory
import os
from PIL import Image

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    uploaded_image = None

    if request.method == 'POST':
        file = request.files.get('image')

        if file:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded.jpg')
            file.save(img_path)

            uploaded_image = img_path.replace("static/", "")

            # --------------------------
            # YOLO
            # --------------------------

    return render_template("index.html", uploaded_image=uploaded_image)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
