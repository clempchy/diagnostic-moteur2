
import streamlit as st
import pandas as pd
import math

st.title("Diagnostic Fréquentiel de Défauts Moteur")

def presque_egal(a, b, tol=0.05):
    return abs(a - b) / b < tol

def interpreter_formule(formule):
    f = formule.strip().lower()
    if "1 à 4" in f and "fr" in f:
        return lambda fr=0, **kwargs: [fr * i for i in range(1, 5)]
    elif "2*fr" in f or "2⋅fr" in f:
        return lambda fr=0, **kwargs: [2 * fr]
    elif "z × fr" in f or "z*fr" in f:
        return lambda fr=0, Z=1, **kwargs: [Z * fr]
    elif "fs ± fr" in f:
        return lambda fr=0, fs=0, **kwargs: [fs + fr, fs - fr]
    elif "0.42" in f and "fr" in f:
        return lambda fr=0, **kwargs: [fr * 0.42, fr * 0.48]
    elif f == "fr" or "= fr" in f:
        return lambda fr=0, **kwargs: [fr]
    elif "fs" in f:
        return lambda fs=0, **kwargs: [fs]
    elif "50" in f:
        return lambda **kwargs: [50]
    else:
        return lambda **kwargs: []

def charger_defauts_depuis_excel(path):
    try:
        df = pd.read_excel(path)
        df = df.rename(columns=lambda x: x.strip()).dropna(subset=["Anomalie", "Fréquence typique"])
        df = df[["Anomalie", "Fréquence typique", "Direction", "Remarques / Signature fréquentielle (vibratoire et/ou courant)"]]
        df.columns = ["nom", "frequence_typique", "direction", "cause"]
        defauts = []
        for _, row in df.iterrows():
            formule = interpreter_formule(row["frequence_typique"])
            defauts.append({
                "nom": row["nom"],
                "formule": formule,
                "direction": row["direction"],
                "cause": row["cause"]
            })
        return defauts
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier Excel : {e}")
        return []

defauts = charger_defauts_depuis_excel("pannes_moteurs.xlsx")

fr = st.number_input("Fréquence de rotation (fr)", value=0.0)
fs = st.number_input("Fréquence d'alimentation (fs)", value=0.0)
Z = st.number_input("Nombre de dents (Z)", value=0)
Nb = st.number_input("Nombre de billes (Nb)", value=0)
Db = st.number_input("Diamètre d’une bille (Db en m)", value=0.0)
Dp = st.number_input("Diamètre primitif (Dp en m)", value=0.0)
theta_deg = st.number_input("Angle de contact θ (degrés)", value=0.0)
theta = math.radians(theta_deg)
f_critique = st.number_input("Fréquence critique (si connue)", value=0.0)
fp = st.number_input("Fréquence de passage courroie (fp)", value=0.0)
g = st.number_input("Glissement (g)", value=0.0)
Nr = st.number_input("Nombre de paires de pôles (Nr)", value=0)
f_aubes = st.number_input("Fréquence de passage des aubes", value=0.0)

frequences_entree = st.text_input("Fréquences mesurées (Hz, séparées par des virgules)", "")
direction = st.selectbox("Direction de la vibration mesurée", ["Axiale", "Radiale", "Axiale et radiale"])

if st.button("Diagnostiquer") and frequences_entree.strip():
    frequences_mesurees = [float(f.strip()) for f in frequences_entree.split(",") if f.strip()]
    caracteristiques = {
        "fr": fr, "fs": fs, "Z": Z, "Nb": Nb, "Db": Db,
        "Dp": Dp, "theta": theta, "f_critique": f_critique,
        "fp": fp, "g": g, "Nr": Nr, "f_aubes": f_aubes
    }

    resultats = []
    for f in frequences_mesurees:
        for d in defauts:
            try:
                f_calc = d["formule"](**caracteristiques)
                if any(presque_egal(f, fc) for fc in f_calc):
                    if direction.lower() in d["direction"].lower() or "et" in d["direction"].lower():
                        resultats.append({
                            "frequence": f,
                            "defaut": d["nom"],
                            "frequences_typiques": f_calc,
                            "cause": d["cause"]
                        })
            except Exception as e:
                continue

    if resultats:
        st.success("Défauts potentiels détectés :")
        for r in resultats:
            st.markdown(f"**{r['defaut']}** détecté à {r['frequence']} Hz")
            st.markdown(f"Fréquences typiques : `{r['frequences_typiques']}`")
            st.markdown(f"Cause probable : {r['cause']}")
    else:
        st.warning("Aucun défaut connu détecté.")
