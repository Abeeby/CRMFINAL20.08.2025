import requests

BASE = "http://127.0.0.1:5005"

def get(path):
    r = requests.get(BASE + path, allow_redirects=False)
    print(path, r.status_code)
    return r

def main():
    # Pages publiques / redirections
    get("/")
    get("/login")
    # Ces pages nécessitent une session, on s'assure que le serveur répond (302 attendu vers /login)
    for path in ["/dashboard", "/employes", "/clients", "/chantiers", "/devis", "/factures", "/leads", "/badges", "/carte", "/parametres"]:
        r = get(path)
        assert r.status_code in (200, 302), f"Unexpected status for {path}: {r.status_code}"
    # API stats (devrait renvoyer 302 non authentifié)
    r = get("/api/stats/dashboard")
    assert r.status_code in (200, 302), f"Unexpected status for stats: {r.status_code}"
    # Interface badge (publique)
    r = get("/employee/badge")
    assert r.status_code == 200

    # Test API badge (publique)
    br = requests.post(BASE + "/api/badge/check", json={"matricule": "EMP001", "type": "matin"})
    print("POST /api/badge/check", br.status_code, br.text[:120])
    assert br.status_code in (200, 400), "Badge API should accept or reject logically"
    print("Smoke tests passed (non-auth paths) ✔")

if __name__ == "__main__":
    main()


