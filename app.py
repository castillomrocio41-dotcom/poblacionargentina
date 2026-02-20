# app.py - TODO EN UN SOLO ARCHIVO (HASTA 2030)
# Genera el dataset automáticamente + muestra gráficos
# ¡Listo para Streamlit Cloud!

import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# 1. DATOS DE CENSO (ficticios pero realistas)
# =====================================================
@st.cache_data  # <- IMPORTANTE: guarda en caché para que no recalcule siempre
def cargar_datos_censo():
    """
    Datos de ejemplo de censos argentinos.
    Podés cambiar estos números cuando tengas datos reales.
    """
    data_censos = [
        # Buenos Aires (CABA)
        (1960, "Buenos Aires", 2976000, "censo"),
        (1970, "Buenos Aires", 2965000, "censo"),
        (1980, "Buenos Aires", 2985000, "censo"),
        (1991, "Buenos Aires", 2988000, "censo"),
        (2001, "Buenos Aires", 2891000, "censo"),
        (2010, "Buenos Aires", 2890151, "censo"),
        (2022, "Buenos Aires", 3121707, "censo"),

        # Córdoba (ciudad)
        (1960, "Cordoba", 580000, "censo"),
        (1970, "Cordoba", 750000, "censo"),
        (1980, "Cordoba", 950000, "censo"),
        (1991, "Cordoba", 1150000, "censo"),
        (2001, "Cordoba", 1270000, "censo"),
        (2010, "Cordoba", 1317298, "censo"),
        (2022, "Cordoba", 1505250, "censo"),

        # Mar del Plata
        (1960, "Mar del Plata", 260000, "censo"),
        (1970, "Mar del Plata", 350000, "censo"),
        (1980, "Mar del Plata", 420000, "censo"),
        (1991, "Mar del Plata", 500000, "censo"),
        (2001, "Mar del Plata", 550000, "censo"),
        (2010, "Mar del Plata", 593337, "censo"),
        (2022, "Mar del Plata", 667082, "censo"),

        # Neuquén
        (1960, "Neuquen", 30000, "censo"),
        (1970, "Neuquen", 55000, "censo"),
        (1980, "Neuquen", 80000, "censo"),
        (1991, "Neuquen", 140000, "censo"),
        (2001, "Neuquen", 201000, "censo"),
        (2010, "Neuquen", 231198, "censo"),
        (2022, "Neuquen", 468794, "censo"),
    ]
    return pd.DataFrame(data_censos, columns=["anio", "ciudad", "poblacion", "fuente"])

# =====================================================
# 2. FUNCIÓN QUE GENERA TODO EL DATASET (HASTA 2030)
# =====================================================
@st.cache_data
def generar_dataset_completo():
    """Genera el dataset completo 1950-2030 interpolando y proyectando"""
    
    # Cargar datos base
    df_censo = cargar_datos_censo()
    
    # 🎯 CAMBIO AQUÍ: Rango de años HASTA 2030
    anio_min, anio_max = 1950, 2030  
    cities = df_censo["ciudad"].unique()
    
    # Crear todas las combinaciones ciudad-año
    filas = []
    for ciudad in cities:
        for anio in range(anio_min, anio_max + 1):
            filas.append({"anio": anio, "ciudad": ciudad})
    
    df_todos = pd.DataFrame(filas)
    
    # Unir con datos de censo
    df = df_todos.merge(
        df_censo[["anio", "ciudad", "poblacion"]], 
        on=["anio", "ciudad"], 
        how="left"
    )
    
    # INTERPOLAR entre censos
    df["poblacion_interp"] = df.groupby("ciudad")["poblacion"].transform(
        lambda x: x.interpolate(method="linear")
    )
    
    # EXTRAPOLAR (simplificado)
    def extrapolar_simple(sub_df):
        sub_df = sub_df.copy()
        sub_df = sub_df.sort_values("anio")
        
        # Antes del primer censo: usar el primer valor
        primera = sub_df["poblacion_interp"].dropna().iloc[0]
        sub_df.loc[sub_df["poblacion"].isna() & (sub_df["anio"] < 1960), 
                  "poblacion_interp"] = primera
        
        # Después del último: crecimiento 1% anual simple
        ultima = sub_df["poblacion_interp"].dropna().iloc[-1]
        for i, row in sub_df.iterrows():
            if pd.isna(row["poblacion_interp"]) and row["anio"] > 2022:
                años_diff = row["anio"] - 2022
                sub_df.loc[i, "poblacion_interp"] = ultima * (1.01 ** años_diff)
        
        return sub_df
    
    df = df.groupby("ciudad").apply(extrapolar_simple).reset_index(drop=True)
    
    # Columna fuente
    df["fuente"] = np.where(df["poblacion"].notna(), "censo", 
                           np.where(df["anio"] > 2022, "proyección", "interpolación"))
    
    # Limpiar y ordenar
    df = df.drop(columns=["poblacion"])
    df = df.rename(columns={"poblacion_interp": "poblacion"})
    df["poblacion"] = df["poblacion"].round().astype(int)
    return df.sort_values(["ciudad", "anio"]).reset_index(drop=True)

# =====================================================
# 3. INTERFAZ STREAMLIT
# =====================================================
st.set_page_config(page_title="Población Argentina 2030", layout="wide")

st.title("📊 Evolución Poblacional Argentina 1950-**2030**")
st.markdown("**Ciudades: Buenos Aires, Córdoba, Mar del Plata, Neuquén**")

# Sidebar con filtros
st.sidebar.header("🔧 Filtros")
df_completo = generar_dataset_completo()

ciudades = st.sidebar.multiselect(
    "Ciudades:",
    options=sorted(df_completo["ciudad"].unique()),
    default=sorted(df_completo["ciudad"].unique())
)

rango_anios = st.sidebar.slider(
    "Años:",
    min_value=int(df_completo["anio"].min()),
    max_value=int(df_completo["anio"].max()),
    value=(1950, 2030)  # 🎯 Actualizado a 2030
)

# Filtrar datos
df_filtrado = df_completo[
    (df_completo["ciudad"].isin(ciudades)) &
    (df_completo["anio"].between(rango_anios[0], rango_anios[1]))
]

# =====================================================
# 4. GRÁFICOS Y TABLAS
# =====================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolución población")
    if not df_filtrado.empty:
        chart_data = df_filtrado.pivot(index="anio", columns="ciudad", values="poblacion")
        st.line_chart(chart_data, use_container_width=True)

with col2:
    st.subheader("📊 Estadísticas")
    if not df_filtrado.empty:
        stats = df_filtrado.groupby("ciudad")["poblacion"].agg([
            "min", "max", "mean"
        ]).round(0)
        st.dataframe(stats, use_container_width=True)

# Tabla completa
st.subheader("📋 Datos completos")
st.dataframe(df_filtrado, use_container_width=True)

# Métricas rápidas
col1, col2, col3, col4 = st.columns(4)
total_filas = len(df_filtrado)
max_poblacion = df_filtrado["poblacion"].max()
ciudad_max = df_filtrado.loc[df_filtrado["poblacion"].idxmax(), "ciudad"]
censos_reales = len(df_filtrado[df_filtrado["fuente"] == "censo"])

col1.metric("Filas", total_filas)
col2.metric("Máx población", f"{max_poblacion:,}")
col3.metric("Ciudad más poblada", ciudad_max)
col4.metric("Datos reales", censos_reales)

# 🎯 NUEVO: Proyección 2030
st.markdown("---")
st.subheader("🔮 **Proyecciones 2030**")
df_2030 = df_completo[df_completo["anio"] == 2030]
if not df_2030.empty:
    st.dataframe(df_2030[["ciudad", "poblacion"]], use_container_width=True)
