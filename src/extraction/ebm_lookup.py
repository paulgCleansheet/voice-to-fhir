"""
EBM (Einheitlicher Bewertungsmassstab) Lookup Database.

German outpatient billing fee schedule. Follows the same pattern as
ops_lookup.py: static database + fuzzy match + enrichment.

Source: KBV EBM Q2 2026, parsed from PDF.
Subset: ~396 codes covering Hausarzt, common diagnostics,
lab, imaging, and Versichertenpauschalen across all specialties.

Flow:
    Service description -> normalize -> fuzzy match -> EBM code -> BillingCandidate
"""

import re
from difflib import SequenceMatcher
from typing import NamedTuple

from extraction.extraction_types import BillingCandidate, ClinicalEntities


class EBMCode(NamedTuple):
    """EBM code with metadata."""
    code: str          # "03000"
    display: str       # German description
    chapter: str       # "03"
    specialty: str     # "hausarzt"
    euro: float | None
    punkte: int | None


# =============================================================================
# EBM Database (~396 common outpatient codes)
# Generated from KBV EBM Q2 2026
# =============================================================================

EBM_DATABASE: dict[str, EBMCode] = {
    "01100": EBMCode("01100", "Unvorhergesehene Inanspruchnahme des Vertragsarztes durch einen Patienten", "01", "allgemein", 24.97, 196),
    "01101": EBMCode("01101", "Unvorhergesehene Inanspruchnahme des Vertragsarztes durch einen Patienten", "01", "allgemein", 39.88, 313),
    "01102": EBMCode("01102", "Inanspruchnahme des Vertragsarztes an Samstagen zwischen 07:00 und 19:00 Uhr", "01", "allgemein", 12.87, 101),
    "01205": EBMCode("01205", "Notfallpauschale im organisierten Not(-fall)dienst und für nicht an der vertr...", "01", "allgemein", 5.73, 45),
    "01207": EBMCode("01207", "Notfallpauschale im organisierten Not(-fall)dienst und für nicht an der vertr...", "01", "allgemein", 10.19, 80),
    "01210": EBMCode("01210", "Notfallpauschale I im organisierten Not(-fall)dienst und für nicht an der ver...", "01", "allgemein", 15.29, 120),
    "01212": EBMCode("01212", "Notfallpauschale II im organisierten Not(-fall)dienst und für nicht an der ve...", "01", "allgemein", 24.84, 195),
    "01214": EBMCode("01214", "Notfallkonsultationspauschale I im organisierten Not(-fall)dienst und für nic...", "01", "allgemein", 6.37, 50),
    "01216": EBMCode("01216", "Notfallkonsultationspauschale II im organisierten Not(-fall)dienst und für ni...", "01", "allgemein", 17.84, 140),
    "01218": EBMCode("01218", "Notfallkonsultationspauschale III im organisierten Not(-fall)dienst und für n...", "01", "allgemein", 21.66, 170),
    "01320": EBMCode("01320", "Grundpauschale für Ärzte, Institute und Krankenhäuser, die zur Erbringung von...", "01", "allgemein", 11.72, 92),
    "01321": EBMCode("01321", "Grundpauschale für Ärzte, Institute und Krankenhäuser, die zur Erbringung von...", "01", "allgemein", 20.26, 159),
    "01322": EBMCode("01322", "Zuschlag zu der Gebührenordnungsposition 01320 für die Behandlung aufgrund ei...", "01", "allgemein", None, None),
    "01323": EBMCode("01323", "Zuschlag zu der Gebührenordnungsposition 01321 für die Behandlung aufgrund ei...", "01", "allgemein", None, None),
    "01410": EBMCode("01410", "Besuch eines Kranken, wegen der Erkrankung ausgeführt", "01", "allgemein", 27.01, 212),
    "01411": EBMCode("01411", "Dringender Besuch wegen der Erkrankung, unverzüglich nach Bestellung ausgeführt", "01", "allgemein", 59.75, 469),
    "01412": EBMCode("01412", "Dringender Besuch / dringende Visite auf der Belegstation wegen der Erkrankun...", "01", "allgemein", 79.75, 626),
    "01413": EBMCode("01413", "Besuch eines weiteren Kranken in derselben sozialen Gemeinschaft (z. B. Famil...", "01", "allgemein", 13.5, 106),
    "01414": EBMCode("01414", "Visite auf der Belegstation, je Patient", "01", "allgemein", 11.08, 87),
    "01415": EBMCode("01415", "Dringender Besuch eines Patienten in beschützenden Wohnheimen bzw. Einrichtun...", "01", "allgemein", 69.56, 546),
    "01418": EBMCode("01418", "Besuch im organisierten Not(-fall)dienst", "01", "allgemein", 99.12, 778),
    "01420": EBMCode("01420", "Überprüfung der Notwendigkeit und Koordination der verordneten häuslichen Kra...", "01", "allgemein", 11.98, 94),
    "01422": EBMCode("01422", "Erstverordnung von Behandlungsmaßnahmen zur psychiatrischen häuslichen Kranke...", "01", "allgemein", 18.98, 149),
    "01424": EBMCode("01424", "Folgeverordnung von Behandlungsmaßnahmen zur psychiatrischen häuslichen Krank...", "01", "allgemein", 19.62, 154),
    "01425": EBMCode("01425", "Erstverordnung der spezialisierten ambulanten Palliativversorgung gemäß der R...", "01", "allgemein", 32.23, 253),
    "01426": EBMCode("01426", "Folgeverordnung zur Fortführung der spezialisierten ambulanten Palliativverso...", "01", "allgemein", 19.37, 152),
    "01430": EBMCode("01430", "Verwaltungskomplex", "01", "allgemein", 1.53, 12),
    "01431": EBMCode("01431", "Zusatzpauschale zu den Gebührenordnungspositionen 01430, 01435 und 01820 für ...", "01", "allgemein", 0.38, 3),
    "01435": EBMCode("01435", "Haus-/Fachärztliche Bereitschaftspauschale", "01", "allgemein", 11.21, 88),
    "01436": EBMCode("01436", "Konsultationspauschale", "01", "allgemein", 2.29, 18),
    "01440": EBMCode("01440", "Verweilen außerhalb der Praxis ohne Erbringung weiterer berechnungsfähiger Ge...", "01", "allgemein", 44.85, 352),
    "01450": EBMCode("01450", "Zuschlag im Zusammenhang mit den Versichertenpauschalen nach den Gebührenordn...", "01", "allgemein", 5.1, 40),
    "01452": EBMCode("01452", "Zuschlag zu den Versichertenpauschalen nach den Gebührenordnungspositionen 03...", "01", "allgemein", 3.82, 30),
    "01510": EBMCode("01510", "Dauer mehr als 2 Stunden", "01", "allgemein", 56.44, 443),
    "01511": EBMCode("01511", "Dauer mehr als 4 Stunden", "01", "allgemein", 111.1, 872),
    "01512": EBMCode("01512", "Dauer mehr als 6 Stunden", "01", "allgemein", 165.5, 1299),
    "01600": EBMCode("01600", "Ärztlicher Bericht über das Ergebnis einer Patientenuntersuchung", "01", "allgemein", 7.01, 55),
    "01601": EBMCode("01601", "Ärztlicher Brief in Form einer individuellen schriftlichen Information des Ar...", "01", "allgemein", 13.76, 108),
    "01602": EBMCode("01602", "Gebührenordnungsposition für die Mehrfertigung (z. B. Kopie) eines Berichtes ...", "01", "allgemein", 1.53, 12),
    "01610": EBMCode("01610", "Bescheinigung zur Feststellung der Belastungsgrenze (Muster 55)", "01", "allgemein", 1.78, 14),
    "01612": EBMCode("01612", "Konsiliarbericht eines Vertragsarztes vor Aufnahme einer Psychotherapie durch...", "01", "allgemein", 4.71, 37),
    "01620": EBMCode("01620", "Kurze Bescheinigung oder kurzes Zeugnis, nur auf besonderes Verlangen der Kra...", "01", "allgemein", 3.82, 30),
    "01621": EBMCode("01621", "Krankheitsbericht, nur auf besonderes Verlangen der Krankenkasse oder Ausstel...", "01", "allgemein", 5.61, 44),
    "01622": EBMCode("01622", "Ausführlicher schriftlicher Kurplan oder begründetes schriftliches Gutachten ...", "01", "allgemein", 10.57, 83),
    "01623": EBMCode("01623", "Kurvorschlag des Arztes zum Antrag auf ambulante Kur, Ausstellung des vereinb...", "01", "allgemein", 6.75, 53),
    "01700": EBMCode("01700", "Grundpauschale für Vertragsärzte, die zur Versorgung gemäß Kapitel 12 zugelas...", "01", "allgemein", 2.93, 23),
    "01701": EBMCode("01701", "Grundpauschale für Vertragsärzte, die zur Versorgung gemäß Kapitel 3 bis 11 o...", "01", "allgemein", 0.64, 5),
    "01702": EBMCode("01702", "Beratung im Rahmen des Pulsoxymetrie-Screenings gemäß Abschnitt C Kapitel V d...", "01", "allgemein", 3.57, 28),
    "01703": EBMCode("01703", "Pulsoxymetrie-Screening gemäß Abschnitt C Kapitel V der Kinder- Richtlinie de...", "01", "allgemein", 20.0, 157),
    "01704": EBMCode("01704", "Zuschlag für die Beratung im Rahmen des Neugeborenen- Hörscreenings gemäß Abs...", "01", "allgemein", 3.57, 28),
    "01731": EBMCode("01731", "Untersuchung zur Früherkennung von Krebserkrankungen beim Mann gemäß Abschnit...", "01", "allgemein", 18.35, 144),
    "01732": EBMCode("01732", "Gesundheitsuntersuchung bei Erwachsenen ab dem vollendeten 18. Lebensjahr gem...", "01", "allgemein", 41.53, 326),
    "01734": EBMCode("01734", "Zuschlag zur Gebührenordnungsposition 01732 für das Screening auf Hepatitis-B...", "01", "allgemein", 5.22, 41),
    "01740": EBMCode("01740", "Beratung zur Früherkennung des kolorektalen Karzinoms gemäß Teil II. § 5 der ...", "01", "allgemein", 14.78, 116),
    "01741": EBMCode("01741", "Koloskopischer Komplex gemäß Teil II. § 3 der Richtlinie für organisierte Kre...", "01", "allgemein", 224.87, 1765),
    "01742": EBMCode("01742", "Zuschlag zu der Gebührenordnungsposition 01741 - Polypektomie(n) von Polypen ...", "01", "allgemein", 33.0, 259),
    "01770": EBMCode("01770", "Betreuung einer Schwangeren gemäß der Richtlinie des Gemeinsamen Bundesaussch...", "01", "allgemein", 149.32, 1172),
    "01783": EBMCode("01783", "Quantitative Bestimmung von Alpha-1-Feto-Protein (AFP) im Fruchtwasser oder i...", "01", "allgemein", 7.13, 56),
    "01793": EBMCode("01793", "Pränatale zytogenetische Untersuchung(en) im Rahmen der Mutterschaftsvorsorge", "01", "allgemein", 670.91, 5266),
    "01796": EBMCode("01796", "Zuschlag zu der Gebührenordnungsposition 01794 für eine wissenschaftlich begr...", "01", "allgemein", 131.23, 1030),
    "01820": EBMCode("01820", "Ausstellung von Wiederholungsrezepten, Überweisungsscheinen oder Übermittlung...", "01", "allgemein", 1.4, 11),
    "01821": EBMCode("01821", "Beratung im Rahmen der Empfängnisregelung", "01", "allgemein", 9.05, 71),
    "01822": EBMCode("01822", "Beratung einschließlich Untersuchung im Rahmen der Empfängnisregelung", "01", "allgemein", 14.4, 113),
    "01823": EBMCode("01823", "Zuschlag zu den Gebührenordnungspositionen 01821 und", "01", "allgemein", 6.37, None),
    "01824": EBMCode("01824", "Veranlassung der Untersuchung der Urinprobe auf Chlamydia trachomatis nach de...", "01", "allgemein", 6.37, 50),
    "01950": EBMCode("01950", "Substitutionsgestützte Behandlung Opioidabhängiger gemäß Nr. 2 Anlage I \"Ane...", "01", "allgemein", 5.86, 46),
    "01951": EBMCode("01951", "Zuschlag zu den Gebührenordnungspositionen 01949 und 01950 für die Behandlung...", "01", "allgemein", 12.87, 101),
    "01955": EBMCode("01955", "Diamorphingestützte Behandlung Opioidabhängiger gemäß Nr. 2 Anlage I \"Anerka...", "01", "allgemein", 42.17, 331),
    "01956": EBMCode("01956", "Zuschlag zu der Gebührenordnungsposition 01955 für die Behandlung an Samstage...", "01", "allgemein", 25.86, 203),
    "02100": EBMCode("02100", "Infusion", "02", "allgemein", 8.54, 67),
    "02101": EBMCode("02101", "Infusionstherapie", "02", "allgemein", 21.02, 165),
    "02102": EBMCode("02102", "Infusionstherapie mit Sebelipase alfa oder Velmanase alfa oder Olipudase alfa...", "02", "allgemein", 21.02, 165),
    "02110": EBMCode("02110", "Erste Transfusion", "02", "allgemein", 23.19, 182),
    "02111": EBMCode("02111", "Jede weitere Transfusion im Anschluss an die Gebührenordnungsposition 02110", "02", "allgemein", 18.98, 149),
    "02112": EBMCode("02112", "Retransfusion", "02", "allgemein", 17.96, 141),
    "02200": EBMCode("02200", "Tuberkulintestung", "02", "allgemein", 1.15, 9),
    "02300": EBMCode("02300", "Kleinchirurgischer Eingriff I und/oder primäre Wundversorgung und/oder Epilation", "02", "allgemein", 8.66, 68),
    "02301": EBMCode("02301", "Kleinchirurgischer Eingriff II und/oder primäre Wundversorgung mittels Naht", "02", "allgemein", 16.94, 133),
    "02302": EBMCode("02302", "Kleinchirurgischer Eingriff III und/oder primäre Wundversorgung bei Säuglinge...", "02", "allgemein", 29.3, 230),
    "02310": EBMCode("02310", "Behandlung einer/eines/von sekundär heilenden Wunde(n) und/ oder Decubitalulc...", "02", "allgemein", 27.01, 212),
    "02311": EBMCode("02311", "Behandlung des diabetischen Fußes", "02", "allgemein", 17.58, 138),
    "02312": EBMCode("02312", "Behandlungskomplex eines oder mehrerer chronisch venösen/r Ulcus/Ulcera cruris", "02", "allgemein", 7.01, 55),
    "02313": EBMCode("02313", "Kompressionstherapie bei der chronisch venösen Insuffizienz, beim postthrombo...", "02", "allgemein", 6.37, 50),
    "02320": EBMCode("02320", "Einführung einer Magenverweilsonde", "02", "allgemein", 6.12, 48),
    "02321": EBMCode("02321", "Legen eines suprapubischen Harnblasenkatheters", "02", "allgemein", 15.93, 125),
    "02322": EBMCode("02322", "Wechsel oder Entfernung eines suprapubischen Harnblasenkatheters", "02", "allgemein", 6.75, 53),
    "02323": EBMCode("02323", "Legen und/oder Wechsel eines transurethralen Dauerkatheters", "02", "allgemein", 8.66, 68),
    "02330": EBMCode("02330", "Blutentnahme durch Arterienpunktion", "02", "allgemein", 6.24, 49),
    "02331": EBMCode("02331", "Intraarterielle Injektion", "02", "allgemein", 7.9, 62),
    "02340": EBMCode("02340", "Punktion I", "02", "allgemein", 5.73, 45),
    "02341": EBMCode("02341", "Punktion II", "02", "allgemein", 17.45, 137),
    "02342": EBMCode("02342", "Lumbalpunktion", "02", "allgemein", 74.15, 582),
    "02343": EBMCode("02343", "Entlastungspunktion des Pleuraraums und/oder nichtoperative Pleuradrainage", "02", "allgemein", 33.13, 260),
    "02400": EBMCode("02400", "Durchführung des ¹³C-Harnstoff-Atemtests ohne Analyse nach der Gebührenordnun...", "02", "allgemein", 2.93, 23),
    "02401": EBMCode("02401", "H2-Atemtest, einschl. Kosten", "02", "allgemein", 9.94, 78),
    "02500": EBMCode("02500", "Einzelinhalationstherapie", "02", "allgemein", 1.53, 12),
    "02501": EBMCode("02501", "Einzelinhalationstherapie mit speziellem Verneblersystem zur Pneumocystis car...", "02", "allgemein", 5.61, 44),
    "02510": EBMCode("02510", "Wärmetherapie", "02", "allgemein", 2.68, 21),
    "02511": EBMCode("02511", "Elektrotherapie unter Anwendung niederfrequenter und/oder mittelfrequenter St...", "02", "allgemein", 1.15, 9),
    "02512": EBMCode("02512", "Gezielte Elektrostimulation bei spastischen und/oder schlaffen Lähmungen", "02", "allgemein", 2.29, 18),
    "02520": EBMCode("02520", "Phototherapie eines Neugeborenen, je Behandlungstag", "02", "allgemein", 12.23, 96),
    "03000": EBMCode("03000", "Versichertenpauschale", "03", "hausarzt", None, None),
    "03001": EBMCode("03001", "Koordination der hausärztlichen Betreuung x", "03", "hausarzt", None, None),
    "03002": EBMCode("03002", "Koordination der hausärztlichen Betreuung eines Kranken x entspr. der Leistun...", "03", "hausarzt", None, None),
    "03005": EBMCode("03005", "Versorgungsbereichsspezifische Bereitschaft x", "03", "hausarzt", None, None),
    "03008": EBMCode("03008", "Zuschlag zu der Versichertenpauschale nach der Gebührenordnungsposition 03000...", "03", "hausarzt", 16.69, 131),
    "03010": EBMCode("03010", "Zuschlag zu der Gebührenordnungsposition 03000 für die Behandlung aufgrund ei...", "03", "hausarzt", None, None),
    "03020": EBMCode("03020", "Hygienezuschlag zu der Versichertenpauschale nach der Gebührenordnungspositio...", "03", "hausarzt", 0.25, 2),
    "03030": EBMCode("03030", "Versichertenpauschale bei unvorhergesehener Inanspruchnahme zwischen 19:00 un...", "03", "hausarzt", 9.81, 77),
    "03040": EBMCode("03040", "Zusatzpauschale zu den Gebührenordnungspositionen 03000 und", "03", "hausarzt", 16.31, None),
    "03041": EBMCode("03041", "bei Erfüllung von mindestens 2 und weniger als 8 Kriterien", "03", "hausarzt", 1.27, 10),
    "03042": EBMCode("03042", "bei Erfüllung von mindestens 8 Kriterien", "03", "hausarzt", 3.82, 30),
    "03060": EBMCode("03060", "Zuschlag zu der Gebührenordnungsposition 03040", "03", "hausarzt", 2.8, 22),
    "03061": EBMCode("03061", "Zuschlag zur Gebührenordnungsposition 03060, je Behandlungsfall gemäß Präambe...", "03", "hausarzt", 1.53, 12),
    "03062": EBMCode("03062", "Gebührenordnungsposition einschl. Wegekosten - entfernungsunabhängig - für är...", "03", "hausarzt", 21.15, 166),
    "03063": EBMCode("03063", "Gebührenordnungsposition einschl. Wegekosten - entfernungsunabhängig - für är...", "03", "hausarzt", 15.54, 122),
    "03064": EBMCode("03064", "Zuschlag zur Gebührenordnungsposition 03062", "03", "hausarzt", 2.55, 20),
    "03065": EBMCode("03065", "Zuschlag zur Gebührenordnungsposition 03063", "03", "hausarzt", 1.78, 14),
    "03110": EBMCode("03110", "Ordinationskomplex - Ordinationskomplex bis 5. Lebensjahr x", "03", "hausarzt", None, None),
    "03111": EBMCode("03111", "Ordinationskomplex - Ordinationskomplex 6.- 59. Lebensjahr x", "03", "hausarzt", None, None),
    "03112": EBMCode("03112", "Ordinationskomplex - Ordinationskomplex ab 60. Lebensjahr x", "03", "hausarzt", None, None),
    "03115": EBMCode("03115", "Konsultationskomplex x", "03", "hausarzt", None, None),
    "03120": EBMCode("03120", "Beratung, Erörterung, Abklärung x", "03", "hausarzt", None, None),
    "03210": EBMCode("03210", "Behandlung und Betreuung eines Patienten mit chronisch- x internistischer Gru...", "03", "hausarzt", None, None),
    "03211": EBMCode("03211", "Behandlung und Betreuung eines Patienten mit chronisch- x degenerativer und/o...", "03", "hausarzt", None, None),
    "03220": EBMCode("03220", "Zuschlag zu der Versichertenpauschale nach der Gebührenordnungsposition 03000...", "03", "hausarzt", 16.56, 130),
    "03221": EBMCode("03221", "Zuschlag zu der Gebührenordnungsposition 03220 für die intensive Behandlung u...", "03", "hausarzt", 5.1, 40),
    "03222": EBMCode("03222", "Zuschlag zu der Gebührenordnungsposition 03220, einmal im Behandlungsfall", "03", "hausarzt", 1.27, 10),
    "03230": EBMCode("03230", "Problemorientiertes ärztliches Gespräch, das aufgrund von Art und Schwere der...", "03", "hausarzt", 16.31, 128),
    "03241": EBMCode("03241", "Computergestützte Auswertung eines kontinuierlich aufgezeichneten Langzeit-EK...", "03", "hausarzt", 10.96, 86),
    "03242": EBMCode("03242", "Testverfahren bei Demenzverdacht", "03", "hausarzt", 2.93, 23),
    "03312": EBMCode("03312", "Klinisch-neurologische Basisdiagnostik x Spaltenbezeichnung VP GP SG Legende ...", "03", "hausarzt", None, None),
    "03313": EBMCode("03313", "Orientierende Erhebung des psychopathologischen Status x", "03", "hausarzt", None, None),
    "03321": EBMCode("03321", "Belastungs-Elektrokardiographie (Belastungs-EKG)", "03", "hausarzt", 25.23, 198),
    "03322": EBMCode("03322", "Aufzeichnung eines Langzeit-EKG von mindestens 18 Stunden Dauer", "03", "hausarzt", 6.12, 48),
    "03324": EBMCode("03324", "Langzeit-Blutdruckmessung", "03", "hausarzt", 7.26, 57),
    "03325": EBMCode("03325", "Indikationsstellung zur Überwachung eines Patienten im Rahmen des Telemonitor...", "03", "hausarzt", 8.28, 65),
    "03326": EBMCode("03326", "Zusatzpauschale für die Betreuung eines Patienten im Rahmen des Telemonitorin...", "03", "hausarzt", 16.31, 128),
    "03330": EBMCode("03330", "Spirographische Untersuchung", "03", "hausarzt", 6.75, 53),
    "03331": EBMCode("03331", "Prokto-/Rektoskopischer Untersuchungskomplex", "03", "hausarzt", 11.98, 94),
    "03335": EBMCode("03335", "Orientierende audiometrische Untersuchung nach vorausgegangener, dokumentiert...", "03", "hausarzt", 11.47, 90),
    "03340": EBMCode("03340", "Allergologische Basisdiagnostik x", "03", "hausarzt", None, None),
    "03350": EBMCode("03350", "Orientierende entwicklungsneurologische Untersuchung eines Neugeborenen, Säug...", "03", "hausarzt", 15.67, 123),
    "03351": EBMCode("03351", "Orientierende Untersuchung der Sprachentwicklung eines Säuglings, Kleinkindes...", "03", "hausarzt", 21.66, 170),
    "03352": EBMCode("03352", "Zuschlag zu den Gebührenordnungspositionen 01712 bis 01720 und", "03", "hausarzt", 9.68, None),
    "03355": EBMCode("03355", "Anleitung zur Selbstanwendung eines Real-Time-Messgerätes zur kontinuierliche...", "03", "hausarzt", 9.17, 72),
    "03360": EBMCode("03360", "Hausärztlich-geriatrisches Basisassessment", "03", "hausarzt", 14.4, 113),
    "03362": EBMCode("03362", "Hausärztlich-geriatrischer Betreuungskomplex", "03", "hausarzt", 22.17, 174),
    "03370": EBMCode("03370", "Palliativmedizinische Ersterhebung des Patientenstatus inkl. Behandlungsplan", "03", "hausarzt", 43.44, 341),
    "03371": EBMCode("03371", "Zuschlag zu der Versichertenpauschale 03000 für die palliativmedizinische Bet...", "03", "hausarzt", 20.26, 159),
    "03372": EBMCode("03372", "Zuschlag zu den Gebührenordnungspositionen 01410 oder 01413 für die palliativ...", "03", "hausarzt", 15.8, 124),
    "03373": EBMCode("03373", "Zuschlag zu den Gebührenordnungspositionen 01411, 01412 oder", "03", "hausarzt", 15.8, None),
    "04000": EBMCode("04000", "Versichertenpauschale", "04", "paediatrie", None, None),
    "04030": EBMCode("04030", "Versichertenpauschale bei unvorhergesehener Inanspruchnahme zwischen 19:00 un...", "04", "paediatrie", 9.81, 77),
    "04210": EBMCode("04210", "Behandlung und Betreuung eines Patienten mit chronisch- x internistischer Gru...", "04", "paediatrie", None, None),
    "04211": EBMCode("04211", "Behandlung und Betreuung eines Patienten mit chronisch- x degenerativer und/o...", "04", "paediatrie", None, None),
    "05210": EBMCode("05210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "05", "anaesthesie", 12.74, 100),
    "05211": EBMCode("05211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "05", "anaesthesie", 11.47, 90),
    "05212": EBMCode("05212", "für Versicherte ab Beginn des 60. Lebensjahres", "05", "anaesthesie", 13.38, 105),
    "06210": EBMCode("06210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "06", "augenheilkunde", 18.98, 149),
    "06211": EBMCode("06211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "06", "augenheilkunde", 14.91, 117),
    "06212": EBMCode("06212", "für Versicherte ab Beginn des 60. Lebensjahres", "06", "augenheilkunde", 17.33, 136),
    "07210": EBMCode("07210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "07", "chirurgie", 29.05, 228),
    "07211": EBMCode("07211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "07", "chirurgie", 29.43, 231),
    "07212": EBMCode("07212", "für Versicherte ab Beginn des 60. Lebensjahres", "07", "chirurgie", 34.02, 267),
    "08210": EBMCode("08210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "08", "gynaekologie", 14.4, 113),
    "08211": EBMCode("08211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "08", "gynaekologie", 18.73, 147),
    "08212": EBMCode("08212", "für Versicherte ab Beginn des 60. Lebensjahres", "08", "gynaekologie", 19.24, 151),
    "09210": EBMCode("09210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "09", "hno", 31.85, 250),
    "09211": EBMCode("09211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "09", "hno", 26.12, 205),
    "09212": EBMCode("09212", "für Versicherte ab Beginn des 60. Lebensjahres", "09", "hno", 26.88, 211),
    "10210": EBMCode("10210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "10", "dermatologie", 17.33, 136),
    "10211": EBMCode("10211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "10", "dermatologie", 18.22, 143),
    "10212": EBMCode("10212", "für Versicherte ab Beginn des 60. Lebensjahres", "10", "dermatologie", 18.73, 147),
    "11210": EBMCode("11210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "11", "humangenetik", 47.52, 373),
    "11211": EBMCode("11211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "11", "humangenetik", 53.0, 416),
    "11212": EBMCode("11212", "für Versicherte ab Beginn des 60. Lebensjahres", "11", "humangenetik", 49.81, 391),
    "12210": EBMCode("12210", "Konsiliarpauschale", "12", "labor", 10.19, 80),
    "13210": EBMCode("13210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "13", "innere_medizin", 15.42, 121),
    "13211": EBMCode("13211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "13", "innere_medizin", 23.44, 184),
    "13212": EBMCode("13212", "für Versicherte ab Beginn des 60. Lebensjahres", "13", "innere_medizin", 24.97, 196),
    "14210": EBMCode("14210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "14", "kjp", 23.06, 181),
    "14211": EBMCode("14211", "für Versicherte ab Beginn des 6. bis zum vollendeten 21. Lebensjahr", "14", "kjp", 23.57, 185),
    "15210": EBMCode("15210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "15", "mkg_chirurgie", 18.22, 143),
    "15211": EBMCode("15211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "15", "mkg_chirurgie", 16.44, 129),
    "15212": EBMCode("15212", "für Versicherte ab Beginn des 60. Lebensjahres", "15", "mkg_chirurgie", 15.42, 121),
    "16210": EBMCode("16210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "16", "neurologie", 24.97, 196),
    "16211": EBMCode("16211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "16", "neurologie", 23.44, 184),
    "16212": EBMCode("16212", "für Versicherte ab Beginn des 60. Lebensjahres", "16", "neurologie", 23.7, 186),
    "17210": EBMCode("17210", "Konsiliarpauschale", "17", "nuklearmedizin", 11.21, 88),
    "18210": EBMCode("18210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "18", "orthopaedie", 23.19, 182),
    "18211": EBMCode("18211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "18", "orthopaedie", 24.46, 192),
    "18212": EBMCode("18212", "für Versicherte ab Beginn des 60. Lebensjahres", "18", "orthopaedie", 28.28, 222),
    "19210": EBMCode("19210", "Konsiliarpauschale", "19", "pathologie", 8.15, 64),
    "20210": EBMCode("20210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "20", "phoniatrie", 38.09, 299),
    "20211": EBMCode("20211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "20", "phoniatrie", 25.74, 202),
    "20212": EBMCode("20212", "für Versicherte ab Beginn des 60. Lebensjahres", "20", "phoniatrie", 25.86, 203),
    "21210": EBMCode("21210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "21", "psychiatrie", 25.61, 201),
    "21211": EBMCode("21211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "21", "psychiatrie", 24.46, 192),
    "21212": EBMCode("21212", "für Versicherte ab Beginn des 60. Lebensjahres", "21", "psychiatrie", 24.33, 191),
    "22210": EBMCode("22210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "22", "psychosomatik", 17.07, 134),
    "22211": EBMCode("22211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "22", "psychosomatik", 22.3, 175),
    "22212": EBMCode("22212", "für Versicherte ab Beginn des 60. Lebensjahres", "22", "psychosomatik", 19.24, 151),
    "23210": EBMCode("23210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "23", "psychotherapie", 7.64, 60),
    "23211": EBMCode("23211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "23", "psychotherapie", 10.06, 79),
    "23212": EBMCode("23212", "für Versicherte ab Beginn des 60. Lebensjahres", "23", "psychotherapie", 9.3, 73),
    "24210": EBMCode("24210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "24", "radiologie", 9.3, 73),
    "24211": EBMCode("24211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "24", "radiologie", 7.77, 61),
    "24212": EBMCode("24212", "für Versicherte ab Beginn des 60. Lebensjahres", "24", "radiologie", 9.3, 73),
    "25210": EBMCode("25210", "Konsiliarpauschale bei gutartiger Erkrankung", "25", "strahlentherapie", 41.02, 322),
    "25211": EBMCode("25211", "Konsiliarpauschale bei bösartiger Erkrankung oder bei raumfordernden Prozesse...", "25", "strahlentherapie", 132.63, 1041),
    "26210": EBMCode("26210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "26", "urologie", 20.77, 163),
    "26211": EBMCode("26211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "26", "urologie", 21.66, 170),
    "26212": EBMCode("26212", "für Versicherte ab Beginn des 60. Lebensjahres", "26", "urologie", 25.48, 200),
    "27210": EBMCode("27210", "für Versicherte bis zum vollendeten 5. Lebensjahr", "27", "reha_medizin", 26.75, 210),
    "27211": EBMCode("27211", "für Versicherte ab Beginn des 6. bis zum vollendeten 59. Lebensjahr", "27", "reha_medizin", 29.81, 234),
    "27212": EBMCode("27212", "für Versicherte ab Beginn des 60. Lebensjahres", "27", "reha_medizin", 31.98, 251),
    "30210": EBMCode("30210", "Teilnahme an einer multidisziplinären Fallkonferenz zur Indikationsüberprüfun...", "30", "spezialversorgung", 10.96, 86),
    "30212": EBMCode("30212", "Indikationsüberprüfung eines Patienten mit diabetischem Fußsyndrom vor Überwe...", "30", "spezialversorgung", 43.7, 343),
    "31030": EBMCode("31030", "Zuschlag für zusätzlichen Hygieneaufwand zu der Gebührenordnungsposition 31121", "31", "ambulante_op", 15.93, 125),
    "31211": EBMCode("31211", "Eingriff der Kategorie L1", "31", "ambulante_op", 174.54, 1370),
    "31212": EBMCode("31212", "Eingriff der Kategorie L2", "31", "ambulante_op", 235.06, 1845),
    "32000": EBMCode("32000", "Laborgrundgebühr x x 2 Zuordnung der operativen Prozeduren nach § 295 SGB V (...", "32", "labor", None, None),
    "32025": EBMCode("32025", "Glucose", "32", "labor", 1.6, None),
    "32026": EBMCode("32026", "TPZ (Thromboplastinzeit)", "32", "labor", 4.7, None),
    "32027": EBMCode("32027", "D-Dimer (nicht mittels trägergebundener Reagenzien)", "32", "labor", 15.3, None),
    "32030": EBMCode("32030", "Orientierende Untersuchung", "32", "labor", 0.5, None),
    "32032": EBMCode("32032", "Bestimmung des pH-Wertes durch apparative Messung (außer im Harn)", "32", "labor", 0.25, None),
    "32035": EBMCode("32035", "Erythrozytenzählung", "32", "labor", 0.25, None),
    "32036": EBMCode("32036", "Leukozytenzählung", "32", "labor", 0.25, None),
    "32037": EBMCode("32037", "Thrombozytenzählung", "32", "labor", 0.25, None),
    "32038": EBMCode("32038", "Hämoglobin", "32", "labor", 0.25, None),
    "32039": EBMCode("32039", "Hämatokrit Werden in Akut- bzw. Notfällen Leistungen entsprechend der Gebühre...", "32", "labor", 0.25, None),
    "32041": EBMCode("32041", "Qualitativer immunologischer Nachweis von Albumin im Stuhl", "32", "labor", 1.6, None),
    "32042": EBMCode("32042", "Bestimmung der Blutkörperchensenkungsgeschwindigkeit 32.2.2 Mikroskopische Un...", "32", "labor", 0.25, None),
    "32045": EBMCode("32045", "Mikroskopische Untersuchung eines Körpermaterials", "32", "labor", 0.25, None),
    "32046": EBMCode("32046", "Fetal-Hämoglobin in Erythrozyten", "32", "labor", 0.4, None),
    "32047": EBMCode("32047", "Retikulozytenzählung", "32", "labor", 0.4, None),
    "32050": EBMCode("32050", "Mikroskopische Untersuchung eines Körpermaterials nach Gram- Färbung", "32", "labor", 0.4, None),
    "32051": EBMCode("32051", "Mikroskopische Differenzierung und Beurteilung aller korpuskulären Bestandtei...", "32", "labor", 0.4, None),
    "32052": EBMCode("32052", "Quantitative Bestimmung(en) der morphologischen Bestandteile durch Kammerzähl...", "32", "labor", 0.25, None),
    "32055": EBMCode("32055", "Quantitative Bestimmung eines Arzneimittels (z. B. Theophyllin, Antikonvulsiv...", "32", "labor", 1.99, None),
    "32056": EBMCode("32056", "Gesamteiweiß", "32", "labor", 0.25, None),
    "32057": EBMCode("32057", "Glukose", "32", "labor", 0.25, None),
    "32058": EBMCode("32058", "Bilirubin gesamt", "32", "labor", 0.25, None),
    "32060": EBMCode("32060", "Cholesterin gesamt", "32", "labor", 0.25, None),
    "32065": EBMCode("32065", "Harnstoff", "32", "labor", 0.25, None),
    "32066": EBMCode("32066", "Kreatinin (Jaffé-Methode)", "32", "labor", 0.25, None),
    "32067": EBMCode("32067", "Kreatinin, enzymatisch", "32", "labor", 0.4, None),
    "32070": EBMCode("32070", "GPT", "32", "labor", 0.25, None),
    "32071": EBMCode("32071", "Gamma-GT", "32", "labor", 0.25, None),
    "32073": EBMCode("32073", "Lipase", "32", "labor", 0.4, None),
    "32074": EBMCode("32074", "Creatinkinase (CK)", "32", "labor", 0.25, None),
    "32075": EBMCode("32075", "LDH", "32", "labor", 0.25, None),
    "32076": EBMCode("32076", "GLDH", "32", "labor", 0.4, None),
    "32080": EBMCode("32080", "Quantitative Bestimmung von Substraten, III / 2007 Enzymaktivitäten oder Elek...", "32", "labor", None, None),
    "32081": EBMCode("32081", "Kalium", "32", "labor", 0.25, None),
    "32082": EBMCode("32082", "Calcium", "32", "labor", 0.25, None),
    "32083": EBMCode("32083", "Natrium", "32", "labor", 0.25, None),
    "32085": EBMCode("32085", "Eisen", "32", "labor", 0.25, None),
    "32086": EBMCode("32086", "Phosphor anorganisch", "32", "labor", 0.4, None),
    "32089": EBMCode("32089", "Zuschlag zu den Gebührenordnungspositionen 32057, 32064, 32065 oder 32066 ode...", "32", "labor", 0.78, None),
    "32092": EBMCode("32092", "Quantitative Bestimmung CK-MB", "32", "labor", 1.12, None),
    "32094": EBMCode("32094", "Quantitative Bestimmung von HbA1c", "32", "labor", 2.67, None),
    "32097": EBMCode("32097", "Quantitative Bestimmung des/der natriuretischen Peptides/Peptide BNP und/oder...", "32", "labor", 11.9, None),
    "32100": EBMCode("32100", "Quantitative Bestimmung mittels Immunoassay, III / 2007 Indirekte Schilddrüse...", "32", "labor", None, None),
    "32101": EBMCode("32101", "Quantitative Bestimmung von Thyrotropin (TSH), je Untersuchung Quantitative i...", "32", "labor", 2.39, None),
    "32105": EBMCode("32105", "Immunglobulin M (Gesamt-IgM)", "32", "labor", 0.58, None),
    "32106": EBMCode("32106", "Transferrin", "32", "labor", 0.58, None),
    "32107": EBMCode("32107", "Elektrophoretische Trennung von Proteinen oder Lipoproteinen im Serum mit qua...", "32", "labor", 0.73, None),
    "32110": EBMCode("32110", "Blutungszeit (standardisiert)", "32", "labor", 0.73, None),
    "32112": EBMCode("32112", "Partielle Thromboplastinzeit (PTT)", "32", "labor", 0.58, None),
    "32113": EBMCode("32113", "Thromboplastinzeit (TPZ) aus Plasma", "32", "labor", 0.58, None),
    "32114": EBMCode("32114", "Thromboplastinzeit (TPZ) aus Kapillarblut", "32", "labor", 0.73, None),
    "32115": EBMCode("32115", "Thrombingerinnungszeit (TZ)", "32", "labor", 0.73, None),
    "32116": EBMCode("32116", "Fibrinogenbestimmung", "32", "labor", 0.73, None),
    "32117": EBMCode("32117", "Qualitativer Nachweis von Fibrinmonomeren, Fibrin- und/oder Fibrinogen-Spaltp...", "32", "labor", 4.46, None),
    "32120": EBMCode("32120", "Bestimmung von mindestens zwei der folgenden Parameter: Erythrozytenzahl, Leu...", "32", "labor", 0.5, None),
    "32122": EBMCode("32122", "Vollständiger Blutstatus mittels automatisierter Verfahren", "32", "labor", 1.07, None),
    "32125": EBMCode("32125", "Bestimmung von mindestens sechs der folgenden Parameter: Erythrozyten, Leukoz...", "32", "labor", 1.41, None),
    "32128": EBMCode("32128", "C-reaktives Protein", "32", "labor", 1.12, None),
    "32130": EBMCode("32130", "Streptolysin O-Antikörper (Antistreptolysin)", "32", "labor", 1.12, None),
    "32135": EBMCode("32135", "Mikroalbuminurie-Nachweis", "32", "labor", 1.55, None),
    "32150": EBMCode("32150", "Immunologischer Nachweis von Troponin I und/oder Troponin T auf einem vorgefe...", "32", "labor", 11.25, None),
    "32151": EBMCode("32151", "Kulturelle bakteriologische und/oder mykologische Untersuchung", "32", "labor", 1.12, None),
    "32155": EBMCode("32155", "Alkalische Leukozyten(Neutrophilen)phosphatase", "32", "labor", 13.16, None),
    "32210": EBMCode("32210", "Antithrombin III", "32", "labor", 10.49, None),
    "32211": EBMCode("32211", "Plasminogen", "32", "labor", 16.84, None),
    "32212": EBMCode("32212", "Fibrinmonomere, Fibrin- und/oder Fibrinogenspaltprodukte, z. B. D- Dimere", "32", "labor", 17.0, None),
    "33000": EBMCode("33000", "Ultraschalluntersuchung des Auges", "33", "ultraschall", 12.1, 95),
    "33001": EBMCode("33001", "Ultraschall-Biometrie des Auges", "33", "ultraschall", 6.24, 49),
    "33002": EBMCode("33002", "Messung der Hornhautdicke des Auges mittels Ultraschall- Pachymetrie", "33", "ultraschall", 6.75, 53),
    "33010": EBMCode("33010", "Sonographische Untersuchung der Nasennebenhöhlen mittels A- Mode- und/oder B-...", "33", "ultraschall", 6.75, 53),
    "33011": EBMCode("33011", "Sonographie der Gesichtsweichteile und/oder Halsweichteile und/ oder Speichel...", "33", "ultraschall", 10.06, 79),
    "33012": EBMCode("33012", "Sonographische Untersuchung der Schilddrüse mittels B-Mode- Verfahren,", "33", "ultraschall", 9.81, 77),
    "33020": EBMCode("33020", "Echokardiographische Untersuchung mittels M-Mode- und B- Mode-Verfahren,", "33", "ultraschall", 31.21, 245),
    "33021": EBMCode("33021", "Doppler-Echokardiographie mittels PW- und/oder CW-Doppler, je Sitzung", "33", "ultraschall", 34.4, 270),
    "33022": EBMCode("33022", "Doppler-Echokardiographie mittels Duplex-Verfahren mit Farbkodierung,", "33", "ultraschall", 39.11, 307),
    "33023": EBMCode("33023", "Zuschlag zu den Gebührenordnungspositionen 04410, 13545 sowie 33020 bis 33022...", "33", "ultraschall", 48.16, 378),
    "33030": EBMCode("33030", "Zweidimensionale echokardiographische Untersuchung in Ruhe und unter physikal...", "33", "ultraschall", 91.86, 721),
    "33031": EBMCode("33031", "Zweidimensionale echokardiographische Untersuchung in Ruhe und unter standard...", "33", "ultraschall", 102.82, 807),
    "33040": EBMCode("33040", "Sonographische Untersuchung der Thoraxorgane mittels B-Mode- Verfahren,", "33", "ultraschall", 14.01, 110),
    "33041": EBMCode("33041", "Sonographische Untersuchung einer oder beider Brustdrüsen mittels B- Mode-Ver...", "33", "ultraschall", 19.11, 150),
    "33042": EBMCode("33042", "Sonographische Untersuchung des Abdomens oder dessen Organe und/oder des Retr...", "33", "ultraschall", 18.22, 143),
    "33043": EBMCode("33043", "Sonographische Untersuchung eines oder mehrerer Uro-Genital- Organe mittels B...", "33", "ultraschall", 10.45, 82),
    "33044": EBMCode("33044", "Sonographische Untersuchung eines oder mehrerer weiblicher Genitalorgane, ggf...", "33", "ultraschall", 16.56, 130),
    "33046": EBMCode("33046", "Zuschlag zu den Gebührenordnungspositionen 33020 bis 33022, 33030, 33031 und ...", "33", "ultraschall", 9.68, 76),
    "33050": EBMCode("33050", "Sonographische Untersuchung von Gelenken und/oder umschriebenen Strukturen de...", "33", "ultraschall", 8.66, 68),
    "33051": EBMCode("33051", "Sonographische Untersuchung der Säuglingshüften mittels B-Mode- Verfahren,", "33", "ultraschall", 13.12, 103),
    "33052": EBMCode("33052", "Sonographische Untersuchung des Schädels durch die offene Fontanelle beim Neu...", "33", "ultraschall", 14.01, 110),
    "33053": EBMCode("33053", "Fraktursonographie bei Neugeborenen, Säuglingen, Kleinkindern und Kindern bis...", "33", "ultraschall", 13.12, 103),
    "33060": EBMCode("33060", "Sonographische Untersuchung extrakranieller hirnversorgender Gefäße, der Peri...", "33", "ultraschall", 34.02, 267),
    "33061": EBMCode("33061", "Sonographische Untersuchung der extremitätenver- und/oder entsorgenden Gefäße...", "33", "ultraschall", 11.47, 90),
    "33062": EBMCode("33062", "Sonographische Untersuchung der Gefäße des männlichen Genitalsystems mittels ...", "33", "ultraschall", 9.05, 71),
    "33063": EBMCode("33063", "Sonographische Untersuchung der intrakraniellen Gefäße mittels PW- Doppler-Ve...", "33", "ultraschall", 29.43, 231),
    "33064": EBMCode("33064", "Sonographische Untersuchung der Gefäße des männlichen Genitalsystems mittels ...", "33", "ultraschall", 11.59, 91),
    "33070": EBMCode("33070", "Sonographische Untersuchung der extrakraniellen hirnversorgenden Gefäße mitte...", "33", "ultraschall", 48.54, 381),
    "33071": EBMCode("33071", "Sonographische Untersuchung der intrakraniellen hirnversorgenden Gefäße mitte...", "33", "ultraschall", 27.26, 214),
    "33072": EBMCode("33072", "Sonographische Untersuchung der extremitätenver- und/oder entsorgenden Gefäße...", "33", "ultraschall", 28.54, 224),
    "33073": EBMCode("33073", "Sonographische Untersuchung der abdominellen und/oder retroperitonealen Gefäß...", "33", "ultraschall", 28.54, 224),
    "33074": EBMCode("33074", "Sonographische Untersuchung der Gefäße des weiblichen Genitalsystems mittels ...", "33", "ultraschall", 23.95, 188),
    "33075": EBMCode("33075", "Zuschlag zu den Gebührenordnungspositionen 33070 bis 33074 für die Durchführu...", "33", "ultraschall", 4.71, 37),
    "33076": EBMCode("33076", "Sonographische Untersuchung der Venen einer Extremität mittels B- Mode-Verfah...", "33", "ultraschall", 9.3, 73),
    "33080": EBMCode("33080", "Sonographische Untersuchung von Teilen der Haut und/oder Subkutis und/oder de...", "33", "ultraschall", 8.03, 63),
    "33081": EBMCode("33081", "Sonographische Untersuchung von Organen oder Organteilen bzw. Organstrukturen...", "33", "ultraschall", 7.13, 56),
    "33090": EBMCode("33090", "Zuschlag zu den Gebührenordnungspositionen 33040, 33042, 33043 und 33081 bei ...", "33", "ultraschall", 7.26, 57),
    "33091": EBMCode("33091", "Zuschlag zu den Gebührenordnungspositionen 33012, 33040, 33041 und 33081 für ...", "33", "ultraschall", 11.08, 87),
    "33092": EBMCode("33092", "Zuschlag zu den Gebührenordnungspositionen 33042, 33043 und", "33", "ultraschall", 15.03, None),
    "34210": EBMCode("34210", "Röntgenübersichtsaufnahmen des Schädels", "34", "radiologie", 13.12, 103),
    "34211": EBMCode("34211", "Panoramaschichtaufnahme(n) des Ober- und/oder Unterkiefers", "34", "radiologie", 9.05, 71),
    "34212": EBMCode("34212", "Röntgenaufnahme(n) der Halsorgane und/oder des Mundbodens", "34", "radiologie", 13.0, 102),
    "34220": EBMCode("34220", "Röntgenaufnahmen des knöchernen Thorax und/oder seiner Teile", "34", "radiologie", 11.59, 91),
    "34221": EBMCode("34221", "Röntgenaufnahmen von Teilen der Wirbelsäule", "34", "radiologie", 17.84, 140),
    "34222": EBMCode("34222", "Röntgenaufnahme(n) der gesamten Wirbelsäule", "34", "radiologie", 20.89, 164),
    "34223": EBMCode("34223", "Myelographie(n)", "34", "radiologie", 89.44, 702),
    "34230": EBMCode("34230", "Röntgenaufnahme von Teilen des Skeletts oder des Kopfes", "34", "radiologie", 9.43, 74),
    "34231": EBMCode("34231", "Röntgenaufnahmen und/oder Teilaufnahmen der Schulter und/oder des Schultergür...", "34", "radiologie", 17.45, 137),
    "34233": EBMCode("34233", "Röntgenaufnahmen der Extremitäten oder deren Teile mit Ausnahme der in der Ge...", "34", "radiologie", 12.61, 99),
    "34234": EBMCode("34234", "Röntgenaufnahme(n) des Beckens und/oder dessen Weichteile", "34", "radiologie", 9.05, 71),
    "34235": EBMCode("34235", "Röntgenkontrastuntersuchung eines Schulter-, Ellbogen-, Hüft- oder Kniegelenks", "34", "radiologie", 77.84, 611),
    "34236": EBMCode("34236", "Röntgenkontrastuntersuchung eines Gelenkes mit Ausnahme der in der Gebührenor...", "34", "radiologie", 65.49, 514),
    "34240": EBMCode("34240", "Röntgenübersichtsaufnahme(n) der Brustorgane", "34", "radiologie", 10.45, 82),
    "34241": EBMCode("34241", "Röntgenübersichtsaufnahmen der Brustorgane", "34", "radiologie", 18.6, 146),
    "34242": EBMCode("34242", "Röntgenübersichtsaufnahme(n) der Brustorgane einschließlich Durchleuchtung", "34", "radiologie", 33.89, 266),
    "34243": EBMCode("34243", "Röntgenübersichtsaufnahme(n) des Abdomens", "34", "radiologie", 11.85, 93),
    "34244": EBMCode("34244", "Röntgenübersichtsaufnahmen des Abdomens", "34", "radiologie", 17.96, 141),
    "34245": EBMCode("34245", "Röntgenaufnahme(n) von Teilen des Abdomens", "34", "radiologie", 13.5, 106),
    "34250": EBMCode("34250", "Röntgenuntersuchung der Gallenblase und/oder Gallengänge", "34", "radiologie", 50.71, 398),
    "34251": EBMCode("34251", "Röntgenkontrastuntersuchung des Dickdarms", "34", "radiologie", 111.99, 879),
    "34252": EBMCode("34252", "Röntgenkontrastuntersuchung des Dickdarms beim Neugeborenen, Säugling, Kleink...", "34", "radiologie", 94.28, 740),
    "34260": EBMCode("34260", "Röntgenuntersuchung natürlicher oder krankhaft entstandener Gangsysteme, Höhl...", "34", "radiologie", 46.25, 363),
    "34270": EBMCode("34270", "Mammographie", "34", "radiologie", 34.91, 274),
    "34271": EBMCode("34271", "Zuschlag zu der Gebührenordnungsposition 34270", "34", "radiologie", 110.71, 869),
    "34272": EBMCode("34272", "Mammateilaufnahme(n)", "34", "radiologie", 34.02, 267),
    "34273": EBMCode("34273", "Röntgenuntersuchung eines Mammapräparates", "34", "radiologie", 12.49, 98),
    "34274": EBMCode("34274", "Vakuumbiopsie(n) der Mamma im Zusammenhang mit der Erbringung der Gebührenord...", "34", "radiologie", 34.65, 272),
    "34275": EBMCode("34275", "Durchführung einer Mammographie in einer Ebene gemäß der Qualitätssicherungsv...", "34", "radiologie", 27.14, 213),
    "34280": EBMCode("34280", "Durchleuchtung(en)", "34", "radiologie", 12.1, 95),
    "34281": EBMCode("34281", "Durchleuchtungen zur weiteren diagnostischen Abklärung", "34", "radiologie", 7.9, 62),
    "34282": EBMCode("34282", "Schichtaufnahmen, je Strahlengang und Projektionsrichtung", "34", "radiologie", 47.39, 372),
    "34283": EBMCode("34283", "Serienangiographie", "34", "radiologie", 197.73, 1552),
    "34284": EBMCode("34284", "Zuschlag zu der Gebührenordnungsposition 34283 bei selektiver Darstellung hir...", "34", "radiologie", 125.11, 982),
    "34285": EBMCode("34285", "Zuschlag zu der Gebührenordnungsposition 34283 bei selektiver Darstellung and...", "34", "radiologie", 60.77, 477),
    "34290": EBMCode("34290", "Angiokardiographie", "34", "radiologie", 178.88, 1404),
    "34291": EBMCode("34291", "Herzkatheteruntersuchung mit Koronarangiographie", "34", "radiologie", 404.51, 3175),
    "34292": EBMCode("34292", "Zuschlag zu der Gebührenordnungsposition 34291 bei Durchführung einer interve...", "34", "radiologie", 484.01, 3799),
    "34310": EBMCode("34310", "CT-Untersuchung des Neurocraniums", "34", "radiologie", 68.03, 534),
    "34311": EBMCode("34311", "CT-Untersuchung von Teilen der Wirbelsäule", "34", "radiologie", 84.34, 662),
    "34320": EBMCode("34320", "CT-Untersuchung des Gesichtsschädels", "34", "radiologie", 82.81, 650),
    "34321": EBMCode("34321", "CT-Untersuchung der Schädelbasis", "34", "radiologie", 71.47, 561),
    "34322": EBMCode("34322", "CT-Untersuchung der Halsweichteile", "34", "radiologie", 86.25, 677),
    "34410": EBMCode("34410", "MRT-Untersuchung des Neurocraniums", "34", "radiologie", 134.16, 1053),
    "34411": EBMCode("34411", "MRT-Untersuchung von Teilen der Wirbelsäule", "34", "radiologie", 134.16, 1053),
    "34420": EBMCode("34420", "MRT-Untersuchung des Gesichtsschädels", "34", "radiologie", 134.16, 1053),
    "34421": EBMCode("34421", "MRT-Untersuchung der Schädelbasis", "34", "radiologie", 134.16, 1053),
    "34422": EBMCode("34422", "MRT-Untersuchung der Halsweichteile, HWK 1 bis HWK 7", "34", "radiologie", 134.16, 1053),
    "34430": EBMCode("34430", "MRT-Untersuchung des Thorax", "34", "radiologie", 134.16, 1053),
    "34431": EBMCode("34431", "MRT-Untersuchung(en) der weiblichen Brustdrüse gemäß der Kernspintomographie-...", "34", "radiologie", 255.7, 2007),
    "34440": EBMCode("34440", "MRT-Untersuchung des Oberbauches", "34", "radiologie", 134.16, 1053),
    "34441": EBMCode("34441", "MRT-Untersuchung des Abdomens", "34", "radiologie", 134.16, 1053),
    "34450": EBMCode("34450", "MRT-Untersuchung der Extremitäten und/oder deren Teile, mit Ausnahme der nach...", "34", "radiologie", 134.16, 1053),
    "34451": EBMCode("34451", "MRT-Untersuchung der Hand, des Fußes und/oder deren Teile", "34", "radiologie", 134.16, 1053),
    "34452": EBMCode("34452", "Zuschlag zu den Gebührenordnungspositionen 34410, 34411, 34420 bis 34422, 344...", "34", "radiologie", 48.41, 380),
    "34460": EBMCode("34460", "MRT-gesteuerte Untersuchung von Organabschnitten für die Bestrahlungsplanung ...", "34", "radiologie", 86.25, 677),
    "34470": EBMCode("34470", "MRT-Angiographie der Hirngefäße gemäß den Qualitätssicherungsvereinbarungen n...", "34", "radiologie", 88.16, 692),
    "34475": EBMCode("34475", "MRT-Angiographie der Halsgefäße gemäß den Qualitätssicherungsvereinbarungen n...", "34", "radiologie", 117.08, 919),
    "34480": EBMCode("34480", "MRT-Angiographie der thorakalen Aorta und ihrer Abgänge und/oder ihrer Äste (...", "34", "radiologie", 117.08, 919),
    "34500": EBMCode("34500", "Durchleuchtungsgestützte Intervention bei PTC", "34", "radiologie", 85.62, 672),
    "34501": EBMCode("34501", "Durchleuchtungsgestützte Intervention bei Anlage eines Ösophagus-Stent", "34", "radiologie", 114.03, 895),
    "34503": EBMCode("34503", "Bildwandlergestützte Intervention(en) an der Wirbelsäule", "34", "radiologie", 84.98, 667),
    "34504": EBMCode("34504", "CT-gesteuerte schmerztherapeutische Intervention(en) bei akutem und/oder chro...", "34", "radiologie", 123.33, 968),
    "34505": EBMCode("34505", "CT-gesteuerte Intervention(en)", "34", "radiologie", 123.33, 968),
    "36211": EBMCode("36211", "Eingriff der Kategorie L1", "36", "belegaerztlich", 84.72, 665),
    "36212": EBMCode("36212", "Eingriff der Kategorie L2", "36", "belegaerztlich", 130.33, 1023),
    "51030": EBMCode("51030", "Psychotherapeutisches Gespräch als Einzelbehandlung", "51", "asv", 19.62, 154),
    "61030": EBMCode("61030", "Tonsillotomie gemäß Kategorie N2", "61", "erprobung", 202.95, 1593),
}


# =============================================================================
# Synonym Mappings (German clinical terms to EBM codes)
# =============================================================================

EBM_SYNONYMS: dict[str, str] = {
    # Common Hausarzt consultation terms
    "versichertenpauschale": "03000",
    "hausarztpauschale": "03000",
    "grundpauschale hausarzt": "03000",
    "chronikerpauschale": "03212",
    "chronikerzuschlag": "03220",
    "gespraechsleistung": "03230",
    "geriatrisches assessment": "03360",
    "geriatrische betreuung": "03362",
    "palliativversorgung": "03370",
    "palliativpauschale": "03371",

    # Visit types
    "hausbesuch": "01410",
    "dringender besuch": "01411",
    "mitbesuch": "01413",
    "besuch altenheim": "01413",
    "besuch pflegeheim": "01413",
    "notfallbesuch": "01412",
    "nachtbesuch": "01412",
    "wochenendbesuch": "01102",
    "notfall": "01210",
    "notfallpauschale": "01210",
    "videosprechstunde": "01450",

    # Reports and letters
    "arztbrief": "01601",
    "arztbericht": "01600",
    "befundbericht": "01600",
    "ueberweisung": "01430",

    # Screenings
    "gesundheitsuntersuchung": "01732",
    "check-up": "01732",
    "checkup": "01732",
    "hautkrebsscreening": "01745",
    "krebsvorsorge": "01730",
    "jugendgesundheitsuntersuchung": "01700",
    "j1": "01700",
    "u-untersuchung": "01700",
    "vorsorge kind": "01700",
    "darmkrebsvorsorge": "01740",
    "stuhltest": "01740",

    # Common procedures
    "blutentnahme": "02330",
    "infusion": "02100",
    "injektion": "02100",
    "wundversorgung": "02300",
    "kleinchirurgie": "02300",
    "naht": "02302",
    "verband": "02310",
    "verbandwechsel": "02310",
    "katheter legen": "02340",
    "punktion": "02320",

    # Ultrasound
    "sonographie abdomen": "33042",
    "sono abdomen": "33042",
    "bauchultraschall": "33042",
    "sonographie schilddruese": "33012",
    "sono schilddruese": "33012",
    "echokardiographie": "33020",
    "herzecho": "33020",
    "echo": "33020",
    "doppler": "33060",
    "duplex": "33061",
    "carotis-doppler": "33060",

    # Radiology
    "roentgen thorax": "34241",
    "roentgen lunge": "34241",
    "thorax roentgen": "34241",
    "roentgen wirbelsaeule": "34220",
    "roentgen hand": "34230",
    "roentgen fuss": "34233",
    "roentgen knie": "34236",
    "roentgen schulter": "34231",
    "roentgen becken": "34234",
    "ct": "34310",
    "computertomographie": "34310",
    "mrt": "34410",
    "kernspintomographie": "34410",
    "magnetresonanztomographie": "34410",
    "ct schaedel": "34311",
    "kopf-ct": "34311",
    "mrt schaedel": "34411",
    "kopf-mrt": "34411",

    # Common lab tests
    "blutbild": "32035",
    "kleines blutbild": "32035",
    "grosses blutbild": "32051",
    "differentialblutbild": "32051",
    "crp": "32460",
    "blutzucker": "32025",
    "glucose": "32025",
    "hba1c": "32094",
    "kreatinin": "32066",
    "gfr": "32066",
    "leberwerte": "32068",
    "got": "32069",
    "gpt": "32068",
    "gamma-gt": "32071",
    "cholesterin": "32060",
    "triglyceride": "32063",
    "tsh": "32101",
    "schilddruese labor": "32101",
    "urinstatus": "32030",
    "urin": "32030",
    "bsg": "32042",
    "blutsenkung": "32042",
    "quickwert": "32113",
    "inr": "32113",
    "gerinnung": "32113",
    "psa": "32351",
    "eisenwerte": "32085",
    "ferritin": "32325",
    "vitamin d": "32413",
    "elektrolyte": "32081",
    "kalium": "32081",
    "natrium": "32083",

    # English terms for common services
    "consultation": "03000",
    "home visit": "01410",
    "urgent visit": "01411",
    "emergency": "01210",
    "blood draw": "02330",
    "wound care": "02300",
    "suture": "02302",
    "ultrasound": "33042",
    "chest x-ray": "34241",
    "cbc": "32035",
    "complete blood count": "32035",
    "metabolic panel": "32060",
    "urinalysis": "32030",
    "ecg": "03320",
    "ekg": "03320",
    "spirometry": "03330",
    "lung function": "03330",
}


def normalize_service(name: str) -> str:
    """Normalize a service/procedure name for matching."""
    if not name:
        return ""
    name = name.lower().strip()
    # Remove common prefixes
    prefixes = ["ambulante ", "ambulanter ", "diagnostische ", "therapeutische "]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    # Normalize German umlauts to ascii equivalents for matching
    name = name.replace("ae", "ae").replace("oe", "oe").replace("ue", "ue")
    # Remove punctuation and extra whitespace
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, s1, s2).ratio()


def find_ebm_code(name: str, threshold: float = 0.6) -> EBMCode | None:
    """
    Look up EBM code for a service description.

    Tries exact code match, then synonym resolution, then fuzzy matching
    against EBM_DATABASE display names.

    Returns:
        EBMCode if found above threshold, else None.
    """
    if not name:
        return None

    normalized = normalize_service(name)

    # 1. Direct code lookup (if input is a 5-digit code)
    if re.match(r"^\d{5}$", normalized):
        return EBM_DATABASE.get(normalized)

    # 2. Exact match in database keys
    if normalized in EBM_DATABASE:
        return EBM_DATABASE[normalized]

    # 3. Synonym resolution
    if normalized in EBM_SYNONYMS:
        code_key = EBM_SYNONYMS[normalized]
        return EBM_DATABASE.get(code_key)

    # 4. Fuzzy match against display names
    best_match: EBMCode | None = None
    best_score = 0.0

    for code_entry in EBM_DATABASE.values():
        display_norm = normalize_service(code_entry.display)
        score = similarity_score(normalized, display_norm)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = code_entry

    # Also check synonyms fuzzy
    for syn, code_key in EBM_SYNONYMS.items():
        score = similarity_score(normalized, syn)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = EBM_DATABASE.get(code_key)

    return best_match


def enrich_billing_candidates_with_ebm(entities: ClinicalEntities) -> ClinicalEntities:
    """
    Create EBM BillingCandidate entries from procedures and procedure_orders.

    For outpatient (ambulatory) encounters in the German GKV system.
    Iterates over procedures and orders, looks up EBM codes, and appends
    to entities.billing_candidates.
    """
    # Process completed procedures
    for proc in entities.procedures:
        ebm = find_ebm_code(proc.name)
        if ebm:
            candidate = BillingCandidate(
                name=proc.name,
                code=ebm.code,
                code_system="EBM",
                confidence=0.90,
                linked_diagnosis=None,
                reasoning=f"Matched procedure '{proc.name}' to EBM {ebm.code} ({ebm.display})",
                ops_chapter=ebm.chapter,
                ops_setting="outpatient",
            )
            entities.billing_candidates.append(candidate)

    # Process procedure orders
    for order in entities.procedure_orders:
        ebm = find_ebm_code(order.name)
        if ebm:
            linked_dx = None
            if order.linked_diagnosis and isinstance(order.linked_diagnosis, dict):
                linked_dx = order.linked_diagnosis.get("icd10")

            candidate = BillingCandidate(
                name=order.name,
                code=ebm.code,
                code_system="EBM",
                confidence=0.90,
                linked_diagnosis=linked_dx,
                reasoning=f"Matched order '{order.name}' to EBM {ebm.code} ({ebm.display})",
                ops_chapter=ebm.chapter,
                ops_setting="outpatient",
            )
            entities.billing_candidates.append(candidate)

    return entities
