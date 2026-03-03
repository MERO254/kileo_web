import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template
from dataclasses import dataclass, fields

app = Flask(__name__)

# --- 1. FIREBASE INITIALIZATION (Global Scope) ---
# We initialize these as None so the 'kileo_home' function can always "see" them
db = None


def initialize_firebase():
    global db
    cred = None

    # Check for Render Environment Variable first
    if os.environ.get('FIREBASE_CONFIG'):
        try:
            service_account_info = json.loads(os.environ.get('FIREBASE_CONFIG'))
            cred = credentials.Certificate(service_account_info)
        except Exception as e:
            print(f"Error parsing FIREBASE_CONFIG variable: {e}")

    # Fallback to local file for PyCharm
    elif os.path.exists("serviceAccountKey.json"):
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
        except Exception as e:
            print(f"Error loading local serviceAccountKey.json: {e}")

    if cred:
        try:
            # Check if app is already initialized to avoid errors on redeploy
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Firebase Client Error: {e}")
    else:
        print("No valid credentials found for Firebase.")


# Run the initialization
initialize_firebase()


# --- 2. DATA MODEL ---
@dataclass
class Product:
    barcode: str
    category: str
    name: str
    price: float
    productId: str
    productImage: str
    productunit: str  # Matches your Firestore data key
    quantityInStock: int

    @classmethod
    def from_dict(cls, source):
        # Only pull keys that exist in our dataclass
        class_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in source.items() if k in class_fields}
        return cls(**filtered_dict)


# --- 3. ROUTES ---
@app.route('/')
def kileo_home():
    # If db is None, the initialization failed (likely bad credentials on Render)
    if db is None:
        return "Database Error: Could not connect to Firestore. Check Render Environment Variables.", 500

    try:
        # Path to your products sub-collection
        products_ref = db.collection("profile") \
            .document("7L2WOwYLbnfxIfYNdyBIkaFoNlo2") \
            .collection("products")

        docs = products_ref.get()

        inventory = []
        for doc in docs:
            if doc.exists:
                inventory.append(Product.from_dict(doc.to_dict()))

        return render_template('index.html', products=inventory)

    except Exception as e:
        return f"An error occurred while fetching data: {e}", 500


# --- 4. EXECUTION ---
if __name__ == '__main__':
    # Use Render's assigned port, or default to 5000 for local PyCharm use
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)