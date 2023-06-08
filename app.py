import toml
import json
from PIL import Image

import ee
import streamlit as st
from streamlit_folium import st_folium
from shapely import Polygon

from soils_revealed.map import MapGEE
from soils_revealed.data import GEEData, read_ds
from soils_revealed.processing import get_data, get_plot
from soils_revealed.verification import selected_bbox_too_large, selected_bbox_in_boundary

MAP_CENTER = [-2.2, 113.8]
MAP_ZOOM = 10
MAX_ALLOWED_AREA_SIZE = 20.0
FILENAME = 'data/land-cover.pkl'
BTN_LABEL = "Submit"

# Load the environment variables from .env
env_var = toml.load(".env")

# Initialize GEE
private_key = env_var["EE_PRIVATE_KEY"]
ee_credentials = ee.ServiceAccountCredentials(email=private_key['client_email'], key_data=json.dumps(private_key))
ee.Initialize(credentials=ee_credentials)

# Load icon
icon = Image.open("images/soils03.png")

# Load datasets
datasets = {}
for dataset in ['SOC-Stock-Change', 'Global-Land-Cover']:
    datasets[dataset] = GEEData(dataset)

# Read data
ds = read_ds(access_key_id=env_var["S3_ACCESS_KEY_ID"], secret_accsess_key=env_var["S3_SECRET_ACCESS_KEY"])


# Create the Streamlit app and define the main code:
def main():
    st.set_page_config(
        page_title="soils_revealed-demo",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("Soils Revealed Demo")

    m = MapGEE(center=MAP_CENTER, zoom=MAP_ZOOM)

    # Add layers
    m.add_gee_layer(
        image=datasets['SOC-Stock-Change'].ee_image(),
        sld_interval=datasets['SOC-Stock-Change'].sld_interval(),
        name=f'SOC Stock Change (2000 - 2018)'
    )

    for year in ['2000', '2018']:
        m.add_gee_layer(
            image=datasets['Global-Land-Cover'].ee_image(year=year),
            sld_interval=datasets['Global-Land-Cover'].sld_interval(),
            name=f'Global Land Cover ({year})'
        )

    m.add_layer_control()

    output = st_folium(m, key="init", width=1200, height=600)

    geojson = None
    if output["all_drawings"] is not None:
        if len(output["all_drawings"]) != 0:
            if output["last_active_drawing"] is not None:
                # get latest modified drawing
                geojson = output["last_active_drawing"]

    # ensure progress bar resides at top of sidebar and is invisible initially
    progress_bar = st.sidebar.progress(0)
    progress_bar.empty()

    # Create an empty container for the plotly figure
    text_container = st.empty()
    plot_container = st.empty()


    # Getting Started container
    with st.sidebar.container():
        # Getting started
        st.subheader("Getting Started")
        st.markdown(
            f"""
                        1. Click the black square on the map
                        2. Draw a rectangle on the map
                        3. Click on <kbd>{BTN_LABEL}</kbd>
                        4. Wait for the computation to finish
                        """,
            unsafe_allow_html=True,
        )

        # Add the button and its callback
        if st.button(
            BTN_LABEL,
            key="compute_zs",
            disabled=False if geojson is not None else True,
        ):
            # Check if the geometry is valid
            geometry = geojson['geometry']
            if selected_bbox_too_large(geometry, threshold=MAX_ALLOWED_AREA_SIZE):
                st.sidebar.warning(
                    "Selected region is too large, fetching data for this area would consume too many resources. "
                    "Please select a smaller region."
                )
            elif not selected_bbox_in_boundary(geometry):
                st.sidebar.warning(
                    "Selected rectangle is not within the allowed region of the world map. "
                    "Do not scroll too far to the left or right. "
                    "Ensure to use the initial center view of the world for drawing your rectangle."
                )
            else:
                # Create a Shapely polygon from the coordinates
                poly = Polygon(geojson['geometry']['coordinates'][0])
                # Get the bbox coordinates using the bounds() method
                xmin, ymin, xmax, ymax = poly.bounds

                # Data analysis
                ds_eg = ds.sel(x=slice(xmin, xmax), y=slice(ymax, ymin)).copy()

                # Generate the data required for the plot
                data = get_data(ds_eg)

                # Generate the plot using Matplotlib
                plot = get_plot(data)

                # Display the plot using Streamlit
                text_container.subheader("SOC stock change by land cover")
                plot_container.pyplot(plot)


if __name__ == "__main__":
    main()