import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from math import radians, sin, cos, sqrt, atan2
import certifi
import ssl
import urllib3
import requests

def haversine_distance(row, lat2, lon2):
    """Calcule la distance haversine entre deux points (en mètres)."""
    R = 6371000.0  # Rayon de la Terre en mètres
    lat1, lon1 = radians(row["Lat"]), radians(row["Long"])
    lat2, lon2 = radians(lat2), radians(lon2)
    
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def get_coordinates(address):
    """Convertit une adresse en latitude/longitude avec Nominatim."""
    try:
        # Configuration du géocodeur avec certificat SSL
        ctx = ssl.create_default_context(cafile=certifi.where())
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        geolocator = Nominatim(
            user_agent="komfor_app",
            scheme='https',
            ssl_context=ctx
        )
        
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
            
    except Exception as e:
        print(f"Erreur de géocodage : {e}")
        return None, None

def run():
    st.set_page_config(
        page_title="Réseaux d'énergie thermique Komfor",
        page_icon="🔥",
    )

    # Charger les données des réseaux de chaleur
    df = pd.read_csv("data.csv", sep=",")

    # Interface utilisateur
    st.markdown("## Les prochains réseaux d'énergie thermique Komfor proches de chez moi")
    st.markdown("**👇 Introduisez votre adresse ci-dessous**")

    address_query = st.text_input("Entrez votre adresse")

    if address_query:
        lat, lon = get_coordinates(address_query)

        if lat and lon:
            df['distance'] = df.apply(haversine_distance, args=(lat, lon), axis=1)
            df_close_distance = df[df["distance"] <= 2000]

            if not df_close_distance.empty:
                closest_network = df_close_distance.loc[df_close_distance["distance"].idxmin(), "Nom"]
            else:
                closest_network = "Pas de réseau trouvé"

            # Messages en fonction de la distance
            if df_close_distance["distance"].min() < 50:
                st.success(f"Le réseau **{closest_network}** passera à côté de chez vous. Contactez-nous pour un raccordement.")
            elif df_close_distance["distance"].min() < 500:
                st.info(f"Le réseau **{closest_network}** est en développement dans votre quartier. Contactez-nous pour évaluer une extension.")
            elif df_close_distance["distance"].min() <= 2000:
                st.info(f"Le réseau **{closest_network}** est en développement à proximité. Si vous êtes un grand consommateur, contactez-nous.")
            else:
                st.info("Aucun réseau à proximité. Suivez-nous sur [LinkedIn](https://www.linkedin.com/company/komfor-energy/).")

            # Affichage de la carte avec Folium
            map_center = [lat, lon]
            m = folium.Map(location=map_center, zoom_start=13)

            # Ajouter l'adresse de l'utilisateur en bleu
            folium.Marker(
                [lat, lon],
                popup="Votre adresse",
                icon=folium.Icon(color="blue"),
            ).add_to(m)
            # Ajouter les réseaux de chaleur comme des ponts et les relier par des lignes
            points = []
            for _, row in df_close_distance.iterrows():
                point = [row["Lat"], row["Long"]]
                points.append(point)
                folium.CircleMarker(
                    point,
                    popup=row["Nom"],
                    radius=8,
                    color="green",
                    fill=True,
                    weight=1
                ).add_to(m)

          

            # Afficher la carte dans Streamlit
            st_folium(m, width=700, height=500)

        else:
            st.error("Adresse introuvable. Veuillez réessayer.")

if __name__ == "__main__":
    run()
