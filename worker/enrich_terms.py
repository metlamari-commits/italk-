#!/usr/bin/env python3
"""
One-shot enrichment of data/terms.json with:
  - phonetics_ar : Arabic transliteration (BGN/PCGN-ish, simplified)
  - phonetics_fa : Farsi transliteration (UniPers-ish, simplified)
  - recommendation_el / recommendation_en : short field-action tip
  (urgency field was removed at Mari's request 2026-09-05 — this is a
   reference glossary, not a triage tool; the amber ΕΠΕΙΓΟΝ pill was
   noise for the browsing use case)

Run:  python worker/enrich_terms.py
Then git-diff to review, git-commit, git-push.
"""
import json, os, sys, io
from pathlib import Path

TERMS_PATH = Path(__file__).parent.parent / "data" / "terms.json"

# Curated first-pass enrichment for ~30 field-critical terms.
# Transliterations are approximations — Mari (a working interpreter) and
# the term-auditor subagent can refine over time. When unsure, we omit.
ENRICHMENT = {
    # ---- STATUS ----
    "asylum-seeker": {
        "phonetics_ar": "talib luju'",
        "phonetics_fa": "panahju",
    },
    "refugee": {
        "phonetics_ar": "laji'",
        "phonetics_fa": "panahandeh",
    },
    "subsidiary-protection": {
        "phonetics_ar": "al-himaya al-idafiyya",
        "phonetics_fa": "hemayat-e far'i",
    },
    "stateless": {
        "phonetics_ar": "'adim al-jinsiyya",
        "phonetics_fa": "bedun-e tabe'iyat",
    },
    "beneficiary-international-protection": {
        "phonetics_ar": "al-mustafid min al-himaya al-duwaliyya",
        "phonetics_fa": "darandeh-ye hemayat-e beynolmelali",
    },
    # ---- PROCEDURE ----
    "application-international-protection": {
        "phonetics_ar": "talab al-himaya al-duwaliyya",
        "phonetics_fa": "darkhast-e hemayat-e beynolmelali",
        "recommendation_el": "Καταγραφή με ακριβή ημερομηνία υποβολής — καθορίζει προθεσμίες.",
        "recommendation_en": "Record the exact submission date — it drives all downstream deadlines.",
    },
    "personal-interview": {
        "phonetics_ar": "muqabala shakhsiyya",
        "phonetics_fa": "mosahebe-ye shakhsi",
        "recommendation_el": "Ο διερμηνέας μιλά σε πρώτο πρόσωπο και δεν συνοψίζει — μεταφέρει κατά λέξη.",
        "recommendation_en": "Interpret in the first person; never summarise or add opinion.",
    },
    "dublin-transfer": {
        "phonetics_ar": "naql dublin",
        "phonetics_fa": "enteqal-e dublin",
    },
    "accelerated-procedure": {
        "phonetics_ar": "ijra' musarra'",
        "phonetics_fa": "ravand-e shetabi",
        "recommendation_el": "Προθεσμία προσφυγής πολύ σύντομη — ενημέρωση δικηγόρου άμεσα.",
        "recommendation_en": "Appeal window is very short — refer to legal aid immediately.",
    },
    "border-procedure": {
        "phonetics_ar": "ijra' 'ala al-hudud",
        "phonetics_fa": "ravand-e marzi",
    },
    "credibility-assessment": {
        "phonetics_ar": "taqyim al-masdaqiyya",
        "phonetics_fa": "arziyabi-ye e'tebar",
    },
    "benefit-of-the-doubt": {
        "phonetics_ar": "qarinat al-shakk",
        "phonetics_fa": "asl-e bara'at",
    },
    # ---- RECEPTION ----
    "registration": {
        "phonetics_ar": "tasjil",
        "phonetics_fa": "sabt-e nam",
    },
    "vulnerability-assessment": {
        "phonetics_ar": "taqyim al-hashasha",
        "phonetics_fa": "arziyabi-ye asibpaziri",
        "recommendation_el": "Αν εντοπίσεις ένδειξη ευαλωτότητας, καταγράφεται και ενεργοποιεί ειδικές εγγυήσεις.",
        "recommendation_en": "Flag any vulnerability signal — it unlocks special procedural guarantees.",
    },
    # ---- VULNERABLE ----
    "unaccompanied-minor": {
        "phonetics_ar": "qasir ghayr musahab",
        "phonetics_fa": "khordsal-e bi-hamrah",
        "recommendation_el": "Άμεση ειδοποίηση κοινωνικής υπηρεσίας & ορισμός επιτρόπου. Καμία απόφαση χωρίς επίτροπο.",
        "recommendation_en": "Notify social service immediately & appoint guardian. No decision without guardian.",
    },
    "vulnerable-person": {
        "phonetics_ar": "shakhs mustad'af",
        "phonetics_fa": "shakhs-e asibpazir",
    },
    "pregnant-woman": {
        "phonetics_ar": "imra'a hamil",
        "phonetics_fa": "zan-e bardar",
        "recommendation_el": "Ιατρικός έλεγχος προτεραιότητας. Αποφυγή πολύωρης αναμονής.",
        "recommendation_en": "Priority medical screening; avoid long waits.",
    },
    "survivor-gender-based-violence": {
        "phonetics_ar": "an-najiya min al-'unf al-qa'im 'ala al-naw' al-ijtima'i",
        "phonetics_fa": "bazmandeh-ye khoshunat-e jensiyati",
        "recommendation_el": "Trauma-informed προσέγγιση. Θηλυκή διερμηνέας αν διατίθεται. Χώρος με ιδιωτικότητα.",
        "recommendation_en": "Trauma-informed approach. Female interpreter if available. Private setting.",
    },
    "survivor-trafficking": {
        "phonetics_ar": "an-najiya min al-ittijar bi-l-bashar",
        "phonetics_fa": "bazmandeh-ye qacaq-e ensan",
        "recommendation_el": "Παραπομπή σε Εθνικό Μηχανισμό Αναφοράς (ΕΜΑ). Ενημέρωση για δικαιώματα προστασίας.",
        "recommendation_en": "Refer to National Referral Mechanism. Inform on protection rights.",
    },
    "person-with-disability": {
        "phonetics_ar": "shakhs dhu i'aqa",
        "phonetics_fa": "shakhs-e dara-ye ma'luliyat",
        "recommendation_el": "Έλεγχος προσβασιμότητας εγκαταστάσεων. Ειδικές ανάγκες επικοινωνίας (νοηματική/Braille κ.ά.).",
        "recommendation_en": "Check facility accessibility. Communication needs (sign language / Braille, etc.).",
    },
    "elderly-person": {
        "phonetics_ar": "shakhs musinn",
        "phonetics_fa": "shakhs-e salmand",
    },
    "best-interest-of-child": {
        "phonetics_ar": "al-maslaha al-fudla li-l-tifl",
        "phonetics_fa": "manafe'-e 'aliyeh-ye kudak",
        "recommendation_el": "Πρωταρχικό κριτήριο σε κάθε απόφαση για ανήλικο (Άρθρο 3 CRC).",
        "recommendation_en": "Primary consideration in every decision affecting a minor (CRC Art. 3).",
    },
    # ---- LEGAL ----
    "well-founded-fear": {
        "phonetics_ar": "khawf ma'qul",
        "phonetics_fa": "tars-e mavajah",
    },
    "persecution": {
        "phonetics_ar": "idtihad",
        "phonetics_fa": "az̄ar va shekanjeh",
    },
    "non-refoulement": {
        "phonetics_ar": "'adam al-i'ada al-qasriyya",
        "phonetics_fa": "'adam-e bazgardaneh-ye ejbari",
        "recommendation_el": "Θεμελιώδης αρχή — απαγορεύεται η επιστροφή σε χώρα κινδύνου. Άμεση παρέμβαση αν παραβιάζεται.",
        "recommendation_en": "Cornerstone principle — no return to a country of risk. Escalate immediately if breached.",
    },
    "family-reunification": {
        "phonetics_ar": "lamm shaml al-'a'ila",
        "phonetics_fa": "peyvand-e mojaddad-e khanevadeh",
        "recommendation_el": "Αίτηση συνήθως εντός 3 μηνών από αναγνώριση — έλεγχος προθεσμίας.",
        "recommendation_en": "Application usually within 3 months of recognition — check the deadline.",
    },
    "particular-social-group": {
        "phonetics_ar": "fi'a ijtima'iyya khassa",
        "phonetics_fa": "goruh-e ejtemai-ye khass",
    },
    # ---- MEDICAL ----
    "medical-screening": {
        "phonetics_ar": "fahs tibbi",
        "phonetics_fa": "moaine-ye peseshki",
    },
    "torture-survivor": {
        "phonetics_ar": "an-najiya min al-ta'dhib",
        "phonetics_fa": "bazmandeh-ye shekanjeh",
        "recommendation_el": "Παραπομπή σε εξειδικευμένη ιατρική/ψυχολογική υποστήριξη (π.χ. ΜΕΤΑδραση, Ιατρική Μέριμνα). Istanbul Protocol.",
        "recommendation_en": "Refer to specialised medical/psychological support (e.g. METAdrasi, Medical Care). Istanbul Protocol.",
    },
    "ptsd": {
        "phonetics_ar": "idtirab ma ba'd al-sadma",
        "phonetics_fa": "ekhtelal-e esteres-e pas az sanehe",
        "recommendation_el": "Παύσεις κατά τη συνέντευξη. Αποφυγή αναμνηστικών ερεθισμάτων. Ψυχολογική υποστήριξη.",
        "recommendation_en": "Interview breaks. Avoid triggering cues. Psychological support referral.",
    },
    "mental-health-assessment": {
        "phonetics_ar": "taqyim al-sihha al-nafsiyya",
        "phonetics_fa": "arziyabi-ye salamat-e ravan",
    },
    "referral": {
        "phonetics_ar": "ihala",
        "phonetics_fa": "erja'",
    },
    "amka": {
        "phonetics_ar": "raqm al-ta'min al-ijtima'i",
        "phonetics_fa": "shomareh-ye bimeh-ye ejtemai",
        "recommendation_el": "Απαραίτητο για πρόσβαση σε δημόσια υγεία & εμβολιασμούς. Χωρίς ΑΜΚΑ, μόνο επείγοντα.",
        "recommendation_en": "Required for public healthcare & vaccinations. Without AMKA, only emergency care.",
    },
    # ---- DETENTION ----
    "administrative-detention": {
        "phonetics_ar": "ihtijaz idari",
        "phonetics_fa": "bazdasht-e edari",
        "recommendation_el": "Δικαίωμα ενημέρωσης σε γλώσσα που καταλαβαίνει. Δικαίωμα προσφυγής. Νομική συνδρομή δωρεάν.",
        "recommendation_en": "Right to information in understood language. Right to appeal. Free legal aid.",
    },
    "right-to-information-detention": {
        "phonetics_ar": "haqq al-i'lam bi-l-ihtijaz",
        "phonetics_fa": "haqq-e ettelaresani darbareh-ye bazdasht",
        "recommendation_el": "Έντυπο δικαιωμάτων σε γλώσσα του κρατούμενου εντός εύλογου χρόνου.",
        "recommendation_en": "Rights notice in the detainee's language within a reasonable time.",
    },
    "detention-review": {
        "phonetics_ar": "muraja'at al-ihtijaz",
        "phonetics_fa": "baznegari-ye bazdasht",
    },
    "alternatives-to-detention": {
        "phonetics_ar": "bada'il al-ihtijaz",
        "phonetics_fa": "jaygozin-haye bazdasht",
    },
    # ---- RETURN ----
    "voluntary-return": {
        "phonetics_ar": "'awda tawa'iyya",
        "phonetics_fa": "bazgasht-e davtalabaneh",
    },
    "forced-return": {
        "phonetics_ar": "'awda qasriyya",
        "phonetics_fa": "bazgasht-e ejbari",
    },
    "removal-order": {
        "phonetics_ar": "amr al-ib'ad",
        "phonetics_fa": "hokm-e ekhraj",
        "recommendation_el": "Έλεγχος προθεσμίας προσφυγής. Έλεγχος non-refoulement.",
        "recommendation_en": "Check appeal deadline. Verify non-refoulement compliance.",
    },
    # ---- FAMILY ----
    "family-member": {
        "phonetics_ar": "fard al-'a'ila",
        "phonetics_fa": "'ozv-e khanevadeh",
    },
    "guardian": {
        "phonetics_ar": "wali / wasi",
        "phonetics_fa": "sarparast",
    },
    "age-assessment": {
        "phonetics_ar": "tahdid al-sinn",
        "phonetics_fa": "ta'yin-e senn",
        "recommendation_el": "Πολυδιάστατη προσέγγιση — όχι μόνο ιατρική εξέταση. Benefit of the doubt αν αμφιβολία.",
        "recommendation_en": "Multi-disciplinary approach — not only medical. Benefit of the doubt if uncertain.",
    },
    # ---- INTEGRATION ----
    "residence-permit": {
        "phonetics_ar": "tasrih al-iqama",
        "phonetics_fa": "ejaze-ye eqamat",
    },
    "afm-tax-number": {
        "phonetics_ar": "al-raqm al-daribi",
        "phonetics_fa": "shomareh-ye maliyati",
    },
    "naturalisation": {
        "phonetics_ar": "at-tajnis",
        "phonetics_fa": "tabe'iyat-pazyri",
    },
    # ---- COMMUNICATION ----
    "interpreter": {
        "phonetics_ar": "mutarjim shafahi",
        "phonetics_fa": "motarjem-e shafahi",
    },
    "consecutive-interpretation": {
        "phonetics_ar": "at-tarjama at-tatabu'iyya",
        "phonetics_fa": "tarjomeh-ye motavali",
    },
    "cultural-mediation": {
        "phonetics_ar": "wasata thaqafiyya",
        "phonetics_fa": "miyanjigari-ye farhangi",
    },
    "confidentiality-interpreter": {
        "phonetics_ar": "sirriyyat al-mutarjim",
        "phonetics_fa": "razdari-ye motarjem",
        "recommendation_el": "Καμία αποκάλυψη πληροφοριών εκτός συνέντευξης. Θεμελιώδης δεοντολογικός κανόνας.",
        "recommendation_en": "No disclosure of information outside the interview. Fundamental ethical rule.",
    },
    "impartiality-interpreter": {
        "phonetics_ar": "hiyad al-mutarjim",
        "phonetics_fa": "bitarafi-ye motarjem",
    },
    # ---- DOCUMENTATION ----
    "asylum-applicant-card": {
        "phonetics_ar": "bitaqat talib al-luju'",
        "phonetics_fa": "kart-e panahju",
    },
    "passport": {
        "phonetics_ar": "jawaz safar",
        "phonetics_fa": "gozarnameh",
    },
    "certified-translation": {
        "phonetics_ar": "tarjama musaddaqa",
        "phonetics_fa": "tarjomeh-ye rasmi",
    },
    # ---- PROCEDURE (appeal / legal aid) ----
    "appeal": {
        "phonetics_ar": "ta'n / isti'naf",
        "phonetics_fa": "tajdid-e nazar",
        "recommendation_el": "Πολύ αυστηρές προθεσμίες (συχνά 10 ή 30 μέρες). Έγκαιρη νομική συνδρομή.",
        "recommendation_en": "Strict deadlines (often 10 or 30 days). Get legal aid on time.",
    },
    "legal-aid": {
        "phonetics_ar": "al-musa'ada al-qanuniyya",
        "phonetics_fa": "komak-e hoquqi",
        "recommendation_el": "Δωρεάν σε β' βαθμό (προσφυγή) — αίτηση εγκαίρως στο Μητρώο Δικηγόρων.",
        "recommendation_en": "Free at appeal stage — apply on time via the Legal Aid Registry.",
    },

    # ========== SECOND PASS (2026-09-05) — remaining 54 AR/FA terms ==========
    # ---- STATUS (continued) ----
    "refugee-status-determination": {
        "phonetics_ar": "tahdid wad' al-laji'",
        "phonetics_fa": "ta'yin-e vaziyat-e panahandegi",
    },
    "internally-displaced-person": {
        "phonetics_ar": "nazih dakhili",
        "phonetics_fa": "avareh-ye dakheli",
    },
    "resettlement": {
        "phonetics_ar": "i'adat at-tawtin",
        "phonetics_fa": "esteqrar-e mojaddad",
    },
    "mandate-refugee": {
        "phonetics_ar": "laji' bi-mujib wilayat al-mufawwadiyya",
        "phonetics_fa": "panahandeh-ye tahat-e mandat",
    },
    "cessation-of-status": {
        "phonetics_ar": "inha' wad' al-laji'",
        "phonetics_fa": "khatm-e vaziyat-e panahandegi",
    },
    # ---- PROCEDURE (continued) ----
    "country-of-origin-information": {
        "phonetics_ar": "ma'lumat balad al-mansha'",
        "phonetics_fa": "ettelaat-e keshvar-e mabda",
    },
    "admissibility-procedure": {
        "phonetics_ar": "ijra' al-maqbuliyya",
        "phonetics_fa": "ravand-e paziresh",
    },
    "safe-country-of-origin": {
        "phonetics_ar": "balad al-mansha' al-amin",
        "phonetics_fa": "keshvar-e mabda-ye amn",
    },
    "safe-third-country": {
        "phonetics_ar": "balad thalith amin",
        "phonetics_fa": "keshvar-e sales-e amn",
    },
    "subsequent-application": {
        "phonetics_ar": "talab lahiq",
        "phonetics_fa": "darkhast-e ba'di",
    },
    # ---- RECEPTION (continued) ----
    "first-reception": {
        "phonetics_ar": "al-istiqbal al-awwali",
        "phonetics_fa": "paziresh-e avvaliyeh",
    },
    "screening": {
        "phonetics_ar": "al-farz",
        "phonetics_fa": "ghalbargari",
    },
    "reception-centre": {
        "phonetics_ar": "markaz al-istiqbal",
        "phonetics_fa": "markaz-e paziresh",
    },
    "ric": {
        "phonetics_ar": "markaz al-istiqbal wa-t-tahdid",
        "phonetics_fa": "markaz-e paziresh va shenasayi",
    },
    "closed-controlled-access-centre": {
        "phonetics_ar": "markaz al-wusul al-muraqab al-mughlaq",
        "phonetics_fa": "markaz-e dastresi-ye kontrol-shodeh-ye baste",
    },
    "biometric-data": {
        "phonetics_ar": "al-bayanat al-biyumitriyya",
        "phonetics_fa": "dade-haye biyometrik",
    },
    "frontex": {
        "phonetics_ar": "Frontex",
        "phonetics_fa": "Frontex",
    },
    "eurodac": {
        "phonetics_ar": "Eurodac",
        "phonetics_fa": "Eurodac",
    },
    # ---- LEGAL (continued) ----
    "acts-of-persecution": {
        "phonetics_ar": "a'mal al-idtihad",
        "phonetics_fa": "a'mal-e az̄ar",
    },
    "agents-of-persecution": {
        "phonetics_ar": "al-jihat al-murtakiba li-l-idtihad",
        "phonetics_fa": "amelan-e az̄ar",
    },
    "internal-protection-alternative": {
        "phonetics_ar": "badil al-himaya ad-dakhiliyya",
        "phonetics_fa": "jaygozin-e hemayat-e dakheli",
    },
    "sur-place-claim": {
        "phonetics_ar": "talab al-luju' fi al-mawqi'",
        "phonetics_fa": "darkhast-e panahandegi dar mahal",
    },
    "material-facts": {
        "phonetics_ar": "al-waqa'i' al-jawhariyya",
        "phonetics_fa": "haqayeq-e jouhari",
    },
    # ---- DETENTION (continued) ----
    "pre-removal-detention": {
        "phonetics_ar": "al-ihtijaz qabl at-tarhil",
        "phonetics_fa": "bazdasht-e pish az ekhraj",
    },
    "geographic-restriction": {
        "phonetics_ar": "at-taqyid al-jughrafi",
        "phonetics_fa": "mahdudiyat-e joghrafiyayi",
    },
    "deprivation-of-liberty": {
        "phonetics_ar": "al-hirman min al-hurriyya",
        "phonetics_fa": "mahrumiyat az azadi",
    },
    "maximum-detention-period": {
        "phonetics_ar": "al-hadd al-aqsa li-muddat al-ihtijaz",
        "phonetics_fa": "haddaksar-e moddat-e bazdasht",
    },
    "objections-against-detention": {
        "phonetics_ar": "i'tiradat 'ala al-ihtijaz",
        "phonetics_fa": "e'terazat 'aleyh-e bazdasht",
    },
    "dublin-detention": {
        "phonetics_ar": "al-ihtijaz bi-mujib la'ihat dublin",
        "phonetics_fa": "bazdasht bar asas-e dublin",
    },
    # ---- RETURN (continued) ----
    "re-entry-ban": {
        "phonetics_ar": "hazr i'adat ad-dukhul",
        "phonetics_fa": "man'-e bazgasht",
    },
    "avr": {
        "phonetics_ar": "al-'awda at-tawa'iyya al-musa'ada (AVR)",
        "phonetics_fa": "bazgasht-e davtalabaneh-ye komaki",
    },
    "readmission-agreement": {
        "phonetics_ar": "ittifaqiyyat i'adat al-qubul",
        "phonetics_fa": "movafeqat-nameh-ye paziresh-e mojaddad",
    },
    "period-for-voluntary-departure": {
        "phonetics_ar": "muhlat al-mughadara at-tawa'iyya",
        "phonetics_fa": "mohlat-e khoruj-e davtalabaneh",
    },
    "escorted-return": {
        "phonetics_ar": "al-'awda al-murafiqa",
        "phonetics_fa": "bazgasht-e badraghe-shodeh",
    },
    "joint-return-operation": {
        "phonetics_ar": "'amaliyyat 'awda mushtaraka",
        "phonetics_fa": "amaliyat-e bazgasht-e moshtarak",
    },
    "postponement-of-removal": {
        "phonetics_ar": "ta'jil al-ib'ad",
        "phonetics_fa": "ta'khir-e ekhraj",
    },
    # ---- FAMILY (continued) ----
    "family-unity": {
        "phonetics_ar": "wahdat al-'usra",
        "phonetics_fa": "vahdat-e khanevadeh",
    },
    "best-interest-assessment": {
        "phonetics_ar": "taqyim al-masalih al-fudla",
        "phonetics_fa": "arziyabi-ye manafe'-e 'aliyeh",
    },
    "sponsor": {
        "phonetics_ar": "al-kafil / sahib at-talab",
        "phonetics_fa": "kafil / darkhast-konandeh",
    },
    # ---- INTEGRATION (continued) ----
    "helios-programme": {
        "phonetics_ar": "barnamaj Helios",
        "phonetics_fa": "barnameh-ye Helios",
    },
    "recognition-of-qualifications": {
        "phonetics_ar": "al-i'tiraf bi-l-mu'ahhilat",
        "phonetics_fa": "be rasmiyat shenakhtan-e madarek",
    },
    "integration-course": {
        "phonetics_ar": "dawrat al-indimaj",
        "phonetics_fa": "dowreh-ye adghām",
    },
    # ---- COMMUNICATION (continued) ----
    "whisper-interpretation": {
        "phonetics_ar": "at-tarjama al-hamsiyya",
        "phonetics_fa": "tarjomeh-ye pech-pechi",
    },
    "simultaneous-interpretation": {
        "phonetics_ar": "at-tarjama al-fawriyya",
        "phonetics_fa": "tarjomeh-ye hamzaman",
    },
    "sight-translation": {
        "phonetics_ar": "at-tarjama al-manzura",
        "phonetics_fa": "tarjomeh-ye did-e-shodeh",
    },
    "relay-interpretation": {
        "phonetics_ar": "at-tarjama 'abr lugha wasita",
        "phonetics_fa": "tarjomeh-ye vasete-i",
    },
    "first-person-interpretation": {
        "phonetics_ar": "at-tarjama bi-sighat al-mutakallim",
        "phonetics_fa": "tarjomeh be-suret-e avval-shakhs",
    },
    # ---- DOCUMENTATION (continued) ----
    "travel-document": {
        "phonetics_ar": "wathiqat safar",
        "phonetics_fa": "sanad-e safar",
    },
    "birth-certificate": {
        "phonetics_ar": "shahadat al-milad",
        "phonetics_fa": "shenasnameh",
    },
    "identity-verification": {
        "phonetics_ar": "at-tahaqquq min al-hawiyya",
        "phonetics_fa": "ehraz-e hoviyat",
    },
    "refugee-travel-document": {
        "phonetics_ar": "wathiqat safar al-laji'",
        "phonetics_fa": "sanad-e safar-e panahandeh",
    },
    "paaypa": {
        "phonetics_ar": "PAAYPA",
        "phonetics_fa": "PAAYPA",
    },
    "apostille": {
        "phonetics_ar": "tasdiq Apostille",
        "phonetics_fa": "tasdiq-e Apostille",
    },
    "marriage-certificate": {
        "phonetics_ar": "shahadat az-zawaj",
        "phonetics_fa": "sanad-e ezdevaj",
    },
}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with open(TERMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    hit = 0
    miss = []
    for tid, extra in ENRICHMENT.items():
        found = False
        for t in data["terms"]:
            if t["id"] == tid:
                # Merge — but do not clobber if a manual field is already present
                for k, v in extra.items():
                    if k not in t or not t[k]:
                        t[k] = v
                found = True
                hit += 1
                break
        if not found:
            miss.append(tid)

    # bump meta
    data["meta"]["enriched"] = "2026-09-05"
    data["meta"]["enrichment_fields"] = ["phonetics_ar", "phonetics_fa", "recommendation_el", "recommendation_en"]

    with open(TERMS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Enriched {hit} / {len(ENRICHMENT)} terms")
    if miss:
        print("MISS (id not found in terms.json):")
        for m in miss:
            print("  -", m)

if __name__ == "__main__":
    main()
