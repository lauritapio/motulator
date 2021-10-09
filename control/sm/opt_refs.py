# pylint: disable=C0103

import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler

# %%
plt.rcParams['axes.prop_cycle'] = cycler(color='brgcmyk')
plt.rcParams['lines.linewidth'] = 1.
plt.rcParams.update({"text.usetex": True,
                     "font.family": "serif",
                     "font.sans-serif": ["Computer Modern Roman"]})


# %%
class OptimalLoci:
    """
    Computes MTPA and MTPV loci based on the motor parameters. The magnetic
    saturation is omitted. Note that these loci could be better implemented
    using normalized quantities.

    """

    def __init__(self, pars):
        """
        Parameters
        ----------
        pars : data object
            Motor parameters.

        """
        self.p = pars.p
        self.L_d = pars.L_d
        self.L_q = pars.L_q
        self.psi_f = pars.psi_f
        try:
            self.i_d_min = pars.i_d_min
        except AttributeError:
            pass

    def torque(self, i):
        """
        Computes the torque.

        Parameters
        ----------
        i : complex
            Stator current space vector.

        Returns
        -------
        T_M : float
            Electromagnetic torque.

        """
        psi = self.L_d*i.real + 1j*self.L_q*i.imag + self.psi_f
        T_M = 1.5*self.p*np.imag(i*np.conj(psi))
        return T_M

    def mtpa(self, i_max, N=20):
        """
        Compute the MTPA locus.

        Parameters
        ----------
        i_max : float
            Maximum current at which the locus is computed.
        N : int, optional
            Amount of points. The default is 20.

        Returns
        -------
        i : complex
            Current space vectors at the MTPA locus.

        """
        if self.psi_f == 0:
            # Magnetically linear SyRM
            i_d = np.linspace(0, i_max/np.sqrt(2), N)
            i_q = i_d
            # Minimum d-axis current
            i_d = (i_d < self.i_d_min)*self.i_d_min + (i_d >= self.i_d_min)*i_d
            i = i_d + 1j*i_q
        else:
            # IPMSM
            abs_i = np.linspace(0, i_max, N)
            i_a = self.psi_f/(self.L_d - self.L_q)
            i_d = -i_a/4 - np.sqrt((i_a**2)/16 + (abs_i**2)/2)
            i_q = np.sqrt(abs_i**2 - i_d**2)
            i = i_d + 1j*i_q
        return i

    def mtpv(self, i_max, N=20):
        if self.psi_f == 0:
            # Magnetically linear SyRM
            abs_i = np.linspace(0, i_max, N)
            i = abs_i*np.exp(1j*(np.arctan(self.L_d/self.L_q)))
        elif self.psi_f/self.L_d < i_max:
            # IPMSM
            abs_i = np.linspace(self.psi_f/self.L_d, i_max, N)
            k = self.L_q/(self.L_d - self.L_q)
            a = self.L_d**2 + self.L_q**2
            b = (2 + k)*self.psi_f*self.L_d
            c = (1 + k)*self.psi_f**2 - (self.L_q*abs_i)**2
            i_d = (-b - np.sqrt(b**2 - 4*a*c))/(2*a)
            i_q = np.sqrt(abs_i**2 - i_d**2)
            i = i_d + 1j*i_q
        return i

    def plot(self, i_max, base, N=20):
        """
        Plots control loci using per-unit quantities.

        Parameters
        ----------
        i_max : float
            Maximum current at which the loci are evaluated.
        base : object
            Base values.
        N : int, optional
            Amount of points to be evaluated. The default is 20.

        """
        # Disable LaTeX in plots
        plt.rcParams.update({"text.usetex": False})

        # Compute the current limit for plotting
        theta = np.linspace(0, np.pi, 2*N)
        i_lim = i_max*np.exp(1j*theta)

        # Compute the characteristics
        i_mtpa = self.mtpa(i_max, N)
        T_M_mtpa = self.torque(i_mtpa)
        i_mtpv = self.mtpv(i_max, N)
        if i_mtpv.any():  # is not None:
            T_M_mtpv = self.torque(i_mtpv)
        else:
            T_M_mtpv = None     # No MTPV in finite speed drives

        # Plot the i_d--i_q current plane
        fig1, ax = plt.subplots(1, 1)
        ax.plot(i_mtpa.real/base.i, i_mtpa.imag/base.i)
        try:
            ax.plot(i_mtpv.real/base.i, i_mtpv.imag/base.i)
        except AttributeError:
            pass
        ax.plot(-i_lim.real/base.i, i_lim.imag/base.i)
        ax.set_xlabel(r'$i_\mathrm{d}$ (p.u.)')
        ax.set_ylabel(r'$i_\mathrm{q}$ (p.u.)')
        ax.legend(['MTPA', 'MTPV'])
        if self.psi_f == 0:
            # SyRM
            ax.axis([0, i_max/base.i, 0, i_max/base.i])
        else:
            ax.axis([-i_max/base.i, 0, 0, i_max/base.i])
        ax.set_aspect('equal', 'box')

        # Plot i_d vs. T_M
        fig2, ax = plt.subplots(1, 1)
        ax.plot(T_M_mtpa/base.T, np.real(i_mtpa)/base.i)
        try:
            ax.plot(T_M_mtpv/base.T, i_mtpv.real/base.i)
        except AttributeError:
            pass
        ax.legend(['MTPA', 'MTPV'])
        ax.set_xlabel(r'$\tau_\mathrm{M}$ (p.u.)')
        ax.set_ylabel(r'$i_\mathrm{d}$ (p.u.)')
        ax.set_xlim(0, None)
        if self.psi_f == 0:
            # SyRM
            ax.set_ylim(0, None)
        else:
            ax.set_ylim(None, 0)
        ax.set_xlim(0, np.max(T_M_mtpa)/base.T)

        # Plot T_M vs. abs(i)
        fig3, ax = plt.subplots(1, 1)
        ax.plot(np.abs(i_mtpa)/base.i, T_M_mtpa/base.T)
        try:
            ax.plot(np.abs(i_mtpv)/base.i, T_M_mtpv/base.T)
        except TypeError:
            pass
        ax.legend(['MTPA', 'MTPV'])
        ax.set_xlabel(r'$i$ (p.u.)')
        ax.set_ylabel(r'$\tau_\mathrm{M}$ (p.u.)')
        ax.set_xlim(0, i_max//base.i)
        ax.set_ylim(0, None)
        return fig1, fig2, fig3
