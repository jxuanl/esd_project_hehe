from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

# URLs of individual microservices
order_service_url = "https://personal-9fpjlj95.outsystemscloud.com/WorkerUI/rest/GetByOrderID/GetOrder"
order_items_service_url = "https://personal-9fpjlj95.outsystemscloud.com/WorkerUI/rest/GetByOrderID/GetOrderItemCustomisation"
Order_customisation_service_url = "https://personal-9fpjlj95.outsystemscloud.com/WorkerUI/rest/GetByOrderID/GetOrderItems"
drink_service_url = "http://localhost:5005/drinks"
outlet_service_url = "http://localhost:5001/outlets"
drink_customization_url = "http://127.0.0.1:5017/cic"

@app.route('/orders/count', methods=['GET'])
def get_order_count_by_outlet():
    # Get outlet_id from query parameters
    outlet_id = request.args.get('outlet_id')
    
    if not outlet_id:
        return jsonify({'error': 'outlet_id parameter is required'}), 400
    
    try:
        # Make request to the external API
        response = requests.get(
            order_service_url
        )
        response.raise_for_status()
        
        # Parse the JSON response
        orders_data = response.json()
        
        # Filter orders by outlet_id and count
        try:
            outlet_id_int = int(outlet_id)
            filtered_orders = [
                item['OrderDetails'] for item in orders_data 
                if item.get('OrderDetails', {}).get('outlet_id') == outlet_id_int
            ]
            count = len(filtered_orders)
            
            return jsonify({
                'outlet_id': outlet_id,
                'total_orders': count,
                # 'orders': filtered_orders
            })
        except ValueError:
            return jsonify({'error': 'outlet_id must be an integer'}), 400
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON response from API'}), 500
    
@app.route('/get_wait_time/<int:outlet_id>', methods=['GET'])
def get_wait_time(outlet_id):
    try:
        # Step 1: Get all orders for this outlet
        orders_url = f"{order_service_url}/outlet/{outlet_id}"
        orders_response = invoke_http(orders_url, method="GET")
        
        if orders_response["code"] != 200:
            return jsonify({
                "code": orders_response["code"],
                "message": f"Failed to fetch orders: {orders_response['message']}"
            }), orders_response["code"]
        
        orders = orders_response.get("data", [])
        if not orders:
            return jsonify({
                "code": 200,
                "data": {
                    "outlet_id": outlet_id,
                    "total_wait_time": 0,
                    "message": "No orders found for this outlet"
                }
            }), 200
        
        total_wait_time = 0
        
        # Step 2: For each order, get the outlet items
        for order in orders:
            order_id = order["order_id"]
            outlet_items_url = f"{order_items_service_url}/order/{order_id}"
            outlet_items_response = invoke_http(outlet_items_url, method="GET")
            
            if outlet_items_response["code"] != 200:
                # Skip this order if we can't get items
                continue
            
            outlet_items = outlet_items_response.get("data", [])
            
            # Step 3: For each outlet item, get the drink preparation time
            for item in outlet_items:
                drink_id = item["drink_id"]
                drink_url = f"{drink_service_url}/{drink_id}"
                drink_response = invoke_http(drink_url, method="GET")
                
                if drink_response["code"] == 200:
                    preparation_time = drink_response["data"].get("prep_time_min", 0)
                    total_wait_time += preparation_time * item.get("quantity", 1)
        
        # Step 4: Return the total wait time
        return jsonify({
            "code": 200,
            "data": {
                "outlet_id": outlet_id,
                "total_wait_time": total_wait_time,
                "unit": "minutes"  # Assuming preparation_time is in minutes
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/get_user_orders/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    try:
        # Step 1: Get all orders for this user
        orders_url = f"{order_service_url}?user_id={user_id}"  # Adjust based on actual API
        orders_response = invoke_http(orders_url, method="GET")
        
        if orders_response.get("code", 200) != 200:
            return jsonify({
                "code": orders_response.get("code", 500),
                "message": f"Failed to fetch orders: {orders_response.get('message', 'Unknown error')}"
            }), orders_response.get("code", 500)
        
        orders = []
        # Handle different response formats
        if isinstance(orders_response, list):
            orders = orders_response
        elif "OrderDetails" in orders_response:
            orders = [orders_response["OrderDetails"]]
        elif isinstance(orders_response.get("data"), list):
            orders = orders_response["data"]
        
        if not orders:
            return jsonify({
                "code": 200,
                "data": [],
                "message": "No orders found for this user"
            }), 200
        
        consolidated_orders = []
        
        # Step 2: Process each order
        for order in orders:
            order_id = order.get("order_id")
            outlet_id = order.get("outlet_id")
            
            # Step 2a: Get outlet details
            outlet_url = f"{outlet_service_url}/{outlet_id}"
            outlet_response = invoke_http(outlet_url, method="GET")
            
            outlet_name = "Unknown Outlet"
            if outlet_response.get("code", 200) == 200:
                outlet_data = outlet_response.get("data", outlet_response)
                outlet_name = outlet_data.get("name", "Unknown Outlet")
            
            # Step 2b: Get all items for this order
            order_items_url = f"{order_items_service_url}?order_id={order_id}"  # Adjust based on actual API
            items_response = invoke_http(order_items_url, method="GET")
            
            items = []
            if items_response.get("code", 200) == 200:
                order_items = []
                # Handle different response formats
                if "orderItems" in items_response:
                    order_items = [items_response["orderItems"]]
                elif "OrderItems" in items_response:
                    order_items = [items_response["OrderItems"]]
                elif isinstance(items_response.get("data"), list):
                    order_items = items_response["data"]
                
                for item in order_items:
                    item_id = item.get("order_item_id")
                    
                    # Step 2c: Get customizations for this item
                    customizations_url = f"{Order_customisation_service_url}?order_item_id={item_id}"  # Adjust based on actual API
                    customizations_response = invoke_http(customizations_url, method="GET")
                    
                    customizations = []
                    if customizations_response.get("code", 200) == 200:
                        customizations_data = []
                        # Handle different response formats
                        if "OrderItemCustomisation" in customizations_response:
                            customizations_data = [customizations_response["OrderItemCustomisation"]]
                        elif isinstance(customizations_response.get("data"), list):
                            customizations_data = customizations_response["data"]
                        
                        # Step 2d: Get customization names
                        for customization in customizations_data:
                            custom_id = customization.get("customisation_id")
                            if custom_id:
                                # Get customization details
                                custom_url = f"{drink_customization_url}/{custom_id}"  # Adjust based on actual API
                                custom_response = invoke_http(custom_url, method="GET")
                                
                                custom_name = f"Customization {custom_id}"  # Default if lookup fails
                                if custom_response.get("code", 200) == 200:
                                    custom_data = custom_response.get("data", custom_response)
                                    custom_name = custom_data.get("name", f"Customization {custom_id}")
                                
                                customizations.append({
                                    "customization_id": custom_id,
                                    "name": custom_name
                                })
                    
                    # Format the item with its customizations
                    formatted_item = {
                        "order_item_id": item_id,
                        "drink_id": item.get("drinks_id"),
                        "quantity": item.get("quantity", 1),
                        "price": item.get("price", 0),
                        "customizations": customizations
                    }
                    items.append(formatted_item)
            
            # Format the complete order
            formatted_order = {
                "order_id": order_id,
                "outlet_id": outlet_id,
                "outlet_name": outlet_name,
                "total_price": float(order.get("total_price", 0)) if order.get("total_price") else 0,
                "status": order.get("status", "unknown"),
                "date_created": order.get("timestamp") or order.get("date_created", ""),
                "items": items
            }
            consolidated_orders.append(formatted_order)
        
        # Step 3: Return consolidated orders
        return jsonify({
            "code": 200,
            "data": consolidated_orders
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/get_order_details/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    try:
        # Step 1: Get the order details
        order_url = f"{order_service_url}/{order_id}"
        order_response = invoke_http(order_url, method="GET")
        
        if order_response.get("code", 200) != 200:
            return jsonify({
                "code": order_response.get("code", 404),
                "message": f"Order not found: {order_response.get('message', 'Unknown error')}"
            }), order_response.get("code", 404)
        
        # Handle different response formats
        order = {}
        if "OrderDetails" in order_response:
            order = order_response["OrderDetails"]
        elif isinstance(order_response.get("data"), dict):
            order = order_response["data"]
        else:
            order = order_response

        outlet_id = order.get("outlet_id")
        
        # Step 2: Get outlet details - now including address, lat, and long
        outlet_url = f"{outlet_service_url}/{outlet_id}"
        outlet_response = invoke_http(outlet_url, method="GET")
        
        outlet_info = {
            "name": "Unknown Outlet",
            "address": "Address not available",
            "latitude": None,
            "longitude": None
        }
        
        if outlet_response.get("code", 200) == 200:
            outlet_data = outlet_response.get("data", outlet_response)
            outlet_info.update({
                "name": outlet_data.get("name", "Unknown Outlet"),
                "address": outlet_data.get("address", "Address not available"),
                "latitude": outlet_data.get("latitude"),
                "longitude": outlet_data.get("longitude")
            })
        
        # Step 3: Get all items for this order
        order_items_url = f"{order_items_service_url}/order/{order_id}"
        items_response = invoke_http(order_items_url, method="GET")
        
        items = []
        if items_response.get("code", 200) == 200:
            order_items = []
            if "orderItems" in items_response:
                order_items = [items_response["orderItems"]]
            elif "OrderItems" in items_response:
                order_items = [items_response["OrderItems"]]
            elif isinstance(items_response.get("data"), list):
                order_items = items_response["data"]
            else:
                order_items = items_response
            
            for item in order_items:
                item_id = item.get("order_item_id")
                
                # Step 4: Get customizations for this item
                customizations_url = f"{Order_customisation_service_url}/item/{item_id}"
                customizations_response = invoke_http(customizations_url, method="GET")
                
                customizations = []
                if customizations_response.get("code", 200) == 200:
                    customizations_data = []
                    if "OrderItemCustomisation" in customizations_response:
                        customizations_data = [customizations_response["OrderItemCustomisation"]]
                    elif isinstance(customizations_response.get("data"), list):
                        customizations_data = customizations_response["data"]
                    else:
                        customizations_data = customizations_response
                    
                    # Convert customization IDs to names
                    for customization in customizations_data:
                        custom_id = customization.get("customisation_id")
                        if custom_id:
                            custom_url = f"{drink_customization_url}/{custom_id}"
                            custom_response = invoke_http(custom_url, method="GET")
                            
                            custom_name = f"Customization {custom_id}"
                            if custom_response.get("code", 200) == 200:
                                custom_data = custom_response.get("data", custom_response)
                                custom_name = custom_data.get("name", f"Customization {custom_id}")
                            
                            customizations.append({
                                "customization_id": custom_id,
                                "name": custom_name
                            })
                
                # Format the item
                items.append({
                    "order_item_id": item_id,
                    "drink_id": item.get("drinks_id"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "customizations": customizations
                })
        
        # Format the complete response with additional outlet info
        response_data = {
            "order_id": order_id,
            "outlet_id": outlet_id,
            "outlet_info": outlet_info,  # Now contains name, address, lat, long
            "user_id": order.get("user_id"),
            "total_price": float(order.get("total_price", 0)) if order.get("total_price") else 0,
            "status": order.get("status", "unknown"),
            "date_created": order.get("timestamp") or order.get("date_created", ""),
            "items": items
        }
        
        return jsonify({
            "code": 200,
            "data": response_data
        }), 200
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)