################################################################################
# Gyration                                                                     #
#                                                                              #
"""Analyse gyration radius in a pore."""
################################################################################


import seaborn as sns
import matplotlib.pyplot as plt

import poreana.utils as utils


def plot(data_link_gyr, data_link_dens, intent="", is_mean=False):
    """This function plots the gyration radius. If an intent is
    given instead, only a plot-function will be called. Available
    options for ``intent`` are

    * empty string - Create subplots for the density inside and outside the pore
    * **in** - Create plot for the density inside pore
    * **ex** - Create plot for the density outside pore

    Parameters
    ----------
    data_link_dens : string
        Link to density data object generated by the sample rountine
        :func:`poreana.sample.density`
    data_link_gyr : string
        Link to gyration data object generated by the sample routine
        :func:`poreana.sample.gyration`
    intent : string, optional
        Intent for plotting
    is_mean : bool, optional
        True to plot mean values

    Returns
    -------
    mean : dictionary
        Mean value of the radius of gyration inside and outside the pore in nm
    """
    # Load data
    areas = ["in", "ex"]
    gyr = utils.load(data_link_gyr)
    dens = utils.load(data_link_dens)
    width = {}
    width["in"] = gyr["data"]["in_width"][:-1]
    width["ex"] = gyr["data"]["ex_width"]

    # Divide gyration radius by density in bins
    gyration = {area: [gyr["data"][area][i]/dens["data"][area][i] if dens["data"][area][i] else 0 for i in range(len(gyr["data"][area]))] for area in areas}

    # Calculate mean gyration radius
    mean = {area: sum(gyration[area])/len(gyration[area]) for area in areas}

    # Full plot
    if not intent:
        plt.subplot(211)
        sns.lineplot(x=width["in"], y=gyration["in"])
        if is_mean:
            sns.lineplot(x=width["in"], y=[mean["in"] for x in width["in"]])

        plt.xlim([0, width["in"][-1]])
        plt.xlabel("Distance from pore center (nm)")
        plt.ylabel(r"Radius (nm)")
        plt.legend(["Gyration radius", "Mean"])

        plt.subplot(212)
        sns.lineplot(x=width["ex"], y=gyration["ex"])
        if is_mean:
            sns.lineplot(x=width["ex"], y=[mean["ex"] for x in width["ex"]])

        plt.xlim([0, width["ex"][-1]])
        plt.xlabel("Distance from reservoir end (nm)")
        plt.ylabel(r"Radius (nm)")
        plt.legend(["Gyration radius", "Mean"])

    # Intent plots
    else:
        if intent not in ["in", "ex"]:
            print("Invalid intent. Check documentation for available options.")
            return

        sns.lineplot(x=width[intent], y=gyration[intent])
        plt.xlim([0, width[intent][-1]])

    return mean
