from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# MySQL Configuration using environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

# Initialize DB
db = SQLAlchemy(app)

# Define Customisation Model
class Customisation(db.Model):
    __tablename__ = 'customisation'

    customisation_id = db.Column(db.Integer, primary_key=True)
    customisation_type = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    price_diff = db.Column(db.Float, nullable=False)

    def json(self):
        return {
            "customisation_id": self.customisation_id,
            "customisation_type": self.customisation_type,
            "name": self.name,
            "price_diff": self.price_diff
        }

@app.route('/')
def home():
    return jsonify({"message": "Drink Customisation microservice is running!"}), 200

@app.route('/customisations', methods=['GET'])
@app.route('/customisations/<int:customisation_id>', methods=['GET'])
def get_customisations(customisation_id=None):
    if customisation_id:
        customisation = Customisation.query.get(customisation_id)
        if customisation:
            return jsonify(customisation.json()), 200
        return jsonify({"message": "Customisation not found"}), 404

    customisations = Customisation.query.all()
    return jsonify([c.json() for c in customisations]), 200

@app.route('/customisations/type/<string:customisation_type>', methods=['GET'])
def get_customisations_by_type(customisation_type):
    customisations = Customisation.query.filter_by(customisation_type=customisation_type).all()
    if customisations:
        return jsonify([c.json() for c in customisations]), 200
    return jsonify({"message": "No customisations found for this type"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
