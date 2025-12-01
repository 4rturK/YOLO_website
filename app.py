from flask import Flask, render_template, request, send_from_directory
import os
from PIL import Image
from ultralytics import YOLO
import uuid

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = YOLO('yolov8n.pt') 

@app.route('/', methods=['GET', 'POST'])
def index():
    uploaded_image = None
    processed_image = None
    detections = []

    if request.method == 'POST':
        file = request.files.get('image')

        if file and file.filename != '':
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(img_path)

            uploaded_image = unique_filename

            # --------------------------
            # Analiza YOLO
            # --------------------------
            results = model(img_path, conf=0.25) 

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
                    "confidence": round(confidence * 100, 2)
                })

    return render_template(
        "index.html", 
        uploaded_image=uploaded_image, 
        processed_image=processed_image,
        detections=detections
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)