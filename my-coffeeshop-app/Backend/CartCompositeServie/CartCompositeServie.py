from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

# URLs of individual microservices
cart_service_url = "http://host.docker.internal:5015/cart"
cart_items_service_url = "http://host.docker.internal:5016/cart_items"
cic_service_url = "http://host.docker.internal:5017/cic"


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if request.is_json:
        try:
            # Parse the incoming JSON request
            data = request.get_json()
            cart_data = data["cart"]
            cart_items_data = data["cart_items"]
            cic_data = data["cart_item_customisation"]

            # Check if cart already exists for this user and outlet
            user_id = cart_data["user_id"]
            outlet_id = cart_data["outlet_id"]
            check_cart_url = f"{cart_service_url}/{user_id}/{outlet_id}"
            existing_cart = invoke_http(check_cart_url, method="GET")
            
            # Calculate total price from drink prices and quantities
            # total_price = 0.0
            # for item in cart_items_data:
            #     drink_price = get_drink_price(item["drink_id"])
            #     total_price += drink_price * item["quantity"]
            #     print("Total Price = "+  str(total_price))

            if existing_cart["code"] == 200 and existing_cart["data"]["carts"]:
                # Cart exists - update it
                cart_id = existing_cart["data"]["carts"][0]["cart_id"]
                current_total = float(existing_cart["data"]["carts"][0]["totalPrice"])
                new_total = cart_data["totalPrice"]
                sub_total = current_total + new_total
                
                # Update cart with new total price
                update_cart_url = f"{cart_service_url}/{cart_id}"
                update_result = invoke_http(update_cart_url, method="PUT", json={"totalPrice": sub_total})
                
                if update_result["code"] not in range(200, 300):
                    return jsonify({
                        "code": update_result["code"],
                        "message": f"Failed to update cart: {update_result['message']}"
                    }), update_result["code"]
            else:
                # Cart doesn't exist - create new one with calculated total price
                # cart_data["totalPrice"] = total_price
                cart_result = invoke_http(cart_service_url, method="POST", json=cart_data)
                if cart_result["code"] not in range(200, 300):
                    return jsonify({
                        "code": cart_result["code"],
                        "message": f"Failed to add cart: {cart_result['message']}"
                    }), cart_result["code"]
                
                cart_id = cart_result["data"]["cart_id"]

            # Process cart items
            for item in cart_items_data:
                # Check if item already exists in cart
                check_item_url = f"{cart_items_service_url}/check/{cart_id}/{item['drink_id']}"
                existing_item = invoke_http(check_item_url, method="GET")
                
                if existing_item["code"] == 200 and existing_item["data"]:
                    # Item exists - update quantity
                    item_id = existing_item["data"]["cart_items_id"]
                    new_quantity = existing_item["data"]["quantity"] + item["quantity"]
                    update_item_url = f"{cart_items_service_url}/{item_id}"
                    item_result = invoke_http(update_item_url, method="PUT", json={"quantity": new_quantity})
                    
                    if item_result["code"] not in range(200, 300):
                        return jsonify({
                            "code": item_result["code"],
                            "message": f"Failed to update cart item: {item_result['message']}"
                        }), item_result["code"]
                    
                    item["cart_item_id"] = item_id
                else:
                    # Item doesn't exist - add new one
                    item["cart_id_fk"] = cart_id
                    item_result = invoke_http(cart_items_service_url, method="POST", json=item)
                    if item_result["code"] not in range(200, 300):
                        return jsonify({
                            "code": item_result["code"],
                            "message": f"Failed to add cart item: {item_result['message']}"
                        }), item_result["code"]
                    
                    item["cart_item_id"] = item_result["data"]["cart_items_id"]

                # Process customizations (assuming customizations might affect price)
                for customisation in cic_data:
                    customisation["cart_item_id_fk"] = item["cart_item_id"]
                    cic_result = invoke_http(cic_service_url, method="POST", json=customisation)
                    if cic_result["code"] not in range(200, 300):
                        return jsonify({
                            "code": cic_result["code"],
                            "message": f"Failed to add customisations: {cic_result['message']}"
                        }), cic_result["code"]

            # Return success response
            return jsonify({
                "code": 201,
                "message": "Successfully updated cart",
                "data": {
                    "cart_id": cart_id,
                    # "total_price": new_total if 'new_total' in locals() else total_price,
                    "items": [item for item in cart_items_data],
                    "customisations": cic_data
                }
            }), 201

        except Exception as e:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input"
    }), 400

@app.route('/get_cart_details/<user_id>/<int:outlet_id>', methods=['GET'])
def get_cart_details(user_id, outlet_id):
    try:
        # Step 1: Fetch cart information
        cart_url = f"http://host.docker.internal:5015/cart/{user_id}/{outlet_id}"
        cart_response = requests.get(cart_url)
        
        if cart_response.status_code != 200 or not cart_response.text.strip():
            return jsonify({"code": 500, "message": "Failed to fetch cart information"}), 500
        
        cart_data = cart_response.json()
        if "data" not in cart_data or not cart_data["data"]["carts"]:
            return jsonify({"code": 404, "message": "Cart not found"}), 404
        
        cart = cart_data["data"]["carts"][0]
        cart_id = cart["cart_id"]
        
        # Step 2: Fetch cart items
        cart_items_url = f"http://host.docker.internal:5016/cart_items/cartId/{cart_id}"
        cart_items_response = requests.get(cart_items_url)
        
        if cart_items_response.status_code != 200 or not cart_items_response.text.strip():
            return jsonify({"code": 500, "message": "Failed to fetch cart items"}), 500
        
        cart_items_data = cart_items_response.json()
        if "data" not in cart_items_data or not cart_items_data["data"]:
            return jsonify({"code": 404, "message": "Cart items not found"}), 404
        
        cart_items = []
        
        # Step 3: Fetch customizations and consolidate data
        for item in cart_items_data["data"]:
            cic_url = f"http://host.docker.internal:5017/cic/{item['cart_items_id']}"
            cic_response = requests.get(cic_url)
            
            customisations = None
            if cic_response.status_code == 200 and cic_response.text.strip():
                cic_data = cic_response.json()
                customisations = cic_data.get("data", None)
            
            # Consolidate relevant fields for this item
            consolidated_item = {
                "cart_items_id":item["cart_items_id"],
                "drink_id": item["drink_id"],
                "quantity": item["quantity"],
                "customisations": customisations
            }
            cart_items.append(consolidated_item)
        
        # Step 4: Final consolidated response
        consolidated_data = {
            "cart_id": cart["cart_id"],
            "user_id": cart["user_id"],
            "outlet_id": cart["outlet_id"],
            "totalPrice": cart["totalPrice"],
            "items": cart_items
        }
        
        return jsonify({"code": 200, "data": consolidated_data}), 200
    
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route('/get_cart_item_count/<user_id>/<int:outlet_id>', methods=['GET'])
def get_cart_item_count(user_id, outlet_id):
    try:
        # Step 1: Check if cart exists for this user and outlet
        check_cart_url = f"{cart_service_url}/{user_id}/{outlet_id}"
        cart_response = invoke_http(check_cart_url, method="GET")
        
        if cart_response["code"] != 200 or not cart_response["data"]["carts"]:
            return jsonify({
                "code": 200,
                "data": {
                    "item_count": 0,
                    "message": "No cart exists for this user and outlet"
                }
            }), 200
        
        cart_id = cart_response["data"]["carts"][0]["cart_id"]
        
        # Step 2: Get all cart items for this cart
        cart_items_url = f"{cart_items_service_url}/cartId/{cart_id}"
        cart_items_response = invoke_http(cart_items_url, method="GET")
        
        if cart_items_response["code"] != 200:
            return jsonify({
                "code": 500,
                "message": "Failed to fetch cart items"
            }), 500
        
        # Calculate total quantity of all items
        total_items = 0
        if cart_items_response["data"]:
            total_items = sum(item["quantity"] for item in cart_items_response["data"])
        
        return jsonify({
            "code": 200,
            "data": {
                "cart_id": cart_id,
                "item_count": total_items
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500


#this is to delete cart_items in cart page
@app.route('/delete_cart_item/<int:cart_item_id>', methods=['DELETE'])
def delete_cart_item(cart_item_id):
    try:
        # Step 1: Get the cart item details
        cart_item_url = f"{cart_items_service_url}/cartItemId/{cart_item_id}"
        print(cart_item_url)
        cart_item_response = invoke_http(cart_item_url, method="GET")
        
        if cart_item_response["code"] != 200:
            return jsonify({
                "code": 404,
                "message": "Cart item not found"
            }), 404
        
        cart_id = cart_item_response["data"]["cart_id_fk"]
        
        # Step 2: Delete all customizations for this item first
        cic_delete_url = f"{cic_service_url}/delete_by_cart_item/{cart_item_id}"
        print ("Cic Delete" + cic_delete_url)
        cic_delete_response = invoke_http(cic_delete_url, method="DELETE")
        
        if cic_delete_response["code"] not in range(200, 300):
            return jsonify({
                "code": cic_delete_response["code"],
                "message": f"Failed to delete customizations: {cic_delete_response['message']}"
            }), cic_delete_response["code"]
        
        # Step 3: Delete the cart item itself
        deleteCartItem_service = f"{cart_items_service_url}/{cart_item_id}"
        item_delete_response = invoke_http(deleteCartItem_service, method="DELETE")
        
        if item_delete_response["code"] not in range(200, 300):
            return jsonify({
                "code": item_delete_response["code"],
                "message": f"Failed to delete cart item: {item_delete_response['message']}"
            }), item_delete_response["code"]
        
        # Step 4: Check if this was the last item in the cart
        remaining_items_url = f"{cart_items_service_url}/cartId/{cart_id}"
        remaining_items_response = invoke_http(remaining_items_url, method="GET")
        
        if remaining_items_response["code"] == 200 and not remaining_items_response["data"]:
            # No items left - delete the entire cart
            cart_delete_url = f"{cart_service_url}/{cart_id}"
            cart_delete_response = invoke_http(cart_delete_url, method="DELETE")
            
            if cart_delete_response["code"] not in range(200, 300):
                return jsonify({
                    "code": cart_delete_response["code"],
                    "message": f"Failed to delete empty cart: {cart_delete_response['message']}"
                }), cart_delete_response["code"]
            
            return jsonify({
                "code": 200,
                "message": "Successfully deleted cart item and empty cart",
                "data": {
                    "cart_deleted": True,
                    "cart_id": cart_id
                }
            }), 200
        
        return jsonify({
            "code": 200,
            "message": "Successfully deleted cart item",
            "data": {
                "cart_deleted": False,
                "cart_id": cart_id
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500
    

#this is to remove the whole cart at the end
@app.route('/delete_cart/<int:cart_id>', methods=['DELETE'])
def delete_cart(cart_id):
    try:
        # Step 1: Verify the cart exists
        cart_info_url = f"{cart_service_url}/{cart_id}"
        cart_response = invoke_http(cart_info_url, method="GET")
        
        if cart_response["code"] != 200:
            return jsonify({
                "code": 404,
                "message": "Cart not found"
            }), 404
        
        # Step 2: Get all cart items for this cart
        cart_items_url = f"{cart_items_service_url}/cartId/{cart_id}"
        cart_items_response = invoke_http(cart_items_url, method="GET")
        
        if cart_items_response["code"] == 200 and cart_items_response["data"]:
            # Step 3: Delete all customizations for each cart item
            for item in cart_items_response["data"]:
                cart_item_id = item["cart_items_id"]
                cic_delete_url = f"{cic_service_url}/delete_by_cart_item/{cart_item_id}"
                cic_delete_response = invoke_http(cic_delete_url, method="DELETE")
                
                if cic_delete_response["code"] not in range(200, 300):
                    return jsonify({
                        "code": cic_delete_response["code"],
                        "message": f"Failed to delete customizations for item {cart_item_id}: {cic_delete_response['message']}"
                    }), cic_delete_response["code"]
            
            # Step 4: Delete all cart items in bulk
            delete_all_items_url = f"{cart_items_service_url}/byCartId/{cart_id}"
            items_delete_response = invoke_http(delete_all_items_url, method="DELETE")
            
            if items_delete_response["code"] not in range(200, 300):
                return jsonify({
                    "code": items_delete_response["code"],
                    "message": f"Failed to delete cart items: {items_delete_response['message']}"
                }), items_delete_response["code"]
        
        # Step 5: Delete the cart itself
        cart_delete_url = f"{cart_service_url}/{cart_id}"
        cart_delete_response = invoke_http(cart_delete_url, method="DELETE")
        
        if cart_delete_response["code"] not in range(200, 300):
            return jsonify({
                "code": cart_delete_response["code"],
                "message": f"Failed to delete cart: {cart_delete_response['message']}"
            }), cart_delete_response["code"]
        
        return jsonify({
            "code": 200,
            "message": "Successfully deleted cart with all items and customizations",
            "data": {
                "cart_id": cart_id,
                "items_deleted": len(cart_items_response.get("data", [])) if cart_items_response.get("code") == 200 else 0
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)