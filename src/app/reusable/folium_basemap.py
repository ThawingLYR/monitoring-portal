from folium import Element
import folium


def get_folium_basemap(location=[78.213578, 15.599462], zoom_start=11):

    # Create map centered near Longyearbyen
    m = folium.Map(
        location=[78.213578, 15.599462], zoom_start=11, tiles=None, control_scale=True
    )  # , width=300, height=100)

    # Basemap layers for different zoom levels
    basemap = folium.FeatureGroup(name="Basemap", overlay=False)

    folium.raster_layers.WmsTileLayer(
        url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Basiskart_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
        layers="NP_Basiskart_Svalbard_WMTS_3857",
        fmt="image/png",
        transparent=False,
        version="1.0.0",
        attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
        name="Basemap low zoom",
        min_zoom=0,
        max_zoom=12,
        overlay=True,
        show=True,
    ).add_to(basemap)

    folium.raster_layers.WmsTileLayer(
        url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/FKB_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
        layers="FKB_Svalbard_WMTS_3857",
        fmt="image/png",
        transparent=False,
        version="1.0.0",
        attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
        name="Basemap high zoom",
        min_zoom=13,
        max_zoom=17,
        overlay=True,
        show=True,
    ).add_to(basemap)

    basemap.add_to(m)

    # Orthographic map as overlay
    folium.raster_layers.WmsTileLayer(
        url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Ortofoto_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
        layers="NP_Ortofoto_Svalbard_WMTS_3857",
        fmt="image/png",
        transparent=False,
        version="1.0.0",
        attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
        name="Orthophoto",
        min_zoom=0,
        max_zoom=17,
        overlay=True,
        control=True,
        show=False,
    ).add_to(m)

    # Add layer control: this method ensures that there is no jumping of zoom levels when switching between basemap and ortographic map
    folium.LayerControl().add_to(m)

    js = """
    <script>
    var basemapLayers = [];
    var orthoLayer;

    // collect layers
    map.eachLayer(function(layer){
        if(layer.options && layer.options.name === "Orthophoto"){
            orthoLayer = layer;
        }
        if(layer.options && layer.options.name === "Basemap low zoom"){
            basemapLayers.push(layer);
        }
        if(layer.options && layer.options.name === "Basemap high zoom"){
            basemapLayers.push(layer);
        }
    });

    // custom control behavior
    map.on('overlayadd', function(e){
        if(e.name === "Orthophoto"){
            basemapLayers.forEach(l => map.removeLayer(l));
        }
        if(e.name === "Basemap Low" || e.name === "Basemap high zoom"){
            map.removeLayer(orthoLayer);
        }
    });
    </script>
    """

    m.get_root().html.add_child(Element(js))

    return m
