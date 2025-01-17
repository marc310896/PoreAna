import numpy as np
import pandas as pd

import poreana.utils as utils

class Model:
    """This class sets the general parameters which are used to initialize
    a model.

    Parameters
    ----------
    data_link : string
        data link to the pickle data from sample_mc
    d0 : double, optional
        initial guess of diffusion coefficent
    """

    def __init__(self, data_link, d0=1e-8):

        # Load data object
        sample = utils.load(data_link)
        inp = sample["inp"]
        self._model_inp = sample

        # Read the inputs
        self._bin_num = inp["bin_num"]                                       # number of bins z-direction
        self._frame_num= inp["num_frame"]                                    # number of bins z-direction
        self._len_step = inp["len_step"]                                     # step length
        self._dt = inp["len_frame"] * 10**12                                 # frame length [ps]
        self._bins = inp["bins"]                                             # bins [nm]
        self._bin_width = self._bins[1] - self._bins[0]                      # bin width [nm]
        self._trans_mat = sample["data"]                                     # transition matrix
        self._pbc = inp["pbc"]                                               # pbc or nopbc
        self._d0 = d0 * (10**18)/(10**12)                                    # guess init profile [A^2/ps]

        # Initialize units of w and v
        self._df_unit = 1.                                                   # in kBT
        self._diff_unit = np.log(self._bin_width**2 / 1.)                    # in m^2/s

        return

    def init_profiles(self):
        """
        This function initializes the normal diffusion, radial diffusion and
        free energy profile over the bins.
        """

        # Initialize the diffusion and free energy profile
        self._df_bin = np.float64(np.zeros(self._bin_num))                   # in kBT
        self._diff_bin = np.float64(np.zeros(self._bin_num))                 # in dz**2/dt


        #Initalize the diffusion profile
        self._diff_bin += (np.log(self._d0) - self._diff_unit)


    def calc_profile(self, coeff, basis):
        """
        This function calculates the diffusion and free energy profile over the
        bins. It is used to initialize the system at the beginning of the
        calculation/MC run. Additional it is needed to update the profiles
        in the Monte Carlo part after the adjustment of a profile coefficient.

        The profile is determining with the basis and the coefficients for the
        free energy with

        .. math::

            \\mathrm{basis} = a_{k} \\cdot \\mathrm{basis}_{\\text{F}},

        and for the diffusion with

        .. math::

            \\mathrm{basis} = a_{k} \\cdot \\mathrm{basis}_{\\text{D}}.

        The diffusion is calculated between to bins and the free energy
        in the center of a bin.
        The basis is received by the create basis function for the chosen model:

        *CosineModel:*
         * :func:`CosineModel.create_basis_center`

         * :func:`CosineModel.create_basis_border`


        *StepModel:*
         * :func:`StepModel.create_basis_center`

         * :func:`StepModel.create_basis_border`

        Parameters
        ----------
        coeff : list
            list of coefficients
        basis : list
            list of the basis part of model
        """

        # Calculate a matrix with the bin_num x ncos
            # Columns contains the n-summand in every bin
            # Line contains the summand of the series
        a = coeff * basis

        return np.sum(a,axis=1)



class CosineModel(Model):
    """This class sets the Cosine Model to calculate the free energy profile
    and the diffusion profile. The profiles have the typical cosine oscillation.
    These profiles over the bins are expressed by the following Fourier
    series. The diffusion profile is calculated between bin i and i+1  over
    the bin border with

    .. math::

        \\ln \\left(D_{i+ \\frac{1}{2}}\\right)=a_{0}+\\sum_{k=1}^{n_b} a_{k} \\cdot \\cos \\left(\\frac{2\\pi ki}{n}\\right).


    Similar the free energy Fourier series can be written:

    .. math::

        F_{i} = a_{0}+\\sum_{k=1}^{n_b} a_{k} \\cdot \\cos \\left(\\frac{2\\pi ki}{n} \\right).

    with the number of bins :math:`n`, the index of a bin :math:`i`,
    the coefficients :math:`a_{k}` of the Fourier series and :math:`k` as the
    number of coefficents`. The free energy is calculated in the bin center.

    For the free energy the coefficient it is assumed that :math:`a_{0} = 0`.

    Parameters
    ----------
    data_link : string
        Data link to the pickle data from :func:`Sample.init_diffusion_mc`
    n_diff : integer, optional
        number of the Fourier coefficients for the diffusion profile
    n_df : integer, optional
        number of the Fourier coefficients for the free energy profile
    n_diff_radial : integer, optional
        number of the Fourier coefficients for the radial diffusion profile
    """

    def __init__(self, data_link, n_diff=6, n_df=10, n_diff_radial=6):

        # Inherit the variables from Model class
        super(CosineModel,self).__init__(data_link)

        # Set the model type
        self._model = "CosineModel"

        #Initialise the Cosinemodel
        self._n_diff = n_diff                                                   # number of diffusion profile coefficients
        self._n_df = n_df                                                       # number of free energy profile coefficients
        self._n_diff_radial = n_diff_radial                                     # number of radial diffusion profile coefficients

        # Initial model
        self.init_model()

        # Initial Profiles
        self.init_profiles()

        # Set basis of Fourier series
        self.cosine_model()


    def init_model(self):
        """
        This function initializes the coefficient list for the Fourier series
        and the profile list for the free energy and diffusion profile.
        It is used to reinitialize these lists at the beginning of a MC run.
        """

        # # Initialize the diffusion and free energy coefficient
        self._df_coeff = np.float64(np.zeros(self._n_df))                       # in dz**2/dt
        self._diff_coeff = np.float64(np.zeros(self._n_diff))                   # in dz**2/dt


        # # Set start diffusion profile
        self._diff_coeff = np.zeros((self._n_diff),float)
        self._diff_coeff[0] += (np.log(self._d0) - self._diff_unit)             # initialize diffusion profile with the guess value [A^2/ps]


    def cosine_model(self):
        """This function sets a Fourier Cosine Series Model for the MC Diffusion
        Calculation and determines the initialize profiles.
        """

        # create basis (for the free energy)
        self.create_basis_center()

    # create basis (for the free energy)
        self.create_basis_border()


        # Update diffusion profile
        self._diff_bin = self.calc_profile(self._diff_coeff,self._diff_basis)

        # Update free energy profile
        self._df_bin = self.calc_profile(self._df_coeff,self._df_basis)

        # Print for console
        print("\n-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print("----------------------------------------------------------------Initialize CosineModel-------------------------------------------------------------------------")
        print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        print("Model Inputs")

        # Set data list for panda table
        len_step_string = ', '.join(str(step) for step in self._len_step)
        data = [str("%.f" % self._bin_num),  len_step_string, str("%.2e" % (self._dt * 10**(-12))), str("%.f" % self._n_diff), str("%.f" % self._n_df), self._model, self._pbc, str("%.2e" % (self._d0 * (10**(-18))/(10**(-12))))]

        # Set pandas table
        df_model = pd.DataFrame(data,index=list(['Bin number','step length','frame length','nD','nF','model','pbc','guess diffusion (m2/s-1)']),columns=list(['Input']))

        # Print panda table with model inputs
        print(df_model)


    def create_basis_center(self):
        """
        This function creates the basis part of the Fourier series for the
        free energy and the radial diffusion profile.
        For a bin the basis is calculated with

        .. math::

            \\mathrm{basis} = \\cos \\left(\\frac{2\\pi k(i+0.5)}{n}\\right)

        hereby :math:`k` is the number of coefficients, :math:`i` is the
        bin index and :math:`n` is the number of the bins.

        """

        # Allocate a vector with bin_num entries
        x = np.arange(self._bin_num)

        # Calculate basis for Fourier cosine series
        basis_df = [np.cos(2 * k * np.pi *(x + 0.5) / self._bin_num) / (k + 1) for k in range(self._n_df)]                      # basis for the free energy profile
        basis_diff_radial = [np.cos(2 * k * np.pi *(x + 0.5) / self._bin_num) / (k + 1) for k in range(self._n_diff_radial)]    # basis for the radial energy profile

        # Transpose basis (is now a bin_num x ncos Matrix)
        self._df_basis = np.array(basis_df).transpose()
        self._diff_radial_basis = np.array(basis_diff_radial).transpose()


    def create_basis_border(self):
        """
        This function creates the basis part in every bin of the Fourier series
        for the Diffusion :math:`\\ln \\ (D)`.
        At the bin border the basis is calculated with

        .. math::

            \\mathrm{basis} = \\cos \\left(\\frac{2\\pi ki}{n}\\right)

        hereby :math:`k` is the number of coefficients, :math:`i` is the bin
        index and :math:`n` is the number of the bins.
        """
        # Allocate a vector with bin_num entries
        x = np.arange(self._bin_num)

        # Calculate basis for Fourier cosine series
        basis = [np.cos(2 * k * np.pi * (x + 1.) / self._bin_num) / (k + 1) for k in range(self._n_diff)]

        # Transpose basis (is now a bin_num x ncos Matrix)
        self._diff_basis = np.array(basis).transpose()

class StepModel(Model):
    """This class sets the Step Model to calculate the free energy profile and
    the diffusion profile. This model based on a spline calculation.
    In contrast to the Cosine Model the determined profile have not the typical
    oscillation and recieves a profile which is better interpretable.

    .. math::

        \\ln \\left(D_{i+\\frac{1}{2}}\\right) = \\mathrm{coeff} \\cdot \\mathrm{basis}_{\\mathrm{diff}}

    .. math::

        F_i = \\mathrm{coeff} \\cdot \\mathrm{basis}_{\\mathrm{df}}

    Parameters
    ----------
    data_link : string
        Data link to the pickle data from :func:`init_diffusion_mc`
    n_diff : integer, optional
        number of the Fourier coefficients for the diffusion profile
    n_df : integer, optional
        number of the Fourier coefficients for the free energy profile
    n_diff_radial : integer, optional
        number of the Fourier coefficients for the radial diffusion profile

    """

    def __init__(self,data_link,n_diff=6, n_df=10, n_diff_radial=6):

        # Inherit the variables from Model class
        super(StepModel,self).__init__(data_link)

        # Set the model type
        self._model = "Step Model"

        # Set the number of coefficients for the step model
        self._n_diff = n_diff                                                   # number of diffusion profile coefficients
        self._n_df = n_df                                                       # number of free energy profile coefficien
        self._n_diff_radial = n_diff_radial                                     # number of radial diffusion profile coeff

        # Initial model
        self.init_model()

        # Initial Profiles
        self.init_profiles()

        # Set basis of Step Model
        self.step_model()

    def init_model(self):
        """
        This function initializes the coefficient list for the Step Model and
        the profile list for the free energy and diffusion profile. It is used
        to reinitializes these lists for every lag time calculation.
        """

        # # Initialize the diffusion and free energy coefficient
        self._df_coeff = np.float64(np.zeros(self._n_df))
        self._diff_coeff = np.float64(np.zeros(self._n_diff))
        self._diff_radial_coeff = np.float64(np.zeros(self._n_diff))

        # Calculate dz
        dx_df = self._bin_num /2. /self._n_df
        dx_diff = self._bin_num /2. /self._n_diff
        dx_diff_radial = self._bin_num_rad /2. /self._n_diff_radial

        self._df_x0 = np.arange(0, self._n_df * dx_df, dx_df)
        self._diff_x0 = np.arange(0, self._n_diff * dx_diff, dx_diff)
        self._diff_radial_x0 = np.arange(0, self._n_diff_radial * dx_diff_radial, dx_diff_radial)

        # # Set start diffusion profile
        self._diff_coeff[0] += (np.log(self._d0) - self._diff_unit)                  # initialize diffusion profile with the guess value [A^2/ps]
        self._diff_radial_coeff[0] += (np.log(self._d0) - self._diff_radial_unit)    # initialize diffusion profile with the guess value [A^2/ps]

    def step_model(self):
        """This function set a Step Model for the MC Diffusion Calculation
        and determine the initialize profiles.
        """

        # create basis (for the free energy)
        self.create_basis_center()

        # create basis (for the free energy)
        self.create_basis_border()

        # Update diffusion profile
        self._diff_bin = self.calc_profile(self._diff_coeff,self._diff_basis)

        # Update free energy profile
        self._df_bin = self.calc_profile(self._df_coeff,self._df_basis)

        # Update radial diffusion profile
        self._diff_radial_bin = self.calc_profile(self._diff_radial_coeff,self._diff_radial_basis)

    def create_basis_center(self):
        """
        This function creates the basis part in every bin of the Step model for
        the free energy and the radial diffusion profile. The following
        explanation is for the free energy profile. For the radial diffusion
        profile the number of free energy coefficients :math:`n_{df}` has to
        exchange with :math:`n_{diff_radial}`. The Dimension of the basis matrix
        is :math:`n_{\\mathrm{bin}} \\times n_{\\mathrm{df}}`. For a bin the basis is calculated with

        .. math::

            \\mathrm{basis} = \\begin{cases}
                            1 & (\\mathrm{bin}+0.5)\\geq \\Delta x\ \\& \ (\\mathrm{bin}+0.5)\\leq n_{\\mathrm{bin}}-\\Delta x \\\\
                            0 & \\mathrm{else}                                 \\
                    \\end{cases}

        hereby is :math:`\\mathrm{bin} = [0,...,n_{bin}]` with
        :math:`n_{\\mathrm{bin}}` as the number of the bins. The variable
        :math:`\\Delta x` is define by

        .. math::

            \\Delta x = \\left [ 0,i \\cdot \\frac{n_{\\mathrm{bin}}}{n_{\\mathrm{df}} \\cdot 2},\\frac{n_{\\mathrm{bin}}}{2} \\right ]

        with :math:`i = [1,...,n_{\\mathrm{df}}-1]`.

        """

        # Calculated the basis in the center of a bin
        x = np.arange(self._bin_num)+0.5
        x_rad = np.arange(self._bin_num_rad)+0.5
        basis = [np.where((x>=i) & (x<=self._bin_num-i),1.,0.) for i in self._df_x0]
        basis_rad = [np.where((x_rad>=i) & (x_rad<=self._bin_num_rad-i),1.,0.) for i in self._diff_radial_x0]

        # Transpose basis (is now a bin_num x ncos Matrix)
        self._df_basis = np.array(basis).transpose()
        self._diff_radial_basis = np.array(basis_rad).transpose()

    def create_basis_border(self):
        """
        This function creates the basis part in every bin of the Step model for
        the diffusion profile.
        The dimension of the basis matrix is :math:`n_{bin} \\times n_{diff}`.
        At the bin border the basis is calculated with

        .. math::

            \\mathrm{basis} = \\begin{cases}
                            1 & (\\mathrm{bin}+1)\\geq \\Delta x\ \\& \ (\\mathrm{bin}+1)\\leq n_{\\mathrm{bin}}-\\Delta x \\\\
                            0 &  \\mathrm{else}                                 \\
                    \\end{cases}
        hereby is :math:`bin = [0,...,n_{\\mathrm{bin}}]` with
        :math:`n_{\\mathrm{bin}}` as the number of the bins. The variable
        :math:`\\Delta x` is define by

        .. math::

            \\Delta x = \\left [ 0,i \\cdot \\frac{n_{\\mathrm{bin}}}{n_{\\mathrm{diff}} \\cdot 2},\\frac{n_{\\mathrm{bin}}}{2} \\right ]

        with :math:`i = [1,...,n_{\\mathrm{diff}}-1]`.
        """

        # Calculated the basis in the border of a bin
        x = np.arange(self._bin_num)+1.
        basis = [np.where((x>=i) & (x<=self._bin_num-i),1.,0.) for i in self._diff_x0]

        # Transpose basis (is now a bin_num x ncos Matrix)
        self._diff_basis = np.array(basis).transpose()
