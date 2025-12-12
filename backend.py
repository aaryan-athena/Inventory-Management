"""
FIFO Inventory Tracker - Flask Backend with Firebase
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize Firebase
if not firebase_admin._apps:
    # Try to load from environment variable first (for Render deployment)
    firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
    
    if firebase_creds and firebase_creds.strip():
        # Parse JSON credentials from environment variable
        try:
            import json
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from environment variable")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing FIREBASE_CREDENTIALS: {e}")
            print("   Make sure the environment variable contains valid JSON")
            raise
    else:
        # Fallback to local file for development
        cred_path = r"C:\Users\AIT 33\Documents\Secrets\firebase-admin-sdk.json"
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from local file")
        else:
            print(f"⚠️ Warning: Firebase credentials not found")
            print(f"   Set FIREBASE_CREDENTIALS env variable or update path in backend.py")

db = firestore.client()
INVENTORY_COLLECTION = "inventory_items"
SETTINGS_COLLECTION = "settings"

# ============== INVENTORY ENDPOINTS ==============

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get all inventory items"""
    try:
        items = []
        docs = db.collection(INVENTORY_COLLECTION).stream()
        
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
        
        return jsonify({"success": True, "data": items}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    """Add a new inventory item"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['productName', 'productId', 'batchNumber', 'expiryDate', 
                          'quantity', 'price', 'shelfLife', 'category']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Check for duplicate Product ID
        existing = db.collection(INVENTORY_COLLECTION).where('productId', '==', data['productId']).limit(1).get()
        if len(list(existing)) > 0:
            return jsonify({"success": False, "error": f"Product ID '{data['productId']}' already exists"}), 400
        
        # Add timestamp
        data['dateAdded'] = datetime.now().strftime('%Y-%m-%d')
        data['createdAt'] = firestore.SERVER_TIMESTAMP
        
        # Add to Firebase
        doc_ref = db.collection(INVENTORY_COLLECTION).add(data)
        
        return jsonify({
            "success": True, 
            "message": "Item added successfully",
            "id": doc_ref[1].id
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/inventory/<item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    """Delete an inventory item"""
    try:
        db.collection(INVENTORY_COLLECTION).document(item_id).delete()
        return jsonify({"success": True, "message": "Item deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/inventory/<item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    """Update an inventory item"""
    try:
        data = request.json
        data['updatedAt'] = firestore.SERVER_TIMESTAMP
        
        db.collection(INVENTORY_COLLECTION).document(item_id).update(data)
        return jsonify({"success": True, "message": "Item updated successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/inventory/clear', methods=['DELETE'])
def clear_all_inventory():
    """Clear all inventory items"""
    try:
        # Get all documents
        docs = db.collection(INVENTORY_COLLECTION).stream()
        
        # Delete each document
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
        
        batch.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Cleared {count} items successfully"
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============== SETTINGS ENDPOINTS ==============

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get application settings"""
    try:
        doc = db.collection(SETTINGS_COLLECTION).document('config').get()
        
        if doc.exists:
            settings = doc.to_dict()
        else:
            # Default settings
            settings = {
                "maxDiscount": 50,
                "criticalDays": 3,
                "warningDays": 7,
                "moderateDays": 14,
                "discountCritical": 50,
                "discountWarning": 30,
                "discountModerate": 15,
                "currencySymbol": "$"
            }
        
        return jsonify({"success": True, "data": settings}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save application settings"""
    try:
        data = request.json
        data['updatedAt'] = firestore.SERVER_TIMESTAMP
        
        db.collection(SETTINGS_COLLECTION).document('config').set(data)
        
        return jsonify({"success": True, "message": "Settings saved successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults"""
    try:
        default_settings = {
            "maxDiscount": 50,
            "criticalDays": 3,
            "warningDays": 7,
            "moderateDays": 14,
            "discountCritical": 50,
            "discountWarning": 30,
            "discountModerate": 15,
            "currencySymbol": "$",
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        db.collection(SETTINGS_COLLECTION).document('config').set(default_settings)
        
        return jsonify({"success": True, "message": "Settings reset successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============== HEALTH CHECK ==============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "firebase_connected": firebase_admin._apps is not None
    }), 200


# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("FIFO Inventory Tracker - Backend Server")
    print("=" * 50)
    print(f"Server starting on port {port}")
    print("Frontend should be served separately (e.g., with Live Server)")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
