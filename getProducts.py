import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template
from dataclasses import dataclass, fields

app = Flask(__name__)

# --- 1. FIREBASE INITIALIZATION ---
# This block handles security for both Local and Render environments
if os.environ.get('FIREBASE_CONFIG'):
    # PRODUCTION (Render): Read the JSON string from Environment Variables
    try:
        service_account_info = json.loads(os.environ.get('FIREBASE_CONFIG'))
        cred = credentials.Certificate(service_account_info)
    except Exception as e:
        print(f"Error parsing FIREBASE_CONFIG: {e}")
        cred = None
else:
    # LOCAL (PyCharm): Read from your local file
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
    except Exception as e:
        print(f"Local serviceAccountKey.json not found: {e}")
        cred = None

if cred:
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    print("Firebase could not be initialized. Check your credentials.")


# --- 2. DATA MODEL ---
@dataclass
class Product:
    barcode: str
    category: str
    name: str
    price: float
    productId: str
    productImage: str
    productunit: str
    quantityInStock: int

    @classmethod
    def from_dict(cls, source):
        # Only pull keys that exist in our dataclass to prevent errors
        class_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in source.items() if k in class_fields}
        return cls(**filtered_dict)


# --- 3. ROUTES ---
@app.route('/')
def kileo_home():
    try:
        # Path to your products sub-collection
        products_ref = db.collection("profile") \
            .document("7L2WOwYLbnfxIfYNdyBIkaFoNlo2") \
            .collection("products")

        docs = products_ref.get()

        # Build the list of Product objects
        inventory = []
        for doc in docs:
            if doc.exists:
                inventory.append(Product.from_dict(doc.to_dict()))

        # Pass the list to your modern index.html
        return render_template('index.html', products=inventory)

    except Exception as e:
        return f"An error occurred: {e}", 500


# --- 4. EXECUTION ---
if __name__ == '__main__':
    # Set debug=False for production deployment
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))