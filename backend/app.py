from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route("/track")
def track():
    num = request.args.get("num", "").strip()
    if not num:
        return jsonify({"error": "Aucun numéro de suivi fourni."}), 400

    num = num.upper()
    transporteur = "Inconnu"

    if num.startswith("CB") and num.endswith("FR") and len(num) == 13:
        transporteur = "Colissimo"
    elif num.startswith("JJD") and len(num) in [24, 25]:
        transporteur = "DHL"
    elif re.match(r"^\d{14}$", num):
        transporteur = "DPD"
    elif re.match(r"^\d{11}$", num):
        transporteur = "GLS"
    elif re.match(r"^[A-Z0-9]{8,}$", num):
        transporteur = "GLS"
    elif len(num) in [15, 20] and num.isdigit():
        transporteur = "FedEx"
    elif re.match(r"^[A-Z]{2}\d{9}[A-Z]{2}$", num) or len(num) == 15:
        transporteur = "Chronopost"

    headers = {"User-Agent": "Mozilla/5.0"}

    if transporteur == "Chronopost":
        chrono_url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={num}"
        return jsonify({
            "transporteur": "Chronopost",
            "tracking": num,
            "statut": "Non trouvé",
            "date_livraison": "Indisponible",
            "historique": [],
            "lien": chrono_url
        })

    return jsonify({
        "transporteur": transporteur,
        "tracking": num,
        "statut": "Non trouvé",
        "date_livraison": "Indisponible",
        "historique": [],
        "lien": "https://google.com"
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
