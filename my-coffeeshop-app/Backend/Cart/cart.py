from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import select
from os import environ
from sqlalchemy.orm import clear_mappers



app = Flask(__name__)
CORS(app)

clear_mappers()
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cart'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}


db = SQLAlchemy(app)

class Cart(db.Model):
    __tablename__ = 'cart'


    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(45), nullable=False)
    outlet_id = db.Column(db.Integer, nullable=False)
    totalPrice = db.Column(db.Float(precision=2), nullable=False)


    def __init__(self, user_id, outlet_id, totalPrice):
        self.user_id = user_id
        self.outlet_id = outlet_id
        self.totalPrice = totalPrice


    def json(self):
        return {"cart_id": self.cart_id, "user_id": self.user_id, "outlet_id": self.outlet_id, "totalPrice": self.totalPrice}



@app.route("/cart")
def get_all():
    cartList = db.session.scalars(db.select(Cart)).all()


    if len(cartList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "carts": [cart.json() for cart in cartList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no carts."
        }
    ), 404



@app.route("/cart/<int:cart_id>")
def filter_byCartID(cart_id):
    cart = db.session.scalar(
    	db.select(Cart).filter_by(cart_id=cart_id)
)


    if cart:
        return jsonify(
            {
                "code": 200,
                "data": cart.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Cart not found."
        }
    ), 404


@app.route("/create_cart", methods=['POST'])
def create_cart():
    data = request.get_json()

    # Create a new Cart instance
    cart = Cart(**data)

    try:
        db.session.add(cart)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the cart.",
                "error": str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": cart.json()
        }
    ), 201

@app.route("/update_cart/<int:cart_id>", methods=['PUT'])
def update_order(cart_id):
    try:
        cart = db.session.scalar(db.select(Cart).filter_by(cart_id=cart_id))
        if not cart:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "cart_id": cart_id
                    },
                    "message": "Cart not found."
                }
            ), 404

        # update status
        data = request.get_json()
        if data['totalPrice']:
            cart.totalPrice = data['totalPrice']
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": cart.json()
                }
            ), 200
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "cart_id": cart_id
                },
                "message": "An error occurred while updating the cart. " + str(e)
            }
        ), 500
    

@app.route("/delete_cart/<int:cart_id>", methods=["DELETE"])
def delete_by_cartId(cart_id):
    # Find the cart by cartId
    cart = db.session.scalar(
        db.select(Cart).filter_by(cart_id=cart_id)
    )

    if cart:
        # If the cart exists, delete it
        db.session.delete(cart)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "Cart deleted successfully."
            }
        )
    else:
        # If the cart does not exist, return a 404 error
        return jsonify(
            {
                "code": 404,
                "message": "Cart not found."
            }
        ), 404   



#####################################################################################################################
class Cart_Items(db.Model):
    __tablename__ = 'cart_items'


    cart_items_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id_fk = db.Column(db.Integer, nullable=False)
    drink_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


    def __init__(self, cart_id_fk, drink_id, quantity):
        self.cart_id_fk = cart_id_fk
        self.drink_id = drink_id
        self.quantity = quantity


    def json(self):
        return {"cart_items_id": self.cart_items_id, "cart_id_fk": self.cart_id_fk, "drink_id": self.drink_id, "quantity": self.quantity}




#Get all the items in the Cart_items table
@app.route("/cart_items")
def get_all_cart_items():
    cartItemList = db.session.scalars(db.select(Cart_Items)).all()


    if len(cartItemList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "carts": [cartItem.json() for cartItem in cartItemList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no cart items."
        }
    ), 404


#Get items from Cart_items based on the cart_item_id
@app.route("/cart_items_cartItemId/<int:cart_items_id>")
def find_cartItem_by_id(cart_items_id):
    cart_item = db.session.scalar(
    	db.select(Cart_Items).filter_by(cart_items_id = cart_items_id)
)


    if cart_item:
        return jsonify(
            {
                "code": 200,
                "data": cart_item.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Cart Item not found."
        }
    ), 404



#Get items from Cart_items based on the cart_id
@app.route("/cart_items_cartId/<int:cart_id_fk>")
def cartItem_by_cartId(cart_id_fk):
    # Fetch all cart items with the given cart_id_fk
    cart_items = db.session.scalars(
        select(Cart_Items).where(Cart_Items.cart_id_fk == cart_id_fk)
    ).all()

    if cart_items:
        return jsonify(
            {
                "code": 200,
                "data": [item.json() for item in cart_items]  # Convert all items to JSON
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No cart items found for the given cart ID."
        }
    ), 404
    
    
@app.route("/create_cart_items", methods=['POST'])
def create_cartItems():
    data = request.get_json()

    # Create a new Cart instance
    cartItem = Cart_Items(**data)

    try:
        db.session.add(cartItem)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the cart.",
                "error": str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": cartItem.json()
        }
    ), 201
    

#Updating the quanity of drink
@app.route("/update_cart_items/<int:cart_items_id>", methods=['PUT'])
def update_quantity(cart_items_id):
    try:
        cart_item = db.session.scalar(db.select(Cart_Items).filter_by(cart_items_id=cart_items_id))
        if not cart_item:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "cart_items_id": cart_items_id
                    },
                    "message": "Cart Item not found."
                }
            ), 404

        # update status
        data = request.get_json()
        if data['quantity']:
            cart_item.quantity = data['quantity']
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": cart_item.json()
                }
            ), 200
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "cart_items_id": cart_items_id
                },
                "message": "An error occurred while updating the cart. " + str(e)
            }
        ), 500


@app.route("/delete_cart_item/<int:cart_items_id>", methods=["DELETE"])
def delete_by_cartItemId(cart_items_id):
    # Find the cart by cartId
    cart_item = db.session.scalar(
        db.select(Cart_Items).filter_by(cart_items_id=cart_items_id)
    )

    if cart_item:
        # If the cart exists, delete it
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "Cart_item deleted successfully."
            }
        )
    else:
        # If the cart does not exist, return a 404 error
        return jsonify(
            {
                "code": 404,
                "message": "Cart_item not found."
            }
        ), 404   
        
#####################################################################################################################
class Cart_Items_Customisation(db.Model):
    __tablename__ = 'cart_item_customisation'


    cic_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_item_id_fk = db.Column(db.Integer, nullable=False)
    customisationId_fk = db.Column(db.Integer, nullable=False)


    def __init__(self, cart_item_id_fk, customisationId_fk):
        self.cart_item_id_fk = cart_item_id_fk
        self.customisationId_fk = customisationId_fk


    def json(self):
        return {"cic_id": self.cic_id, "cart_item_id_fk": self.cart_item_id_fk, "customisationId_fk": self.customisationId_fk}


#Get all the items in the Cart_item_customisation table
@app.route("/cic")
def get_all_cic():
    cicList = db.session.scalars(db.select(Cart_Items_Customisation)).all()


    if len(cicList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "cic": [cic.json() for cic in cicList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no CIC items."
        }
    ), 404


#Get items from Cart_items based on the cart_item_id
@app.route("/cic_by_id/<int:cic_id>")
def find_cic_by_id(cic_id):
    cicList = db.session.scalar(
    	db.select(Cart_Items_Customisation).filter_by(cic_id = cic_id)
)


    if cicList:
        return jsonify(
            {
                "code": 200,
                "data": cicList.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "CIC Item not found."
        }
    ), 404

@app.route("/create_cic", methods=['POST'])
def create_cic():
    data = request.get_json()

    # Create a new Cart instance
    cicList = Cart_Items_Customisation(**data)

    try:
        db.session.add(cicList)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the CIC.",
                "error": str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": cicList.json()
        }
    ), 201

#Updating the quanity of drink
@app.route("/update_cic/<int:cic_id>", methods=['PUT'])
def update_customisation(cic_id):
    try:
        cicList = db.session.scalar(db.select(Cart_Items_Customisation).filter_by(cic_id=cic_id))
        if not cicList:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "cic_id": cic_id
                    },
                    "message": "CustomisationId not found."
                }
            ), 404

        # update status
        data = request.get_json()
        if data['customisationId_fk']:
            cicList.customisationId_fk = data['customisationId_fk']
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": cicList.json()
                }
            ), 200
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "data": {
                    "cic_id": cic_id
                },
                "message": "An error occurred while updating the customisation. " + str(e)
            }
        ), 500
    
@app.route("/delete_cic/<int:cic_id>", methods=["DELETE"])
def delete_by_cicId(cic_id):
    # Find the cart by cartId
    cicList = db.session.scalar(
        db.select(Cart_Items_Customisation).filter_by(cic_id=cic_id)
    )

    if cicList:
        # If the cart exists, delete it
        db.session.delete(cicList)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "CIC Item deleted successfully."
            }
        )
    else:
        # If the cart does not exist, return a 404 error
        return jsonify(
            {
                "code": 404,
                "message": "CIC Item not found."
            }
        ), 404   



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015, debug=True)