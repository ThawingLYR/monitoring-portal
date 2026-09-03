from .plot_timeseries_boreholes import PlotTimeseriesBoreholes
from .plot_timeseries_months_boreholes import PlotTimeseriesMonthsBoreholes
from .plot_trumpet_curves_boreholes import PlotTrumpetCurveBoreholes
from .plot_profile_current_past_dates import PlotLatestProfilePastSameDateBoreholes
from .plot_isotherm_development_all_boreholes import PlotIsothermDevelopmentAllBoreholes
from .plot_isotherm_development_deepest_boreholes import (
    PlotIsothermDevelopmentDeepestBoreholes,
)
from .plot_heatmap_boreholes import PlotContourDiscreteTemperatureDepthsTimesBoreholes

all_boreholes_figures = [
    PlotTimeseriesBoreholes,
    PlotTimeseriesMonthsBoreholes,
    PlotTrumpetCurveBoreholes,
    PlotLatestProfilePastSameDateBoreholes,
    PlotIsothermDevelopmentAllBoreholes,
    PlotIsothermDevelopmentDeepestBoreholes,
    PlotContourDiscreteTemperatureDepthsTimesBoreholes,
]
