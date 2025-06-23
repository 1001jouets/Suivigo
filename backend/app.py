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
        return jsonify({"error": "Numéro manquant"}), 400

    # Détection du transporteur
    transporteur = "Inconnu"
    if re.match(r"^[A-Z0-9]{8,12}$", num, re.IGNORECASE):
        transporteur = "GLS"
    elif re.match(r"^\d{14}$", num):
        transporteur = "DPD"
    elif re.match(r"^(?!1362961)\d{13}$", num) or re.match(r"^(CB|6A)\d{11}$", num):
        transporteur = "Colissimo"
    elif re.match(r"^JJD\d{20,}$", num):
        transporteur = "DHL"
    elif re.match(r"^\d{20}$", num):
        transporteur = "DHL"
    elif re.match(r"^\d{12}$", num) or re.match(r"^\d{15}$", num) or re.match(r"^\d{20}$", num):
        transporteur = "FedEx"
    elif re.match(r"^\d{17}$", num):
        transporteur = "Agediss"

    headers = {"User-Agent": "Mozilla/5.0"}

    if transporteur == "GLS":
        try:
            gls_url = f"https://gls-group.eu/FR/fr/suivi-colis?match={num}"
            r = requests.get(gls_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".status")
            date = soup.select_one(".estimated")
            historique = [el.text.strip() for el in soup.select(".history")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": gls_url})
        except Exception as e:
            return jsonify({"error": "GLS tracking failed", "details": str(e)}), 500

    if transporteur == "DPD":
        try:
            dpd_url = f"https://www.dpd.com/tracking/(lang)/fr_FR?parcelNumber={num}"
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": "Non trouvé", "date_livraison": "Indisponible", "historique": [], "lien": dpd_url})
        except Exception as e:
            return jsonify({"error": "DPD tracking failed", "details": str(e)}), 500

    if transporteur == "Colissimo":
        try:
            colissimo_url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}"
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": "Non trouvé", "date_livraison": "Indisponible", "historique": [], "lien": colissimo_url})
        except Exception as e:
            return jsonify({"error": "Colissimo tracking failed", "details": str(e)}), 500

    if transporteur == "DHL":
        try:
            dhl_url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}"
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": "Non trouvé", "date_livraison": "Indisponible", "historique": [], "lien": dhl_url})
        except Exception as e:
            return jsonify({"error": "DHL tracking failed", "details": str(e)}), 500

    if transporteur == "Agediss":
        try:
            agediss_url = f"https://www.agediss.com/fr/suivi/{num}"
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": "Non trouvé", "date_livraison": "Indisponible", "historique": [], "lien": agediss_url})
        except Exception as e:
            return jsonify({"error": "Agediss tracking failed", "details": str(e)}), 500

    if transporteur == "FedEx":
        try:
            fedex_url = f"https://www.fedex.com/fedextrack/?tracknumbers={num}"
            r = requests.get(fedex_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".statusChevron")
            date = soup.select_one(".estimatedDeliveryDate")
            historique = [el.text.strip() for el in soup.select(".statusBar")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": fedex_url})
        except Exception as e:
            return jsonify({"error": "FedEx tracking failed", "details": str(e)}), 500

    return jsonify({"transporteur": transporteur, "tracking": num, "message": "Tracking non encore pris en charge pour ce transporteur"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
