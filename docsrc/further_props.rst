:orphan:

.. raw:: html

  <div class="container-fluid">
    <div class="row">
      <div class="col-md-10">
        <div style="text-align: justify; text-justify: inter-word;">

Further Properties
==================

Other properties can be implemented using available analysis
routines as a basis. Following analyses have also been implemented.

Adsorption
----------

Based on the Density analysis

.. code-block:: python

    import porems as pms
    import poreana as pa

    mol = pms.Molecule(inp="data/benzene.gro")

    sample = pa.Sample("data/pore_system_cylinder.obj", "data/traj_cylinder.xtc", mol, [])
    sample.init_density("output/dens.obj")
    sample.sample()


``Finished frame 2001/2001...``


Adsorption values within the pore can be calculated by counting the
instance of atoms inside and outside the pore system resulting into a
surface concentration within the pore and a volumetric concentration in
the bulk reservoirs

.. code-block:: python

    import pandas as pd

    ads = pa.adsorption.calculate("output/dens.obj")

    pd.DataFrame(ads)


.. raw:: html

    <div class="nboutput nblast">
      <div class="output_area rendered_html">
        <table border="1" class="dataframe">
          <thead>
            <tr>
              <th></th>
              <th style="text-align: center;">Conc</th>
              <th style="text-align: center;">Num</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th style="text-align: left;">mumol_m2</th>
              <td>0.153606</td>
              <td></td>
            </tr>
            <tr>
              <th style="text-align: left;">mmol_l</th>
              <td>139.490759</td>
              <td></td>
            </tr>
            <tr>
              <th style="text-align: left;">in</th>
              <td></td>
              <td>10.678661</td>
            </tr>
            <tr>
              <th style="text-align: left;">ex</th>
              <td></td>
              <td>18.785607</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>


Radius of Gyration
------------------

The radius of gyration can be calculated by sampling the molecule radius
inside and outside the pore using the gyration routine. The density
routine is also needed for weighting the radius based on the bin
density

.. code-block:: python

    import porems as pms
    import poreana as pa

    mol = pms.Molecule(inp="data/benzene.gro")

    sample = pa.Sample("data/pore_system_cylinder.obj", "data/traj_cylinder.xtc", mol, [])
    sample.init_density("output/dens.obj")
    sample.init_gyration("output/gyr.obj")
    sample.sample()


``Finished frame 2001/2001...``


The gyration radius can then be calculated and visualized as a function
of radius and distance inside and outside the pore respectively

.. code-block:: python

    import matplotlib.pyplot as plt

    plt.figure(figsize=(13, 4))

    ylim = [0, 0.2]

    plt.subplot(121)
    pa.gyration.plot("output/gyr.obj", "output/dens.obj", intent="in")
    plt.xlim([0, 2])
    plt.ylim(ylim)
    plt.xlabel("Distance from pore center (nm)")
    plt.ylabel(r"Radius of gyration (nm)")

    plt.subplot(122)
    pa.gyration.plot("output/gyr.obj", "output/dens.obj", intent="ex")
    plt.xlim([0, 5])
    plt.ylim(ylim)
    plt.xlabel("Distance from reservoir end (nm)")
    plt.ylabel(r"Radius of gyration (nm)")


.. figure::  /pics/gyration_01.svg
  :align: center
  :width: 100%
  :name: fig1


.. raw:: html

        </div>
      </div>
    </div>
  </div>
