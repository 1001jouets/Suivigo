# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route("/track", methods=["GET"])
def track():
    num = request.args.get("num", "")
    if not num:
        return jsonify({"error": "missing tracking number"}), 400

    # Detect transporteur
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
    elif len(num) == 11 and num.startswith("3"):
        transporteur = "Agediss"
    else:
        transporteur = "Inconnu"

    headers = {"User-Agent": "Mozilla/5.0"}

    if transporteur == "GLS":
        try:
            gls_url = f"https://gls-group.eu/FR/fr/suivi-colis?match={num}"
            r = requests.get(gls_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".status-detail .step-current .title")
            date = soup.select_one(".status-detail .step-current .date")
            historique = [el.text.strip() for el in soup.select(".step-completed .title")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": gls_url})
        except Exception as e:
            return jsonify({"error": "GLS tracking failed", "details": str(e)}), 500

    if transporteur == "DPD":
        try:
            dpd_url = f"https://www.dpdgroup.com/be/mydpd/my-parcels/incoming?parcelNumber={num}"
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": "Consulter le lien de suivi",
                "date_livraison": "Indisponible",
                "historique": [],
                "lien": dpd_url
            })
        except Exception as e:
            return jsonify({"error": "DPD tracking failed", "details": str(e)}), 500

    if transporteur == "Colissimo":
        try:
            colissimo_url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}"
            r = requests.get(colissimo_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".status .title")
            date = soup.select_one(".status .date")
            historique = [el.text.strip() for el in soup.select(".history .event .description")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": colissimo_url})
        except Exception as e:
            return jsonify({"error": "Colissimo tracking failed", "details": str(e)}), 500

    if transporteur == "DHL":
        try:
            dhl_url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}"
            r = requests.get(dhl_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".shipment-status")
            date = soup.select_one(".shipment-date")
            historique = [el.text.strip() for el in soup.select(".shipment-status-detail")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": dhl_url})
        except Exception as e:
            return jsonify({"error": "DHL tracking failed", "details": str(e)}), 500

    if transporteur == "Agediss":
        try:
            agediss_url = f"https://agediss.com/fr/suivi/{num}"
            r = requests.get(agediss_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".suivi_statut")
            date = soup.select_one(".suivi_date")
            historique = [el.text.strip() for el in soup.select(".suivi_historique .suivi_etape")]
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut.text.strip() if statut else "Non trouvé", "date_livraison": date.text.strip() if date else "Indisponible", "historique": historique, "lien": agediss_url})
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

