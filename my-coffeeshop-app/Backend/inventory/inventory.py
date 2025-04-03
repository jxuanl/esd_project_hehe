from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
from datetime import datetime, timedelta
from flasgger import Swagger
from sqlalchemy import desc

app = Flask(__name__)
CORS(app)
Swagger(app)  # Enable Swagger UI

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Inventory(db.Model):
    __tablename__ = 'inventory'

    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ingredient = db.Column(db.String(64), nullable=False)
    available_quantity = db.Column(db.Float(precision=2), nullable=False)
    unit = db.Column(db.String(32), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    change_in_quantity = db.Column(db.Float(precision=2), default=0.0)

    def __init__(self, ingredient, available_quantity, unit, change_in_quantity=0.0):
        self.ingredient = ingredient
        self.available_quantity = available_quantity
        self.unit = unit
        self.date_time = datetime.utcnow()
        self.change_in_quantity = change_in_quantity

    def json(self):
          return {
              "inventory_id": self.inventory_id,
              "ingredient": self.ingredient,
              "available_quantity": self.available_quantity,
              "unit": self.unit,
              "date_time": self.date_time.strftime('%Y-%m-%d %H:%M:%S'),
              "change_in_quantity": self.change_in_quantity
          }
    
    def json_change_only(self):
        return {
            "ingredient": self.ingredient,
            "change_in_quantity": self.change_in_quantity,
            "date_time": self.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            "unit": self.unit
        }


@app.route("/inventory", methods=["GET"])
def get_all_items():
    """
    Get all inventory items
    ---
    responses:
      200:
        description: A list of inventory items
      404:
        description: No inventory items found
    """
    item_list = db.session.scalars(db.select(Inventory)).all()
    if item_list:
        return jsonify({
            "code": 200,
            "data": {
                "inventory": [item.json() for item in item_list]
            }
        })
    return jsonify({"code": 404, "message": "No inventory items found."}), 404

@app.route("/inventory/<int:inventory_id>", methods=["GET"])
def get_item_by_id(inventory_id):
    """
    Get an inventory item by ID
    ---
    parameters:
      - in: path
        name: inventory_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Item found
      404:
        description: Inventory item not found
    """
    item = db.session.scalar(db.select(Inventory).filter_by(inventory_id=inventory_id))
    if item:
        return jsonify({"code": 200, "data": item.json()})
    return jsonify({"code": 404, "message": "Inventory item not found."}), 404

@app.route("/inventory/ingredient/<string:ingredient>", methods=["GET"])
def get_inventory_by_ingredient(ingredient):
    """
    Get an inventory item by ingredient name
    ---
    parameters:
      - in: path
        name: ingredient
        required: true
        schema:
          type: string
    responses:
      200:
        description: A list of inventory records for the given ingredient
      404:
        description: Inventory records for that ingredient not found
    """
    items = db.session.execute(db.select(Inventory).filter_by(ingredient=ingredient)).scalars().all()
    if items:
        inventory_list = [item.json() for item in items]
        return jsonify({"code": 200, "data": {"inventory": inventory_list}})
    return jsonify({"code": 404, "message": f"Inventory records for ingredient '{ingredient}' not found."}), 404

@app.route("/inventory/ingredient/<string:ingredient>/available_quantity", methods=["GET"])
def get_ingredient_available_quantity(ingredient):
    """
    Get the latest available quantity for a specific ingredient.
    ---
    parameters:
      - in: path
        name: ingredient
        required: true
        schema:
          type: string
    responses:
      200:
        description: The latest available quantity of the ingredient.
      404:
        description: No inventory records found for that ingredient.
    """
    latest_record = db.session.scalar(
        db.select(Inventory)
        .filter_by(ingredient=ingredient)
        .order_by(desc(Inventory.date_time))
    )

    if latest_record:
        return jsonify({
            "code": 200,
            "data": {
                "ingredient": latest_record.ingredient,
                "available_quantity": latest_record.available_quantity,
                "unit": latest_record.unit,
                "date_time": latest_record.date_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return jsonify({"code": 404, "message": f"No inventory records found for ingredient '{ingredient}'."}), 404

@app.route("/inventory/ingredient/<string:ingredient>/change_in_quantity", methods=["GET"])
def get_ingredient_changes(ingredient):
    """
    Get change in quantities for an ingredient for the past 7 days
    ---
    parameters:
      - in: path
        name: ingredient
        required: true
        schema:
          type: string
    responses:
      200:
        description: List of change in quantities
      404:
        description: Ingredient not found or no history
    """
    time_period = datetime.utcnow() - timedelta(days=7)
    history = db.session.scalars(db.select(Inventory).filter_by(ingredient=ingredient).filter(Inventory.date_time >= time_period)).all()

    if history:
        history_list = [item.json_change_only() for item in history]
        return jsonify({"code": 200, "data": history_list})
    return jsonify({"code": 404, "message": f"No history found for ingredient '{ingredient}' in the past 7 days."}), 404


@app.route("/inventory", methods=["POST"])
def create_item():
    """
    Create a new inventory item
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ingredient
              - available_quantity
              - unit
            properties:
              ingredient:
                type: string
              available_quantity:
                type: number
              unit:
                type: string
              change_in_quantity:
                type: number
    responses:
      201:
        description: Item created
      400:
        description: Missing fields
      500:
        description: Server error
    """
    data = request.get_json()
    required = ['ingredient', 'available_quantity', 'unit']
    if not all(key in data for key in required):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    change = data.get('change_in_quantity', data['available_quantity'])

    item = Inventory(
        ingredient=data['ingredient'],
        available_quantity=data['available_quantity'],
        unit=data['unit'],
        change_in_quantity=change
    )
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "An error occurred creating the item.", "error": str(e)}), 500

    return jsonify({"code": 201, "data": item.json()}), 201

@app.route("/inventory/<int:inventory_id>", methods=["DELETE"])
def delete_item(inventory_id):
    """
    Delete an inventory item
    ---
    parameters:
      - in: path
        name: inventory_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Item deleted
      404:
        description: Item not found
      500:
        description: Failed to delete item
    """
    item = db.session.scalar(db.select(Inventory).filter_by(inventory_id=inventory_id))
    if not item:
        return jsonify({"code": 404, "message": "Item not found."}), 404

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "Failed to delete item.", "error": str(e)}), 500

    return jsonify({"code": 200, "message": "Item deleted successfully."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)