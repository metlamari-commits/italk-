"""One-shot: append 20 IPSN psychosocial terms to data/terms.json.
Source: EUAA IPSN Tool https://ipsn.euaa.europa.eu/el/ipsn-tool (2026-09-11).
Category: medical (matches existing PTSD/depression/psychosis entries).
"""
import json
from pathlib import Path

TERMS_PATH = Path(__file__).parent.parent / "data" / "terms.json"
SOURCE = "EUAA IPSN Tool — https://ipsn.euaa.europa.eu/el/ipsn-tool (accessed 2026-09-11); AR/FA/FR drafted, need native review"

NEW_TERMS = [
    {
        "id": "impulsive-behavior",
        "translations": {
            "el": "παρορμητική συμπεριφορά",
            "en": "impulsive behavior",
            "ar": "سلوك اندفاعي",
            "fa": "رفتار تکانشی",
            "fr": "comportement impulsif",
        },
        "definition_el": "Πράξεις που εκτελούνται χωρίς προηγούμενη σκέψη ή αυτοέλεγχο· συμπεριφορικός δείκτης ψυχολογικής δυσφορίας κατά το εργαλείο IPSN της EUAA.",
        "definition_en": "Actions performed without prior deliberation or self-control; a behavioural indicator of psychological distress under the EUAA IPSN screening tool.",
    },
    {
        "id": "bizarre-behavior",
        "translations": {
            "el": "ασυνήθης ή αλλοπρόσαλλη συμπεριφορά",
            "en": "unusual or bizarre behavior",
            "ar": "سلوك غير عادي أو غريب",
            "fa": "رفتار غیرعادی یا عجیب",
            "fr": "comportement inhabituel ou bizarre",
        },
        "definition_el": "Κοινωνικά ασυνήθεις πράξεις που υποδηλώνουν πιθανή ψυχολογική δυσφορία και χρήζουν περαιτέρω αξιολόγησης.",
        "definition_en": "Socially atypical actions suggesting possible psychological distress and warranting further assessment.",
    },
    {
        "id": "dangerous-behavior",
        "translations": {
            "el": "επικίνδυνη συμπεριφορά",
            "en": "dangerous behavior",
            "ar": "سلوك خطير",
            "fa": "رفتار خطرناک",
            "fr": "comportement dangereux",
        },
        "definition_el": "Πράξεις που θέτουν σε κίνδυνο τον ίδιο τον αιτούντα ή τρίτους· απαιτούν άμεση παραπομπή σε εξειδικευμένη υπηρεσία.",
        "definition_en": "Actions posing a risk to the applicant themselves or to others; require immediate referral to specialised support.",
    },
    {
        "id": "self-harm-tendencies",
        "translations": {
            "el": "τάσεις αυτοτραυματισμού",
            "en": "self-harm tendencies",
            "ar": "ميول لإيذاء النفس",
            "fa": "گرایش به خودآزاری",
            "fr": "tendances à l'automutilation",
        },
        "definition_el": "Παρατηρούμενη τάση για εθελούσια πρόκληση σωματικής βλάβης στον εαυτό, χωρίς απαραίτητα να έχει εκδηλωθεί πράξη αυτοτραυματισμού· δείκτης ρίσκου κατά την IPSN.",
        "definition_en": "Observed inclination toward deliberate self-injury, not necessarily involving completed self-harm acts; a risk indicator under the IPSN tool.",
    },
    {
        "id": "substance-abuse",
        "translations": {
            "el": "κατάχρηση ουσιών",
            "en": "substance abuse",
            "ar": "تعاطي المخدرات",
            "fa": "سوءمصرف مواد",
            "fr": "abus de substances",
        },
        "definition_el": "Βλαπτική χρήση ναρκωτικών ουσιών ή αλκοόλ χωρίς απαραίτητα να έχει εγκατασταθεί εξάρτηση· διακρίνεται από τον εθισμό.",
        "definition_en": "Harmful use of drugs or alcohol without necessarily meeting the criteria for dependence; distinct from addiction.",
    },
    {
        "id": "apathy",
        "translations": {
            "el": "απάθεια",
            "en": "apathy",
            "ar": "اللامبالاة",
            "fa": "بی‌تفاوتی",
            "fr": "apathie",
        },
        "definition_el": "Απουσία συναισθήματος, ενδιαφέροντος ή κινήτρου· συχνά συνοδεύει κατάθλιψη ή τραυματικές εμπειρίες.",
        "definition_en": "Absence of emotion, interest, or motivation; frequently observed alongside depression or trauma exposure.",
    },
    {
        "id": "phobia",
        "translations": {
            "el": "φοβία",
            "en": "phobia",
            "ar": "رهاب",
            "fa": "هراس",
            "fr": "phobie",
        },
        "definition_el": "Έντονος, μη ορθολογικός φόβος που προκαλείται από συγκεκριμένο ερέθισμα ή κατάσταση και οδηγεί σε αποφυγή.",
        "definition_en": "Intense, irrational fear triggered by a specific stimulus or situation, leading to avoidance behaviour.",
    },
    {
        "id": "depressive-mood",
        "translations": {
            "el": "καταθλιπτική διάθεση",
            "en": "depressive mood",
            "ar": "مزاج اكتئابي",
            "fa": "خلق افسرده",
            "fr": "humeur dépressive",
        },
        "definition_el": "Επίμονη θλίψη που επηρεάζει τη λειτουργικότητα· συμπτωματολογικός δείκτης, όχι απαραίτητα κλινική διάγνωση κατάθλιψης.",
        "definition_en": "Pervasive sadness affecting daily functioning; a symptomatic indicator rather than a clinical diagnosis of depression.",
    },
    {
        "id": "suicidal-and-self-destructive-thoughts",
        "translations": {
            "el": "πεισιθάνατες και αυτοκαταστροφικές σκέψεις",
            "en": "suicidal and self-destructive thoughts",
            "ar": "أفكار انتحارية وتدميرية للذات",
            "fa": "افکار خودکشی و خودتخریبی",
            "fr": "pensées suicidaires et autodestructrices",
        },
        "definition_el": "Σκέψεις που αφορούν πρόκληση βλάβης στον εαυτό, από γενική αυτοκαταστροφική ιδεοληψία έως συγκεκριμένο σχεδιασμό αυτοκτονίας.",
        "definition_en": "Ideation regarding harm to oneself, ranging from general self-destructive thinking to specific suicidal planning.",
    },
    {
        "id": "sleep-disturbances",
        "translations": {
            "el": "διαταραχές ύπνου",
            "en": "sleep disturbances",
            "ar": "اضطرابات النوم",
            "fa": "اختلالات خواب",
            "fr": "troubles du sommeil",
        },
        "definition_el": "Επίμονα διαταραγμένα πρότυπα ύπνου (αϋπνία, εφιάλτες, αποσπασματικός ύπνος)· κοινός δείκτης ψυχολογικής δυσφορίας.",
        "definition_en": "Persistent disruption of sleep patterns (insomnia, nightmares, fragmented sleep); a common indicator of psychological distress.",
    },
    {
        "id": "confusion-and-disorientation",
        "translations": {
            "el": "σύγχυση και αποπροσανατολισμός",
            "en": "confusion and disorientation",
            "ar": "التشوش والارتباك",
            "fa": "سردرگمی و گم‌گشتگی",
            "fr": "confusion et désorientation",
        },
        "definition_el": "Γνωσιακή δυσλειτουργία που επηρεάζει την επίγνωση χρόνου, τόπου ή προσώπου· χρήζει άμεσης ιατρικής και ψυχιατρικής εκτίμησης.",
        "definition_en": "Cognitive impairment affecting awareness of time, place, or identity; warrants prompt medical and psychiatric evaluation.",
    },
    {
        "id": "concentration-difficulties",
        "translations": {
            "el": "δυσκολία συγκέντρωσης",
            "en": "concentration difficulties",
            "ar": "صعوبات في التركيز",
            "fa": "مشکلات تمرکز",
            "fr": "difficultés de concentration",
        },
        "definition_el": "Δυσκολία στη διατήρηση της προσοχής· συχνός δείκτης PTSD, κατάθλιψης ή άγχους.",
        "definition_en": "Difficulty sustaining attention; a common indicator of PTSD, depression, or anxiety.",
    },
    {
        "id": "avoidance-of-trauma-stimuli",
        "translations": {
            "el": "αποφυγή ερεθισμάτων που θυμίζουν το τραύμα",
            "en": "avoidance of trauma-related stimuli",
            "ar": "تجنب المحفزات المرتبطة بالصدمة",
            "fa": "اجتناب از محرک‌های مرتبط با تروما",
            "fr": "évitement des stimuli liés au traumatisme",
        },
        "definition_el": "Εκούσια αποφυγή σκέψεων, τόπων, ανθρώπων ή δραστηριοτήτων που θυμίζουν το τραυματικό γεγονός· κύριο διαγνωστικό κριτήριο PTSD.",
        "definition_en": "Deliberate avoidance of thoughts, places, people, or activities that recall a traumatic event; a core PTSD diagnostic criterion.",
    },
    {
        "id": "personality-change",
        "translations": {
            "el": "αλλαγή προσωπικότητας",
            "en": "personality change",
            "ar": "تغير في الشخصية",
            "fa": "تغییر شخصیت",
            "fr": "changement de personnalité",
        },
        "definition_el": "Θεμελιώδης μεταβολή στον χαρακτήρα ή στη συμπεριφορά σε σχέση με την προτραυματική βάση του ατόμου· δείκτης πιθανής σοβαρής ψυχικής δυσλειτουργίας.",
        "definition_en": "Fundamental shift in a person's character or behaviour relative to their pre-trauma baseline; an indicator of possible severe psychological disturbance.",
    },
    {
        "id": "feeling-of-guilt",
        "translations": {
            "el": "αίσθημα ενοχής",
            "en": "feeling of guilt",
            "ar": "الشعور بالذنب",
            "fa": "احساس گناه",
            "fr": "sentiment de culpabilité",
        },
        "definition_el": "Αυτοενοχοποίηση για παρελθόντα γεγονότα, συχνά δυσανάλογη προς την πραγματική ευθύνη· συχνή σε επιζώντες τραυματικών εμπειριών και σε PTSD.",
        "definition_en": "Self-blame regarding past events, often disproportionate to actual responsibility; commonly seen in trauma survivors and in PTSD.",
    },
    {
        "id": "feeling-of-shame",
        "translations": {
            "el": "αίσθημα ντροπής",
            "en": "feeling of shame",
            "ar": "الشعور بالخجل",
            "fa": "احساس شرم",
            "fr": "sentiment de honte",
        },
        "definition_el": "Έντονη αμηχανία ή δυσφορία για την προσωπική κατάσταση, συχνά συνδεδεμένη με σεξουαλική βία, βασανιστήρια ή στιγματισμό.",
        "definition_en": "Intense embarrassment or distress regarding one's circumstances, often linked to sexual violence, torture, or stigmatisation.",
    },
    {
        "id": "hopelessness",
        "translations": {
            "el": "απόγνωση",
            "en": "hopelessness",
            "ar": "اليأس",
            "fa": "ناامیدی",
            "fr": "désespoir",
        },
        "definition_el": "Πεποίθηση ότι η κατάσταση δεν πρόκειται να βελτιωθεί· ισχυρός δείκτης ρίσκου αυτοκτονίας.",
        "definition_en": "Belief that one's situation cannot improve; a strong risk indicator for suicide.",
    },
    {
        "id": "feeling-of-worthlessness",
        "translations": {
            "el": "αίσθημα αναξιότητας",
            "en": "feeling of worthlessness",
            "ar": "الشعور بعدم القيمة",
            "fa": "احساس بی‌ارزشی",
            "fr": "sentiment de dévalorisation",
        },
        "definition_el": "Μειωμένη αυτοεκτίμηση και πεποίθηση ότι κανείς δεν έχει αξία ως άτομο· χαρακτηριστικό της κατάθλιψης.",
        "definition_en": "Diminished self-worth and belief that one has no personal value; characteristic of depression.",
    },
    {
        "id": "severe-self-esteem-erosion",
        "translations": {
            "el": "σοβαρός κλονισμός της αυτοεκτίμησης",
            "en": "severe self-esteem erosion",
            "ar": "تدهور شديد في تقدير الذات",
            "fa": "تخریب شدید عزت نفس",
            "fr": "érosion sévère de l'estime de soi",
        },
        "definition_el": "Βαθιά απώλεια εμπιστοσύνης στην προσωπική αξία, συχνά ως συνέπεια παρατεταμένης θυματοποίησης, βασανιστηρίων ή βίας.",
        "definition_en": "Profound loss of confidence in personal worth, often as a consequence of prolonged victimisation, torture, or violence.",
    },
    {
        "id": "anxiety-disorder",
        "translations": {
            "el": "διαταραχή άγχους",
            "en": "anxiety disorder",
            "ar": "اضطراب القلق",
            "fa": "اختلال اضطرابی",
            "fr": "trouble anxieux",
        },
        "definition_el": "Κλινική διάγνωση χαρακτηριζόμενη από χρόνιο υπέρμετρο άγχος και ανησυχία· διακρίνεται από την επεισοδιακή «κρίση άγχους».",
        "definition_en": "A clinical diagnosis characterised by chronic excessive worry and nervousness; distinct from an episodic anxiety attack.",
    },
]


def main() -> None:
    data = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
    existing_ids = {t["id"] for t in data["terms"]}

    added = 0
    for term in NEW_TERMS:
        if term["id"] in existing_ids:
            print(f"skip (exists): {term['id']}")
            continue
        entry = {
            "id": term["id"],
            "category": "medical",
            "translations": term["translations"],
            "definition_el": term["definition_el"],
            "definition_en": term["definition_en"],
            "sources": [SOURCE],
        }
        data["terms"].append(entry)
        added += 1

    data["meta"]["version"] = "0.7.2"
    data["meta"]["updated"] = "2026-09-11"

    TERMS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"added: {added}  total terms: {len(data['terms'])}")


if __name__ == "__main__":
    main()
