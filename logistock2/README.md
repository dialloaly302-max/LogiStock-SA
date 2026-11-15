\# LogiStock SA



Application web de gestion de \*\*stock, de ventes et de crédits clients\*\* pour une petite boutique (montants en FCFA).



\## Fonctionnalités

\- Connexion sécurisée et 4 rôles : administrateur, manager, gestionnaire des ventes, gestionnaire de stock.

\- Catalogue : catégories et produits (code unique, prix, seuil minimal).

\- Stock par \*\*mouvements\*\* (entrées et sorties) : le stock se calcule, on ne modifie jamais une quantité. Inventaire et alertes de stock bas.

\- Clients : fiche, solde, badges (Bon payeur, Débiteur, En retard), archivage.

\- Ventes au comptant ou à crédit, avec contrôle du stock, de la remise et du plafond de crédit.

\- Annulation d'une vente (motif obligatoire), paiements, facture A4 et ticket 80 mm.

\- Tableau de bord : ventes, stock critique, crédits, produits les plus vendus, exports PDF et Excel.



\## Technologies

Python 3.12, Django 5.2, MariaDB (XAMPP), Bootstrap 5 et Chart.js (fichiers locaux), openpyxl, reportlab.



\## Installation (Windows)

Prérequis : Python 3.12, Git, XAMPP avec \*\*MySQL démarré\*\*.



1\. Récupérer le projet et créer l'environnement Python :

```powershell

git clone <URL\_DU\_DEPOT>

cd logistock2

python -m venv venv

.\\venv\\Scripts\\activate

pip install -r requirements.txt

```



2\. Créer à la racine un fichier `.env` (jamais publié sur GitHub) :

```

DB\_NAME=logistock

DB\_USER=root

DB\_PASSWORD=

DB\_HOST=127.0.0.1

DB\_PORT=3306

```



\## Import de la base de données

Le fichier de sauvegarde `.sql` n'est pas sur GitHub (il contient des données) : il est fourni séparément.

```powershell

\# Crée la base vide.

\& "C:\\xampp\\mysql\\bin\\mysql.exe" -u root -e "CREATE DATABASE logistock CHARACTER SET utf8mb4 COLLATE utf8mb4\_general\_ci;"

\# Importe la sauvegarde (adapter le nom du fichier).

$f = (Resolve-Path .\\sauvegarde\_logistock.sql).Path -replace '\\\\','/'

\& "C:\\xampp\\mysql\\bin\\mysql.exe" -u root --default-character-set=utf8mb4 logistock -e "source $f"

```

Les tables existent déjà : \*\*ne pas lancer `makemigrations`\*\*.



\## Lancement

```powershell

python manage.py check

python manage.py runserver

```

Ouvrir http://127.0.0.1:8000/



\## Comptes de test

| Identifiant | Rôle | Accès principal |

|---|---|---|

| AD18 | Administrateur | Tout, dont les utilisateurs et le prix de vente |

| OT99 | Manager | Consultation, tableau de bord et exports |

| DP00 | Gestionnaire des ventes | Clients, ventes, paiements, annulations |

| CM01, BF02 | Gestionnaire de stock | Catalogue, stock, inventaire |



Les mots de passe se définissent avec : `python manage.py changepassword IDENTIFIANT`



\## Règles importantes

\- Le stock = entrées - sorties. \*\*Rien n'est supprimé\*\* : une annulation ajoute des mouvements de correction, un client se \*\*archive\*\*.

\- Une vente est enregistrée dans \*\*une seule transaction\*\* : si une règle échoue, rien n'est enregistré.

\- Remise limitée à 10 % pour le gestionnaire des ventes. Crédit refusé si le plafond est dépassé ou si le client est en retard de plus de 30 jours (l'administrateur peut autoriser).

\- 5 échecs de connexion bloquent le compte 15 minutes.



\## Tests

```powershell

python manage.py test --noinput

```

168 tests automatiques (base temporaire : les vraies données ne sont pas touchées).



\## Structure

`comptes` (connexion, rôles), `catalogue`, `stock`, `clients`, `ventes`, `tableau\_bord`, `templates/`, `static/`.



\## Sauvegarde

```powershell

\& "C:\\xampp\\mysql\\bin\\mysqldump.exe" -u root --result-file=sauvegarde\_logistock.sql logistock

```

