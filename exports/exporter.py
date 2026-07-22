import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import pandas as pd


class Exporter:
    @staticmethod
    def _get_styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="TitleGreen", parent=styles["Title"],
                                  textColor=colors.HexColor("#1B5E20"), fontSize=16, alignment=TA_CENTER))
        return styles

    @staticmethod
    def _create_doc(filepath, title):
        return SimpleDocTemplate(filepath, pagesize=A4, leftMargin=40, rightMargin=40,
                                 topMargin=40, bottomMargin=40)

    @staticmethod
    def _make_table(data, headers):
        all_data = [headers] + data
        t = Table(all_data, repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#E8F5E9")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        t.setStyle(TableStyle(style))
        return t

    @staticmethod
    def export_budget_pdf_web(recettes, depenses, solde, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"budget_{timestamp}.pdf")
        styles = Exporter._get_styles()
        doc = Exporter._create_doc(filepath, "Budget")
        elements = []
        elements.append(Paragraph("Rapport Budget - FC VAINQUEUR", styles["TitleGreen"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Solde actuel : {solde:,.0f} FC", styles["Normal"]))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Recettes", styles["Heading2"]))
        if recettes:
            data = [[r.motif, f"{r.montant:,.0f} FC", r.responsable or "-", r.date_operation] for r in recettes]
            elements.append(Exporter._make_table(data, ["Motif", "Montant", "Responsable", "Date"]))
        else:
            elements.append(Paragraph("Aucune recette", styles["Normal"]))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Depenses", styles["Heading2"]))
        if depenses:
            data = [[d.motif, f"{d.montant:,.0f} FC", d.responsable or "-", d.date_operation] for d in depenses]
            elements.append(Exporter._make_table(data, ["Motif", "Montant", "Responsable", "Date"]))
        else:
            elements.append(Paragraph("Aucune depense", styles["Normal"]))
        doc.build(elements)
        return filepath

    @staticmethod
    def export_budget_excel_web(recettes, depenses, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"budget_{timestamp}.xlsx")
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            if recettes:
                df_r = pd.DataFrame([{"Motif": r.motif, "Montant": r.montant,
                                       "Responsable": r.responsable or "", "Date": r.date_operation}
                                      for r in recettes])
                df_r.to_excel(writer, sheet_name="Recettes", index=False)
            if depenses:
                df_d = pd.DataFrame([{"Motif": d.motif, "Montant": d.montant,
                                       "Responsable": d.responsable or "", "Date": d.date_operation}
                                      for d in depenses])
                df_d.to_excel(writer, sheet_name="Depenses", index=False)
            if not recettes and not depenses:
                pd.DataFrame([{"Info": "Aucune operation"}]).to_excel(
                    writer, sheet_name="Budget", index=False)
        return filepath

    @staticmethod
    def export_equipements_pdf_web(equipements, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"equipements_{timestamp}.pdf")
        styles = Exporter._get_styles()
        doc = Exporter._create_doc(filepath, "Equipements")
        elements = []
        elements.append(Paragraph("Liste des Equipements - FC VAINQUEUR", styles["TitleGreen"]))
        elements.append(Spacer(1, 15))
        if equipements:
            data = [[e.nom, e.categorie or "-", str(e.quantite),
                      f"{e.prix:,.0f} FC", e.etat or "-", e.fournisseur or "-"]
                     for e in equipements]
            elements.append(Exporter._make_table(data, ["Nom", "Categorie", "Qte", "Prix", "Etat", "Fournisseur"]))
        else:
            elements.append(Paragraph("Aucun equipement", styles["Normal"]))
        doc.build(elements)
        return filepath

    @staticmethod
    def export_equipements_excel_web(equipements, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"equipements_{timestamp}.xlsx")
        if equipements:
            df = pd.DataFrame([{"Nom": e.nom, "Categorie": e.categorie or "",
                                "Quantite": e.quantite, "Prix": e.prix,
                                "Etat": e.etat or "", "Fournisseur": e.fournisseur or ""}
                               for e in equipements])
            df.to_excel(filepath, index=False, sheet_name="Equipements")
        else:
            pd.DataFrame([{"Info": "Aucun equipement"}]).to_excel(
                filepath, index=False, sheet_name="Equipements")
        return filepath

    @staticmethod
    def export_joueurs_pdf_web(joueurs, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"joueurs_{timestamp}.pdf")
        styles = Exporter._get_styles()
        doc = Exporter._create_doc(filepath, "Joueurs")
        elements = []
        elements.append(Paragraph("Liste des Joueurs - FC VAINQUEUR", styles["TitleGreen"]))
        elements.append(Spacer(1, 15))
        if joueurs:
            data = [[j.prenom, j.nom, str(j.numero), j.poste or "-",
                      j.telephone or "-", j.email or "-"]
                     for j in joueurs]
            elements.append(Exporter._make_table(data, ["Prenom", "Nom", "Numero", "Poste", "Telephone", "Email"]))
        else:
            elements.append(Paragraph("Aucun joueur", styles["Normal"]))
        doc.build(elements)
        return filepath

    @staticmethod
    def export_joueurs_excel_web(joueurs, export_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_folder, f"joueurs_{timestamp}.xlsx")
        if joueurs:
            df = pd.DataFrame([{"Prenom": j.prenom, "Nom": j.nom, "Numero": j.numero,
                                "Poste": j.poste or "", "Telephone": j.telephone or "",
                                "Email": j.email or "", "Date naissance": j.date_naissance or ""}
                               for j in joueurs])
            df.to_excel(filepath, index=False, sheet_name="Joueurs")
        else:
            pd.DataFrame([{"Info": "Aucun joueur"}]).to_excel(
                filepath, index=False, sheet_name="Joueurs")
        return filepath
