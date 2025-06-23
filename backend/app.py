# backend/app.py
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/track", methods=["GET"])
def track():
    num = request.args.get("num", "")
    if not num:
        return jsonify({"error": "missing tracking number"}), 400

    # START: Detect transporteur
    if num.startswith("CB") and num.endswith("FR"):
        transporteur = "Colissimo"
    elif len(num) == 11 and num.isdigit():
        transporteur = "GLS"
    elif len(num) == 14 and num.isdigit():
        transporteur = "DPD"
    elif num.startswith("JJD") or len(num) in [18, 20]:
        transporteur = "DHL"
    elif len(num) in range(12, 16) and num.isdigit():
        transporteur = "FedEx"
    else:
        transporteur = "Inconnu"

    if transporteur == "GLS":
        try:
            gls_url = f"https://gls-group.eu/FR/fr/suivi-colis?match={num}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(gls_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")

            statut = soup.select_one(".status-detail .step-current .title")
            date = soup.select_one(".status-detail .step-current .date")
            historique = [el.text.strip() for el in soup.select(".step-completed .title")]

            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut.text.strip() if statut else "Non trouvé",
                "date_livraison": date.text.strip() if date else "Indisponible",
                "historique": historique,
                "lien": gls_url
            })
        except Exception as e:
            return jsonify({"error": "GLS tracking failed", "details": str(e)}), 500

    return jsonify({
        "transporteur": transporteur,
        "tracking": num,
        "message": "Tracking non encore pris en charge pour ce transporteur"
    })
