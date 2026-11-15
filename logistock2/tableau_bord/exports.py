from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

BLEU_NUIT = "1E3A5F"
ROUGE_CLAIR = "FDE2E2"
FORMAT_FCFA = '#,##0" FCFA"'


# ---------- Petits outils, partagés avec l'export PDF ----------

def formater_fcfa(valeur):
    """1250000 devient « 1 250 000 FCFA » (avec des espaces simples)."""
    return f"{int(valeur):,}".replace(",", " ") + " FCFA"


def formater_date(jour):
    return jour.strftime("%d/%m/%Y")


def nom_utilisateur(utilisateur):
    return f"{utilisateur.nom} {utilisateur.prenom or ''}".strip()


def maintenant_texte():
    return timezone.localtime().strftime("%d/%m/%Y %H:%M")


# ---------- Export Excel ----------

def _entete(feuille, ligne, titres):
    for colonne, titre in enumerate(titres, start=1):
        cellule = feuille.cell(row=ligne, column=colonne, value=titre)
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = PatternFill("solid", fgColor=BLEU_NUIT)
        cellule.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )


def _largeurs(feuille, largeurs):
    for numero, largeur in enumerate(largeurs, start=1):
        feuille.column_dimensions[get_column_letter(numero)].width = largeur


def construire_excel(donnees, utilisateur):
    """Fabrique le fichier Excel (3 feuilles) et le renvoie en octets."""
    gras = Font(bold=True)
    classeur = Workbook()

    # --- Feuille 1 : le résumé ---
    resume = classeur.active
    resume.title = "Résumé"
    resume["A1"] = "LogiStock SA - Tableau de bord"
    resume["A1"].font = Font(bold=True, size=16, color=BLEU_NUIT)
    resume["A2"] = (
        f"Période : du {formater_date(donnees['debut'])} "
        f"au {formater_date(donnees['fin'])}"
    )
    resume["A3"] = f"Édité le {maintenant_texte()} par {nom_utilisateur(utilisateur)}"
    _entete(resume, 5, ["Indicateur", "Valeur", "Détail"])
    indicateurs = [
        ("Ventes du jour", donnees["jour"]["total"],
         f"{donnees['jour']['nombre']} vente(s) validée(s) aujourd'hui", True),
        ("Ventes du mois", donnees["mois"]["total"],
         f"{donnees['mois']['nombre']} vente(s) validée(s) ce mois-ci", True),
        ("Produits en stock critique", donnees["nb_critiques"],
         "stock inférieur ou égal au seuil minimal", False),
        ("Crédits à recouvrer", donnees["credits"]["total"],
         f"{donnees['credits']['nombre']} client(s) avec une dette", True),
        ("Chiffre d'affaires de la période", donnees["periode"]["total"],
         f"{donnees['periode']['nombre']} vente(s) validée(s), ventes annulées exclues",
         True),
    ]
    for numero, (nom, valeur, detail, est_montant) in enumerate(indicateurs, start=6):
        resume.cell(row=numero, column=1, value=nom)
        cellule = resume.cell(row=numero, column=2, value=valeur)
        cellule.number_format = FORMAT_FCFA if est_montant else "0"
        resume.cell(row=numero, column=3, value=detail)
    _largeurs(resume, [38, 22, 60])

    # --- Feuille 2 : le classement des produits vendus ---
    produits = classeur.create_sheet("Produits vendus")
    _entete(produits, 1, [
        "Rang", "Code", "Désignation", "Quantité vendue",
        "Nombre de ventes", "Chiffre d'affaires (avant remise)",
    ])
    classement = donnees["classement"]
    for rang, ligne in enumerate(classement, start=1):
        produits.append([
            rang, ligne["code"], ligne["designation"],
            ligne["quantite"], ligne["nombre_ventes"], ligne["ca"],
        ])
        produits.cell(row=rang + 1, column=6).number_format = FORMAT_FCFA
    if classement:
        total = len(classement) + 2
        produits.cell(row=total, column=3, value="TOTAL").font = gras
        quantites = produits.cell(
            row=total, column=4, value=sum(l["quantite"] for l in classement)
        )
        quantites.font = gras
        montant = produits.cell(
            row=total, column=6, value=sum(l["ca"] for l in classement)
        )
        montant.font = gras
        montant.number_format = FORMAT_FCFA
    else:
        produits.cell(row=2, column=1, value="Aucune vente validée sur cette période.")
    produits.freeze_panes = "A2"
    _largeurs(produits, [8, 14, 36, 18, 18, 30])

    # --- Feuille 3 : les produits en stock critique ---
    critiques = classeur.create_sheet("Stock critique")
    _entete(critiques, 1, [
        "Code", "Désignation", "Catégorie", "Stock restant", "Seuil minimal",
    ])
    rouge = PatternFill("solid", fgColor=ROUGE_CLAIR)
    for numero, produit in enumerate(donnees["critiques"], start=2):
        critiques.append([
            produit.code, produit.designation, produit.categorie.nom_categorie,
            int(produit.stock), produit.seuil_minimal,
        ])
        for colonne in range(1, 6):
            critiques.cell(row=numero, column=colonne).fill = rouge
        critiques.cell(row=numero, column=4).font = Font(bold=True, color="B91C1C")
    if not donnees["critiques"]:
        critiques.cell(row=2, column=1, value="Aucun produit en stock critique.")
    critiques.freeze_panes = "A2"
    _largeurs(critiques, [14, 36, 24, 16, 16])

    sortie = BytesIO()
    classeur.save(sortie)
    return sortie.getvalue()


# ---------- Export PDF ----------
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

COULEUR_BARRE = colors.HexColor("#1E3A5F")
GRIS_CLAIR = colors.HexColor("#F3F4F6")
GRIS_BORD = colors.HexColor("#D1D5DB")
GRIS_TEXTE = colors.HexColor("#6B7280")
ROUGE_FOND = colors.HexColor("#FDE2E2")


def _style_tableau(colonnes_droite=(), colonnes_centre=()):
    """Les règles d'apparence communes à tous les tableaux du PDF."""
    commandes = [
        ("BACKGROUND", (0, 0), (-1, 0), COULEUR_BARRE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_BORD),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for colonne in colonnes_droite:
        commandes.append(("ALIGN", (colonne, 0), (colonne, -1), "RIGHT"))
    for colonne in colonnes_centre:
        commandes.append(("ALIGN", (colonne, 0), (colonne, -1), "CENTER"))
    return commandes


def _pied_de_page(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS_TEXTE)
    canvas.drawString(15 * mm, 8 * mm, "LogiStock SA - Tableau de bord")
    canvas.drawRightString(195 * mm, 8 * mm, f"Page {document.page}")
    canvas.restoreState()


def construire_pdf(donnees, utilisateur):
    """Fabrique le fichier PDF (format A4) et le renvoie en octets."""
    sortie = BytesIO()
    document = SimpleDocTemplate(
        sortie, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title="LogiStock SA - Tableau de bord", author="LogiStock SA",
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    titre = ParagraphStyle(
        "TitreLogi", parent=styles["Title"], alignment=0, fontSize=20,
        textColor=COULEUR_BARRE,
    )
    sous_titre = ParagraphStyle(
        "SousTitreLogi", parent=styles["Heading2"], textColor=COULEUR_BARRE,
        spaceBefore=14, spaceAfter=6,
    )
    petit = ParagraphStyle(
        "PetitLogi", parent=normal, fontSize=8, textColor=GRIS_TEXTE
    )
    cellule = ParagraphStyle("CelluleLogi", parent=normal, fontSize=9, leading=11)

    elements = [
        Paragraph("LogiStock SA - Tableau de bord", titre),
        Paragraph(
            f"Période : du {formater_date(donnees['debut'])} "
            f"au {formater_date(donnees['fin'])}",
            normal,
        ),
        Paragraph(
            f"Édité le {maintenant_texte()} par "
            f"{escape(nom_utilisateur(utilisateur))}",
            petit,
        ),
        Spacer(1, 4 * mm),
    ]

    # --- Les indicateurs ---
    elements.append(Paragraph("Indicateurs", sous_titre))
    lignes = [["Indicateur", "Valeur", "Détail"]]
    indicateurs = [
        ("Ventes du jour", formater_fcfa(donnees["jour"]["total"]),
         f"{donnees['jour']['nombre']} vente(s) validée(s) aujourd'hui"),
        ("Ventes du mois", formater_fcfa(donnees["mois"]["total"]),
         f"{donnees['mois']['nombre']} vente(s) validée(s) ce mois-ci"),
        ("Produits en stock critique", str(donnees["nb_critiques"]),
         "stock inférieur ou égal au seuil minimal"),
        ("Crédits à recouvrer", formater_fcfa(donnees["credits"]["total"]),
         f"{donnees['credits']['nombre']} client(s) avec une dette"),
        ("Chiffre d'affaires de la période",
         formater_fcfa(donnees["periode"]["total"]),
         f"{donnees['periode']['nombre']} vente(s) validée(s), "
         "ventes annulées exclues"),
    ]
    for nom, valeur, detail in indicateurs:
        lignes.append([nom, valeur, Paragraph(detail, cellule)])
    tableau = Table(lignes, colWidths=[58 * mm, 38 * mm, 84 * mm])
    tableau.setStyle(TableStyle(
        _style_tableau(colonnes_droite=(1,))
        + [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLAIR])]
    ))
    elements.append(tableau)

    # --- Les produits les plus vendus ---
    elements.append(Paragraph("Classement des produits vendus", sous_titre))
    classement = donnees["classement"]
    if classement:
        lignes = [[
            "Rang", "Code", "Désignation", "Quantité", "Ventes", "Chiffre d'affaires",
        ]]
        for rang, ligne in enumerate(classement, start=1):
            lignes.append([
                str(rang), ligne["code"],
                Paragraph(escape(ligne["designation"]), cellule),
                str(ligne["quantite"]), str(ligne["nombre_ventes"]),
                formater_fcfa(ligne["ca"]),
            ])
        lignes.append([
            "", "", "TOTAL", str(sum(l["quantite"] for l in classement)), "",
            formater_fcfa(sum(l["ca"] for l in classement)),
        ])
        tableau = Table(
            lignes,
            colWidths=[14 * mm, 24 * mm, 56 * mm, 22 * mm, 20 * mm, 44 * mm],
            repeatRows=1,
        )
        tableau.setStyle(TableStyle(
            _style_tableau(colonnes_droite=(5,), colonnes_centre=(0, 3, 4))
            + [
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIS_CLAIR]),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), GRIS_BORD),
            ]
        ))
        elements.append(tableau)
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            "Les montants par produit sont calculés avant remise "
            "(prix x quantité).", petit,
        ))
    else:
        elements.append(
            Paragraph("Aucune vente validée sur cette période.", normal)
        )

    # --- Les produits en stock critique ---
    elements.append(Paragraph("Produits en stock critique", sous_titre))
    if donnees["critiques"]:
        lignes = [["Code", "Désignation", "Catégorie", "Stock restant", "Seuil"]]
        for produit in donnees["critiques"]:
            lignes.append([
                produit.code,
                Paragraph(escape(produit.designation), cellule),
                Paragraph(escape(produit.categorie.nom_categorie), cellule),
                str(int(produit.stock)),
                str(produit.seuil_minimal),
            ])
        tableau = Table(
            lignes,
            colWidths=[24 * mm, 62 * mm, 44 * mm, 26 * mm, 24 * mm],
            repeatRows=1,
        )
        tableau.setStyle(TableStyle(
            _style_tableau(colonnes_centre=(3, 4))
            + [("BACKGROUND", (0, 1), (-1, -1), ROUGE_FOND)]
        ))
        elements.append(tableau)
    else:
        elements.append(Paragraph("Aucun produit en stock critique.", normal))

    document.build(
        elements, onFirstPage=_pied_de_page, onLaterPages=_pied_de_page
    )
    return sortie.getvalue()