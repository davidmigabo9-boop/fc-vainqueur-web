import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
app = create_app()
app.config["TESTING"] = True

with app.app_context():
    from extensions import db
    from models.joueur import Joueur
    from models.budget import Budget
    from models.user import Utilisateur
    db.create_all()

    with app.test_client() as c:
        c.post('/login', data={'username': 'admin', 'password': 'admin123'})

        # Create test data
        c.post('/joueurs/ajouter', data={'nom': 'Dupont', 'prenom': 'Jean', 'numero': '9', 'poste': 'ATT'})
        c.post('/joueurs/ajouter', data={'nom': 'Martin', 'prenom': 'Paul', 'numero': '10', 'poste': 'MIL'})
        c.post('/budget/ajouter', data={'type_operation': 'recette', 'motif': 'Cotisations', 'montant': '50000', 'date_operation': '2026-07-01'})
        c.post('/budget/ajouter', data={'type_operation': 'depense', 'motif': 'Equipement', 'montant': '20000', 'date_operation': '2026-07-15'})
        c.post('/equipements/ajouter', data={'nom': 'Ballon', 'categorie': 'BALLON', 'quantite': '5', 'etat': 'BON'})
        c.post('/equipements/ajouter', data={'nom': 'Maillot', 'categorie': 'TENUE', 'quantite': '20', 'etat': 'Neuf'})

        all_ok = True
        def check(route, r, expected=None):
            global all_ok
            ok = r.status_code == expected if expected else r.status_code == 200
            if not ok: all_ok = False
            print(f"  {route}: {'OK' if ok else 'FAIL(' + str(r.status_code) + ')'}")

        # All GET routes
        for route in ['/dashboard', '/joueurs/', '/joueurs/ajouter', '/budget/', '/budget/ajouter',
                      '/budget/chart-data', '/equipements/', '/equipements/ajouter', '/settings/']:
            check(f'GET {route}', c.get(route))

        # Export routes
        for route in ['/budget/export/pdf', '/budget/export/excel',
                      '/equipements/export/pdf', '/equipements/export/excel',
                      '/joueurs/export/pdf', '/joueurs/export/excel']:
            check(f'GET {route}', c.get(route))

        # ID-specific routes
        j = Joueur.query.first()
        b = Budget.query.first()
        if j:
            check(f'GET /joueurs/{j.id}', c.get(f'/joueurs/{j.id}'))
            check(f'GET /joueurs/{j.id}/modifier', c.get(f'/joueurs/{j.id}/modifier'))
        if b:
            check(f'GET /budget/{b.id}/modifier', c.get(f'/budget/{b.id}/modifier'))

        # POST modifier budget
        if b:
            r = c.post(f'/budget/{b.id}/modifier', data={
                'motif': 'Motif modifie', 'montant': '75000',
                'responsable': 'Admin', 'date_operation': '2026-07-20'
            }, follow_redirects=True)
            check(f'POST /budget/{b.id}/modifier', r)

        # POST modifier joueur
        if j:
            r = c.post(f'/joueurs/{j.id}/modifier', data={
                'nom': 'DupontMod', 'prenom': 'Jean', 'numero': '9', 'poste': 'ATT'
            }, follow_redirects=True)
            check(f'POST /joueurs/{j.id}/modifier', r)

        # Add contribution
        if j:
            r = c.post(f'/joueurs/{j.id}/contributions/ajouter', data={
                'montant': '5000', 'description': 'Test', 'date_contribution': '2026-07-21'
            }, follow_redirects=True)
            check(f'POST contribution', r)

        # Delete joueur with admin password
        j2 = Joueur.query.filter_by(nom='Martin').first()
        if j2:
            r = c.post(f'/joueurs/{j2.id}/supprimer', data={'admin_password': 'admin123'}, follow_redirects=True)
            check(f'POST /joueurs/{j2.id}/supprimer', r)

        # === ROLE-BASED ACCESS TESTS ===
        # Create limited users
        c.get('/logout')
        c.post('/login', data={'username': 'admin', 'password': 'admin123'})
        u = Utilisateur(nom_complet='Coach', username='coach', role='entraineur')
        u.set_password('test123')
        db.session.add(u)
        u2 = Utilisateur(nom_complet='Spectateur', username='lecteur', role='lecteur')
        u2.set_password('test123')
        db.session.add(u2)
        db.session.commit()

        # EntraI neur: can see dashboard + joueurs, denied budget/settings/joueurs_ajouter
        c.get('/logout')
        c.post('/login', data={'username': 'coach', 'password': 'test123'})
        check('GET /dashboard (entraineur)', c.get('/dashboard'))
        check('GET /joueurs/ (entraineur)', c.get('/joueurs/'))
        check('GET /budget/ (entraineur - denied=302)', c.get('/budget/'), expected=302)
        check('GET /settings/ (entraineur - denied=302)', c.get('/settings/'), expected=302)
        check('GET /joueurs/ajouter (entraineur - denied=302)', c.get('/joueurs/ajouter'), expected=302)
        check('GET /joueurs/export/pdf (entraineur)', c.get('/joueurs/export/pdf'))

        # Lecteur: can see everything read-only, denied add/modify/delete
        c.get('/logout')
        c.post('/login', data={'username': 'lecteur', 'password': 'test123'})
        check('GET /dashboard (lecteur)', c.get('/dashboard'))
        check('GET /joueurs/ (lecteur)', c.get('/joueurs/'))
        check('GET /budget/ (lecteur)', c.get('/budget/'))
        check('GET /equipements/ (lecteur)', c.get('/equipements/'))
        check('GET /joueurs/ajouter (lecteur - denied=302)', c.get('/joueurs/ajouter'), expected=302)
        check('GET /budget/ajouter (lecteur - denied=302)', c.get('/budget/ajouter'), expected=302)
        check('GET /settings/ (lecteur - denied=302)', c.get('/settings/'), expected=302)

        c.get('/logout')
        print(f"\n{'ALL TESTS PASSED!' if all_ok else 'SOME TESTS FAILED'}")
