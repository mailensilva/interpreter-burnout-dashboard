import pandas as pd
import numpy as np
import os
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier

# ======================
# 1. Ubicar Carpeta de Descargas
# ======================
# Esto detecta automáticamente la ruta C:\Users\TuUsuario\Downloads
downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
archivo_entrada = os.path.join(downloads_path, "interpreters_risk_analysis.xlsx")

if not os.path.exists(archivo_entrada):
    print(f"❌ Error: No se encuentra el archivo en: {archivo_entrada}")
    print("Asegurate de que el nombre sea exactamente 'interpreters_risk_analysis.xlsx'")
else:
    df = pd.read_excel(archivo_entrada)
    df.columns = df.columns.str.lower().str.strip()

    # ======================
    # 2. Transformaciones
    # ======================
    df["would_work_again_num"] = df["would_work_again"].map({
        "Yes": 1,
        "Maybe": 0.5,
        "No": 0
    }).fillna(0.5)

    # ======================
    # 3. Ponderación de calls (Legal = Prioridad 1)
    # ======================
    def calcular_peso_calls(x):
        x = str(x).lower()
        peso = 0
        if "legal" in x or "court" in x:
            peso += 5  
        if "911" in x or "emergency" in x:
            peso += 4
        if "er" in x or "critical" in x:
            peso += 3.5
        if "medical" in x:
            peso += 2.5
        if "social" in x:
            peso += 1.5
        if "insurance" in x:
            peso += 1
        return peso

    df["difficulty_weighted"] = df["call_difficult"].apply(calcular_peso_calls)

    # ======================
    # 4. Variables de control
    # ======================
    np.random.seed(42)
    df["breaks_per_day"] = np.random.randint(1, 7, size=len(df)) 
    df["qa_score"] = np.random.normal(loc=85, scale=5, size=len(df)).clip(60, 100)

    # ======================
    # 5. Burnout risk (Breaks SUMAN riesgo)
    # ======================
    df["burnout_risk_score"] = (
        (df["difficulty_weighted"] * 0.45) +              
        (df["breaks_per_day"] * 0.25) +                  
        (1 / (df["final_payment_hour"] + 1) * 0.20) +    
        (1 - df["would_work_again_num"]) * 0.10          
    )

    # Normalización
    min_val = df["burnout_risk_score"].min()
    max_val = df["burnout_risk_score"].max()
    df["burnout_risk_score"] = (df["burnout_risk_score"] - min_val) / (max_val - min_val)

    df["burnout_risk"] = (df["burnout_risk_score"] > 0.65).astype(int)

    # ======================
    # 6. Modelo y Exportación
    # ======================
    df_synth = resample(df, replace=True, n_samples=400, random_state=42)
    df_full = pd.concat([df, df_synth], ignore_index=True)

    features = ["difficulty_weighted", "final_payment_hour", "would_work_again_num", "breaks_per_day"]
    X = df_full[features]
    y = df_full["burnout_risk"]

    model = RandomForestClassifier(random_state=42)
    model.fit(X, y)

    # Guardar el resultado también en Downloads para que lo encuentres fácil
    archivo_salida = os.path.join(downloads_path, "interpreters_risk_final.xlsx")
    df_full.to_excel(archivo_salida, index=False)
    
    print(f"✅ Proceso completado.")
    print(f"📁 Archivo generado en: {archivo_salida}")