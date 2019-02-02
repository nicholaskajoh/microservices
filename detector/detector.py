import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import cv2
import numpy as np
import cloudinary
from cloudinary.uploader import upload
from collections import Counter
import urllib.request


# load env vars
# APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# load_dotenv(os.path.join(APP_ROOT, '.env'))
# create Flask app
app = Flask(__name__)


# error handling
class BadRequest(Exception):
    def __init__(self, message, status=400, errors=None):
        self.message = message
        self.status = status
        self.errors = errors

@app.errorhandler(BadRequest)
def handle_bad_request(ex):
    payload = {
        'message': ex.message,
    }
    if ex.errors:
        payload['errors'] = ex.errors
    return jsonify(payload), ex.status


# detect objects, draw bounding boxes, save new image and return image url and predictions
@app.route('/', methods=['POST'])
def index():
    # get image
    data = request.get_json()
    if 'image_url' not in data:
        raise BadRequest('Image url is required!', status=403)
    image_url = data['image_url']
    image_response = urllib.request.urlopen(image_url)
    image_array = np.asarray(bytearray(image_response.read()), dtype='uint8')
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # get object classes
    classes = None
    with open('classes.txt', 'r') as classes_file:
        classes = [line.strip() for line in classes_file.readlines()]

    # assign a random but unique colour to each class 
    colours = np.random.uniform(0, 255, size=(len(classes), 3))
    
    # create a YOLO v3 DNN model using pre-trained weights
    net = cv2.dnn.readNet('yolov3.weights', 'yolov3.cfg')
    
    # create image blog
    scale = 0.00392
    image_blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    # detect objects
    net.setInput(image_blob)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                width = image.shape[1]
                height = image.shape[0]
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # draw bounding boxes on detected objects
    def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
        label = str(classes[class_id])
        colour = colours[class_id]
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colour, 3)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_DUPLEX, 1, colour, 2)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))
    
    output_image_path = '.tmp/output-image.jpg'
    cv2.imwrite(output_image_path, image)

    # upload image to Cloudinary
    cloudinary.config(
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key = os.getenv('CLOUDINARY_API_KEY'),
        api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    )
    image_meta = upload(output_image_path, folder='detector_svc_images')

    # get detected objects
    detected_objects = []
    for class_id in class_ids:
        detected_objects.append(classes[class_id])
    detected_objs_and_freqs = Counter(detected_objects)
    
    return jsonify({
        'url': image_meta['url'],
        'objects': detected_objs_and_freqs,
    })