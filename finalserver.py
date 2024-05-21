from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import pandas as pd
from datetime import datetime
import logging


# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(50))
    name = db.Column(db.String(100))
    review = db.Column(db.Text)

# Ensure the directory for storing data exists
os.makedirs("data", exist_ok=True)
excel_file = "data/cyber_crime.xlsx"

# Load Excel data if it exists
if os.path.exists(excel_file):
    data = pd.read_excel(excel_file)
    data['RID'] = data['RID'].astype(str)
else:
    data = pd.DataFrame(columns=[
        "Complaint ID", "Type of Cyber Crime", "City", "Description", "Date Submitted", 
        "Status", "Victim ID", "Police Department Notes", "Resolution Details", 
        "Phone Number", "Victim Name", "RID", "NOC_File_Path", "Rstatus"
    ])

# Directory to save PDF files
pdfs_dir = os.path.join(app.root_path, "pdfs")
if not os.path.exists(pdfs_dir):
    os.makedirs(pdfs_dir)

# Home route to serve the form
@app.route('/')
def index():
    return render_template('index.html')

# Route for the complaint form
@app.route('/complaint')
def complaint():
    return render_template('complaint.html')

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    crime_type = data.get("crimeType")
    city = data.get("city")
    description = data.get("description")
    phone_number = data.get("phoneNumber")
    victim_name = data.get("victimName")
    date_submitted = datetime.now()

    if not all([crime_type, city, description, phone_number, victim_name]):
        return jsonify({"message": "Missing required fields"}), 400

    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
    else:
        df = pd.DataFrame(columns=[
            "Complaint ID", "Type of Cyber Crime", "City", "Description", "Date Submitted", 
            "Status", "Victim ID", "Police Department Notes", "Resolution Details", 
            "Phone Number", "Victim Name"
        ])

    complaint_id = "CID-" + datetime.now().strftime("%Y%m%d%H%M%S")

    new_data = pd.DataFrame([{
        "Complaint ID": complaint_id,
        "Type of Cyber Crime": crime_type,
        "City": city,
        "Description": description,
        "Date Submitted": date_submitted,
        "Status": "Received",
        "Victim ID": "",
        "Police Department Notes": "",
        "Resolution Details": "",
        "Phone Number": phone_number,
        "Victim Name": victim_name
    }])
    
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel(excel_file, index=False)

    return jsonify({"message": "Complaint submitted successfully", "complaint_id": complaint_id})

# Function to fetch complaint status
def fetch_status(cid):
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        df['Complaint ID'] = df['Complaint ID'].astype(str)
        row = df[df['Complaint ID'] == cid]
        if not row.empty:
            status = row.iloc[0]['Status']
            return status, ""
    return "Not Found", ""

# Function to get the registered name associated with the complaint ID
def get_registered_name(complaint_id):
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        df['Complaint ID'] = df['Complaint ID'].astype(str)
        row = df[df['Complaint ID'] == complaint_id]
        if not row.empty:
            victim_name = row.iloc[0]['Victim Name']
            return victim_name
    return None

# Route for tracking complaint status
@app.route('/track')
def track():
    return render_template('complaint_status.html')
@app.route('/status')
def get_status():
    complaint_id = request.args.get('id')
    status, update = fetch_status(complaint_id)
    return jsonify({"status": status, "update": update})

def fetch_status(complaint_id):
    excel_file = r"C:\Users\joshi\OneDrive\Desktop\collage\SEM 4\PYTHON\flask\data\cyber_crime.xlsx"
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        row = df[df['Complaint ID'] == complaint_id]
        if not row.empty:
            status = row.iloc[0]['Status']
            return status, ""  # No last update information available
    return "Not Found", ""


# Route to submit funds recovery request
@app.route('/submit_recovery', methods=['POST'])
def submit_recovery():
    try:
        complaint_id = request.form['complaint_id']
        noc = request.files['NOC']

        if complaint_id in data['Complaint ID'].values:
            noc_filename = f"noc_{complaint_id}.pdf"
            noc_path = os.path.join(pdfs_dir, noc_filename)
            noc.save(noc_path)

            rid = datetime.now().strftime("%Y%m%d%H%M%S")
            data.loc[data['Complaint ID'] == complaint_id, 'RID'] = rid
            data.loc[data['Complaint ID'] == complaint_id, 'NOC_File_Path'] = noc_path
            data.to_excel(excel_file, index=False)
            return jsonify({"success": True, "message": "Funds recovery request submitted successfully.", "rid": rid})
        else:
            return jsonify({"success": False, "error": "Complaint ID not found. Please try again."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Route to track funds recovery status
# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index1():
    return render_template('trackfunds.html')

@app.route('/status')
def status():
    rid = request.args.get('RID')
    if rid is None:
        return jsonify({"error": "Missing 'RID' parameter"}), 400

    status, update = fetch_status(rid)
    return jsonify({"status": status, "update": update})

def fetch_status(rid):
    excel_file = r"C:\Users\joshi\OneDrive\Desktop\collage\SEM 4\PYTHON\flask\data\cyber_crime.xlsx"
    
    if not os.path.exists(excel_file):
        return "Not Found", "Excel file not found"
    
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        return "Error", f"Error reading Excel file: {e}"

    if 'RID' not in df.columns or 'Rstatus' not in df.columns:
        return "Error", "Required columns missing in Excel file"

    df['RID'] = df['RID'].astype(str)

    row = df[df['RID'] == rid]

    if not row.empty:
        status = row.iloc[0]['Rstatus']
        return status, ""
    else:
        return "Not Found", "RID not found"

# Route to submit a review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.json
    complaint_id = data.get('complaint_id')
    review_text = data.get('review')

    status, _ = fetch_status(complaint_id)
    if status == "Not Found":
        return jsonify({"success": False, "error": "Complaint ID not found."})

    registered_name = get_registered_name(complaint_id)
    review = Review(complaint_id=complaint_id, name=registered_name, review=review_text)
    db.session.add(review)
    db.session.commit()

    return jsonify({"success": True})

# Route to get all reviews
@app.route('/get_reviews')
def get_reviews():
    reviews_from_db = Review.query.all()
    return jsonify({"reviews": [{"id": review.id, "name": review.name, "complaint_id": review.complaint_id, "review": review.review} for review in reviews_from_db]})

# Route to delete a review
@app.route('/delete_review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if review:
        db.session.delete(review)
        db.session.commit()
        return jsonify({"success": True, "message": "Review deleted successfully."})
    else:
        return jsonify({"success": False, "error": "Review not found."})

# Route for guidance
@app.route('/guidance')
def guidance():
    return render_template('guidance.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
