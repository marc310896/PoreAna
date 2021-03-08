################################################################################
# Diffusion                                                                    #
#                                                                              #
"""Analyse diffusion in a pore."""
################################################################################


import math
import warnings
import scipy as sp
import numpy as np
# import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import poreana.utils as utils
import poreana.density as density


def cui(data_link, z_dist=None, ax_area=[0.2, 0.8], intent=None, is_fit=False, is_plot=True):
    """This function samples and calculates the diffusion coefficient of a
    molecule group in a pore in both axial and radial direction, as described
    in the paper of `Cui <https://doi.org/10.1063/1.1989314>`_.

    The mean square displacement is sampled in function
    :func:`poreana.sample.diffusion_bin`.

    The axial diffusion is given by the Einstein relation

    .. math::

        \\langle\\left[z(0)-z(t)\\right]^2\\rangle=2D_\\text{axial}t

    with axial diffusion coefficient :math:`D_\\text{axial}`. Thus the
    coefficient corresponds to the slope of the axial msd

    .. math::

        D_\\text{axial}=\\frac12\\frac{\\text{msd}_\\text{axial}[i]-\\text{msd}_\\text{axial}[j]}{t_i-t_j}

    with bin :math:`i>j`. The radial diffusion is given by

    .. math::

        \\langle\\left[r(0)-r(t)\\right]^2\\rangle=R^2\\left[1-\\sum_{n=1}^\\infty\\frac{8}{\\lambda_{1n}^2(\\lambda_{1n}^2-1)}\\exp\\left(-\\frac{\\lambda_{1n}^2}{R^2}D_\\text{radial}t\\right)\\right].

    with radial diffusion coefficient :math:`D_\\text{radial}`, the maximal
    accessible radial position :math:`R` by an atom

    .. math::

        R = \\frac12d-0.2

    with pore diameter :math:`d`, and the zeros :math:`\\lambda_{1n}^2` of
    the derivative

    .. math::

        \\frac{dJ_1}{dx}

    of the first order Bessel function :math:`J_1`. Therefore the coefficient
    has to be fitted to the sampled radial msd. The author observed that
    the first 20 Bessel function zeros were sufficient for the function fit.

    The final unit transformation is done by

    .. math::

        \\frac{\\text{nm}^2}{\\text{ps}}=10^{-2}\\frac{\\text{cm}^2}{\\text{s}}.

    **Note that the function for the radial diffusion is obtained under the
    assumption that the density inside the pore is uniform.**

    Parameters
    ----------
    data_link : string
        Link to data object generated by the sample routine
        :func:`poreana.sample.diffusion_bin`
    z_dist : float, None, optional
        Distance from pore centre to calculate the mean
    ax_area : list, optional
        Bin area percentage to calculate the axial diffusion coefficient
    intent : string, None, optional
        axial, radial or None for both
    is_fit : bool, optional
        True to plot the fitted function
    is_plot : bool, optional
        True to create plot in this function
    """
    # Load data object
    sample = utils.load(data_link)

    # Load data
    inp = sample["inp"]
    bins = inp["bins"] if z_dist is None else math.floor(z_dist/sample["bins"][1])
    msd_z = [0 for x in range(inp["window"])]
    msd_r = [0 for x in range(inp["window"])]
    norm_z = [0 for x in range(inp["window"])]
    norm_r = [0 for x in range(inp["window"])]

    # Sum up all bins
    for i in range(bins):
        for j in range(inp["window"]):
            msd_z[j] += sample["axial_tot"][i][j]
            norm_z[j] += sample["norm_tot"][i][j]

    for i in range(inp["bins"]):
        for j in range(inp["window"]):
            msd_r[j] += sample["radial_tot"][i][j]
            norm_r[j] += sample["norm_tot"][i][j]

    # Normalize
    msd_z_n = [msd_z[i]/norm_z[i] if norm_z[i] > 0 else 0 for i in range(inp["window"])]
    msd_r_n = [msd_r[i]/norm_r[i] if norm_r[i] > 0 else 0 for i in range(inp["window"])]

    # Define time axis and range
    time_ax = [x*inp["step"]*inp["frame"] for x in range(inp["window"])]
    t_range = (inp["window"]-1)*inp["step"]*inp["frame"]

    # Calculate axial coefficient
    if intent is None or intent == "axial":
        dz = (msd_z_n[int(ax_area[1]*inp["window"])]-msd_z_n[int(ax_area[0]*inp["window"])])*1e-9**2/((ax_area[1]-ax_area[0])*t_range)/2*1e2**2*1e5  # 10^-9 m^2s^-1

        print("Diffusion axial:  "+"%.3f" % dz+" 10^-9 m^2s^-1")

    # Calculate radial coefficient
    if intent is None or intent == "radial":
        def diff_rad(x, a, b, c):
            # Process input
            x = x if isinstance(x, list) or isinstance(x, np.ndarray) else [x]

            # Get bessel function zeros
            jz = sp.special.jnp_zeros(1, math.ceil(b))
            # Calculate sum
            sm = [[8/(z**2*(z**2-1))*math.exp(-(z/c)**2*a*t) for z in jz] for t in x]
            # Final equation
            return [c**2*(1-sum(s)) for s in sm]

        # Fit function
        popt, pcov = sp.optimize.curve_fit(diff_rad, [x*1e12 for x in time_ax], msd_r_n, p0=[1, 20, inp["diam"]/2-0.2], bounds=(0, np.inf))

        print("Diffusion radial: "+"%.3f" % (popt[0]*1e3)+" 10^-9 m^2 s^-1; Number of zeros: "+"%2i" % (math.ceil(popt[1]))+"; Radius: "+"%5.2f" % popt[2])

    # Plot
    if is_plot:
        # plt.figure(figsize=(10, 7))
        sns.set(style="whitegrid")
        sns.set_palette(sns.color_palette("deep"))
        legend = []

    if intent is None or intent == "axial":
        sns.lineplot(x=[x*1e12 for x in time_ax], y=msd_z_n)
        if is_plot:
            legend += ["Axial"]
        if is_fit:
            sns.lineplot(x=[x*1e12 for x in time_ax], y=[dz*2*time_ax[x]/1e5/1e-7**2 for x in range(inp["window"])])
            legend += ["Fitted Axial"]

    if intent is None or intent == "radial":
        sns.lineplot(x=[x*1e12 for x in time_ax], y=msd_r_n)
        if is_plot:
            legend += ["Radial"]
        if is_fit:
            sns.lineplot(x=[x*1e12 for x in time_ax], y=diff_rad([x*1e12 for x in time_ax], *popt))
            legend += ["Fitted Radial"]

    if is_plot:
        plt.xlabel("Time (ps)")
        plt.ylabel(r"Mean square displacement (nm$^2$)")
        plt.legend(legend)


def bins(data_link, ax_area=[0.2, 0.8], intent="plot", is_norm=False):
    """This function calculates the axial (z-axis) diffusion coefficient as a
    function of the radial distance. This is done by sampling the mean square
    displacement for all molecules in a radial sub volume.

    The mean square displacement is sampled in function
    :func:`poreana.sample.diffusion_bin`.

    For each bin, the msd is summed up, resulting into a msd slope for each
    bin. Thus, the axial diffusion coefficient can be calculated using

    .. math::

        D_\\text{axial}=\\frac12\\frac{\\text{msd}_\\text{axial}[i]-\\text{msd}_\\text{axial}[j]}{t_i-t_j}.

    Note that the msd is evaluated in the area, where the slope is uniform,
    which means that the first twenty and last twenty percent should be
    neglected.

    If ``is_norm`` is set to **True**, the radius will be normalized in respect
    to the effective radius which means, the last radius that has a
    Diffusion greater than zero is taken

    .. math::

        r_\\text{norm}=\\frac{1}{r_\\text{eff}}r.

    Parameters
    ----------
    data_link : string
        Link to data object generated by the sample routine :func:`poreana.sample.diffusion_bin`
    ax_area : list, optional
        Bin area percentage to calculate the axial diffusion coefficient
    intent : string, optional
        Set to **plot**, for plotting or set to **line** to only return the
        lineplot, leave empty for nothing
    is_norm : bool, optional
        True to normalize x-axis

    Returns
    -------
    diffusion : list
        List of the slope of the non-normalized diffusion coefficient
    """
    # Load data object
    sample = utils.load(data_link)

    # Load data
    inp = sample["inp"]
    bins = sample["bins"]
    msd_z = sample["axial"]
    norm = sample["norm"]

    # Normalize
    msd_norm = [[msd_z[i][j]/norm[i][j] if norm[i][j] > 0 else 0 for j in range(inp["window"])] for i in range(inp["bins"]+1)]

    # Calculate slope
    f_start = int(ax_area[0]*inp["window"])
    f_end = int(ax_area[1]*inp["window"])
    time_ax = [x*inp["step"]*inp["frame"] for x in range(inp["window"])]
    slope = [(msd_norm[i][f_end]-msd_norm[i][f_start])/(time_ax[f_end]-time_ax[f_start]) for i in range(inp["bins"]+1)]

    # Calculate diffusion coefficient
    diff = [msd*1e-9**2/2*1e2**2*1e5 for msd in slope]  # 10^-9 m^2s^-1

    # Normalize x-axis
    if is_norm:
        for i in range(len(diff)-1, 0, -1):
            if diff[i] > 0:
                x_max = bins[i+1]
                break

        bins_norm = [x/x_max for x in bins]

    # Plot
    if intent == "plot":
        # plt.figure(figsize=(10, 7))
        sns.set(style="whitegrid")
        sns.set_palette(sns.color_palette("deep"))

    if intent == "plot" or intent == "line":
        x_axis = bins_norm if is_norm else bins
        sns.lineplot(x=x_axis[:-1], y=diff)

    if intent == "plot":
        if is_norm:
            plt.xlabel("Normalized distance from pore center")
        else:
            plt.xlabel("Distance from pore center (nm)")
        plt.ylabel(r"Diffusion coefficient ($10^{-9}$ m${^2}$ s$^{-1}$)")

    return {"bins": bins, "diff": diff}


def mean(data_link_diff, data_link_dens, ax_area=[0.2, 0.8], is_norm=False):#, is_check=False):
    """This function uses the diffusion coefficient slope obtained from
    function :func:`bins` and the density slope of function
    :func:`poreana.density.calculate` to calculate a weighted diffusion
    coefficient inside the pore

    .. math::

        \\langle D_\\text{axial}\\rangle
        =\\frac{\\int\\rho(r)D_\\text{axial}(r)dA(r)}{\\int\\rho(r)dA(r)}.

    In a discrete form, following formula is evaluated

    .. math::

        \\langle D_\\text{axial}\\rangle=\\frac{\\sum_{i=1}^n\\rho(r_i)D_\\text{axial}(r_i)A(r_i)}{\\sum_{i=1}^n\\rho(r_i)A(r_i)}

    with the partial area

    .. math::

        A(r_i)=\\pi(r_i^2-r_{i-1}^2)

    of radial bin :math:`i`.

    Parameters
    ----------
    data_link_dens : string
        Link to density data object generated by the sample rountine
        :func:`poreana.density.sample`
    data_link_diff : string
        Link to diffusion data object generated by the sample routine
        :func:`poreana.sample.diffusion_bin`
    ax_area : list, optional
        Bin area percentage to calculate the axial diffusion coefficient
    is_norm : bool, optional
        True to normalize x-axis
    is_check : bool, optional
        True to show density function fit
    """
    # Load data
    dens = density.calculate(data_link_dens, is_print=False)
    diff = bins(data_link_diff, ax_area=ax_area, intent="", is_norm=is_norm)

    # Get number of bins
    bin_num = len(diff["bins"][:-1])

    # Set diffusion functions
    bins_f = diff["bins"][:-1]
    diff_f = diff["diff"]

    # Fit density function
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', r'Polyfit may be poorly conditioned')
        param = np.polyfit(dens["in"][0][0][:-1], dens["in"][1], 100)
        dens_f = np.poly1d(param)(bins_f)

    # Check results
    # if is_check:
    #     # Plot check
    #     plt.plot(dens["in"][0][0][:-1], dens["in"][1], diff["bins"][:-1], dens_f)
    #     plt.show()
    #
    #     # Output data as excel
    #     df = pd.DataFrame({"bins": bins_f, "dens": dens_f, "diff": diff_f})
    #     df.to_excel("C:/Users/Ajax/Desktop/"+data_link_diff.split("/")[-1].split(".")[0]+".xlsx")

    # Integrate density
    dens_int = sum([dens_f[i]*(bins_f[i+1]**2-bins_f[i]**2) for i in range(bin_num-1)])

    # Calculate weighted diffusion
    diff_int = sum([dens_f[i]*diff_f[i]*(bins_f[i+1]**2-bins_f[i]**2) for i in range(bin_num-1)])

    # Normalize
    diff_weight = diff_int/dens_int

    print("Mean Diffusion axial: "+"%.3f" % diff_weight+" 10^-9 m^2s^-1")
