from .plot_timeseries_aws_temp import PlotTimeseriesAWStemp
from .plot_timeseries_wind_aws_temp import PlotTimeserieswindAWStemp
from .plot_windrose_aws_temp import PlotWindroseAWStemp
from .plot_windrose_2hr_aws_temp import PlotWindrose2hAWStemp
from .plot_timeseries_rh_aws_temp import PlotTimeseriesRhAWStemp
from .plot_timeseries_atmp_aws_temp import PlotTimeseriesAtmpAWStemp
from .plot_timeseries_vp_aws_temp import PlotTimeseriesVpAWStemp
from .plot_latest_measurements import (
    AirTemperatureFigure,
    WindSpeedsCombinedFigure,
    WindDirectionFigure,
    RelativeHumidityFigure,
    AtmosphericPressureFigure,
    VaporPressureFigure,
)

all_aws_temp_figures = [
    PlotTimeseriesAWStemp,
    PlotTimeserieswindAWStemp,
    PlotWindroseAWStemp,
    PlotWindrose2hAWStemp,
    PlotTimeseriesRhAWStemp,
    PlotTimeseriesAtmpAWStemp,
    PlotTimeseriesVpAWStemp,
    AirTemperatureFigure,
    WindSpeedsCombinedFigure,
    WindDirectionFigure,
    RelativeHumidityFigure,
    AtmosphericPressureFigure,
    VaporPressureFigure,
]
