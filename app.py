from flask import Flask, render_template, request, send_from_directory
import os
from PIL import Image
from ultralytics import YOLO
import uuid
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

app.secret_key = 'Coockies_key'
# Konfiguracja folderów
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Załadowanie modelu YOLO
model = YOLO('yolov8n.pt') 

# Definicja kategorii (ID zgodne ze zbiorem COCO)
CATEGORIES = {
    "Pojazdy": [1, 2, 3, 4, 5, 6, 7, 8],
    "Zwierzęta": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "Jedzenie": [46, 47, 48, 49, 50, 51, 52, 53, 54, 55],
    "Ludzie": [0],
    "Przedmioty domowe": [39, 41, 42, 43, 44, 45, 56, 57, 58, 59, 60, 61, 62],
    "Elektronika": [62, 63, 64, 65, 66, 67, 73]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    uploaded_image = None
    processed_image = None
    detections = []
    
    # Pobieramy nazwy wszystkich klas z modelu
    all_classes = model.names 

    sorted_classes = sorted(all_classes.items(), key=lambda x: x[1].lower())

    if request.method == 'POST':
        file = request.files.get('image')

        if not file or file.filename == '':
            flash('Błąd: Nie wybrano pliku!')
            return redirect(url_for('index'))

        if not allowed_file(file.filename):
            flash(f'Błąd: Niedozwolony format pliku! Dozwolone to: {", ".join(ALLOWED_EXTENSIONS)}')
            return redirect(url_for('index'))
        selected_class_ids = request.form.getlist('classes')

        if file and file.filename != '':
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(img_path)
            uploaded_image = unique_filename

            classes_to_detect = [int(cls_id) for cls_id in selected_class_ids] if selected_class_ids else None

            results = model(img_path, conf=0.25, classes=classes_to_detect) 
            result = results[0]

            im_array = result.plot() 
            im = Image.fromarray(im_array[..., ::-1])
            
            processed_filename = f"pred_{unique_filename}"
            processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            im.save(processed_path)
            processed_image = processed_filename

            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                detections.append({
                    "name": class_name,
                    "class_id": class_id,
                    "confidence": round(confidence * 100, 2),
                    "box": box.xyxyn[0].tolist()
                })

    return render_template(
        "index.html", 
        uploaded_image=uploaded_image, 
        processed_image=processed_image,
        detections=detections,
        all_classes=all_classes,
        sorted_classes=sorted_classes,
        categories=CATEGORIES
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)