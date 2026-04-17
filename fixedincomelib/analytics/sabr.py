from enum import Enum
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from scipy.stats import norm
from fixedincomelib.analytics.european_options import (
    CallOrPut,
    SimpleMetrics,
    EuropeanOptionAnalytics,
)


class SabrMetrics(Enum):

    # parameters
    ALPHA = "alpha"
    BETA = "beta"
    NU = "nu"
    RHO = "rho"

    # risk
    DALPHA = "dalpha"
    DLNSIGMA = "dlnsigma"
    DNORMALSIGMA = "dnormalsigma"
    DBETA = "dbeta"
    DRHO = "drho"
    DNU = "dnu"
    DFORWARD = "dforward"
    DSTRIKE = "dstrike"
    DTTE = "dtte"
    DSTRIKESTRIKE = "dstrikestrike"

    # (alpha, beta, nu, rho, forward, strike, tte) => \sigma_k
    D_LN_SIGMA_D_FORWARD = "d_ln_sigma_d_forward"
    D_LN_SIGMA_D_STRIKE = "d_ln_sigma_d_strike"
    D_LN_SIGMA_D_TTE = "d_ln_sigma_d_tte"
    D_LN_SIGMA_D_ALPHA = "d_ln_sigma_d_alpha"
    D_LN_SIGMA_D_BETA = "d_ln_sigma_d_beta"
    D_LN_SIGMA_D_NU = "d_ln_sigma_d_nu"
    D_LN_SIGMA_D_RHO = "d_ln_sigma_d_rho"
    D_LN_SIGMA_D_STRIKESTRIKE = "d_ln_sigma_d_strike_strike"

    # (\sigma_ln_atm, f, tte, beta, nu, rho) => alpha
    D_ALPHA_D_LN_SIGMA_ATM = "d_alpha_d_ln_sigma_atm"
    D_ALPHA_D_FORWARD = "d_alpha_d_forward"
    D_ALPHA_D_TTE = "d_alpha_d_tte"
    D_ALPHA_D_BETA = "d_alpha_d_beta"
    D_ALPHA_D_NU = "d_alpha_d_nu"
    D_ALPHA_D_RHO = "d_alpha_d_rho"

    # (alpha, beta, nu, rho, f, tte) => \sigma_n_atm
    D_NORMAL_SIGMA_D_ALPHA = "d_normal_sigma_d_alpha"
    D_NORMAL_SIGMA_D_BETA = "d_normal_sigma_d_beta"
    D_NORMAL_SIGMA_D_NU = "d_normal_sigma_d_nu"
    D_NORMAL_SIGMA_D_RHO = "d_normal_sigma_d_rho"
    D_NORMAL_SIGMA_D_FORWARD = "d_normal_sigma_d_forward"
    D_NORMAL_SIGMA_D_TTE = "d_normal_sigma_d_tte"
    D_ALPHA_D_NORMAL_SIGMA_ATM = "d_alpha_d_normal_sigma_atm"

    @classmethod
    def from_string(cls, value: str) -> "SabrMetrics":
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError as e:
            raise ValueError(f"Invalid token: {value}") from e

    def to_string(self) -> str:
        return self.value


class SABRAnalytics:

    EPSILON = 1e-6

    ### parameters conversion

    # solver to back out lognormal vol from alpha and sensitivities
    # please implement the _vol_and_risk function to make this work
    @staticmethod
    def lognormal_vol_from_alpha(
        forward: float,
        strike: float,
        time_to_expiry: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
    ) -> Dict[SabrMetrics | SimpleMetrics, float]:

        res: Dict[Any, float] = {}

        ln_sigma, risks = SABRAnalytics._vol_and_risk(
            forward + shift, strike + shift, time_to_expiry, alpha, beta, rho, nu, calc_risk
        )
        res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL] = ln_sigma

        if len(risks) == 0:
            return res

        res.update(risks)
        return res

    @staticmethod
    def alpha_from_atm_lognormal_sigma(
        forward: float,
        time_to_expiry: float,
        sigma_atm_lognormal: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
        max_iter: Optional[int] = 50,
        tol: Optional[float] = 1e-12,
    ) -> Dict[SabrMetrics, float]:

        if forward + shift <= 0.0:
            raise ValueError("forward must be > 0")
        if time_to_expiry < 0.0:
            raise ValueError("time_to_expiry must be >= 0")
        if sigma_atm_lognormal <= 0.0:
            raise ValueError("sigma_atm_lognormal must be > 0")
        if abs(rho) >= 1.0:
            raise ValueError("rho must be in (-1,1)")
        if nu < 0.0:
            raise ValueError("nu must be >= 0")
        if not (0.0 <= beta <= 1.0):
            raise ValueError("beta should be in [0,1] for standard SABR usage")

        # newton + bisec fallback
        # root finding
        # f = F(alpha, theta) - ln_sigma = 0
        # where F is lognormal_vol_from_alpha
        # alpha^* = alpha(ln_sigma, theta)

        def _f_and_res(alpha_: float, with_risk: bool = False):
            out = SABRAnalytics.lognormal_vol_from_alpha(
                forward,
                forward,
                time_to_expiry,
                alpha_,
                beta,
                rho,
                nu,
                shift,
                with_risk,
            )
            return out[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL] - sigma_atm_lognormal, out

        this_res = None
        alpha = sigma_atm_lognormal * (forward + shift) ** (1.0 - beta)
        alpha = max(alpha, tol)

        alpha_lo = max(alpha * 0.5, tol)
        alpha_hi = max(alpha * 2.0, 2.0 * tol)
        f_lo, _ = _f_and_res(alpha_lo, False)
        f_hi, _ = _f_and_res(alpha_hi, False)
        for _ in range(max_iter):
            if f_lo * f_hi <= 0.0:
                break
            if f_lo > 0.0 and f_hi > 0.0:
                alpha_lo = max(alpha_lo * 0.5, tol)
                f_lo, _ = _f_and_res(alpha_lo, False)
            else:
                alpha_hi *= 2.0
                f_hi, _ = _f_and_res(alpha_hi, False)

        for _ in range(max_iter):
            this_f, this_res = _f_and_res(alpha, calc_risk)
            if abs(this_f) <= tol:
                break

            dfdalpha = None
            if (
                this_res is not None
                and SabrMetrics.D_LN_SIGMA_D_ALPHA in this_res
                and np.isfinite(this_res[SabrMetrics.D_LN_SIGMA_D_ALPHA])
            ):
                dfdalpha = this_res[SabrMetrics.D_LN_SIGMA_D_ALPHA]

            if dfdalpha is None or abs(dfdalpha) < 1e-14:
                bump = max(1e-6 * alpha, 1e-10)
                f_up, _ = _f_and_res(alpha + bump, False)
                f_dn, _ = _f_and_res(max(alpha - bump, tol), False)
                dfdalpha = (f_up - f_dn) / (2.0 * bump)

            use_newton = np.isfinite(dfdalpha) and abs(dfdalpha) > 1e-14
            alpha_new = alpha - this_f / dfdalpha if use_newton else np.nan

            if (
                not np.isfinite(alpha_new)
                or alpha_new <= tol
                or alpha_new < alpha_lo
                or alpha_new > alpha_hi
            ):
                alpha_new = 0.5 * (alpha_lo + alpha_hi)

            f_new, _ = _f_and_res(alpha_new, False)
            if f_lo * f_new <= 0.0:
                alpha_hi, f_hi = alpha_new, f_new
            else:
                alpha_lo, f_lo = alpha_new, f_new

            if abs(alpha_new - alpha) <= tol * max(1.0, alpha):
                alpha = alpha_new
                this_f, this_res = _f_and_res(alpha, calc_risk)
                if abs(this_f) <= tol:
                    break

            alpha = alpha_new
        else:
            raise RuntimeError("alpha_from_atm_lognormal_sigma: Newton did not converge")

        res: Dict[SabrMetrics, float] = {SabrMetrics.ALPHA: alpha}

        if calc_risk:

            # dalphad...
            # alpha^* = alpha(ln_sigma, theta, target_ln_sigma)
            # F(alpha(ln_sigma, theta), theta) = target_ln_sigma
            # using implicit function theorem
            # df/dalpha * dalpha/dln_sigma = 1 =>             dalpha / dln_sigma = 1 / df/dalpha
            # df/dalpha * dalpha/dtheta  + df/dtheta = 0 =>  dalpha / dtheta = - df/dtheta / df/dalpha
            if this_res is None:
                _, this_res = _f_and_res(alpha, True)
            dfdalpha = this_res[SabrMetrics.D_LN_SIGMA_D_ALPHA]
            if abs(dfdalpha) < 1e-14:
                raise RuntimeError(
                    "alpha_from_atm_lognormal_sigma: unstable derivative d_ln_sigma/d_alpha near solution"
                )

            # NOTE: at the ATM slice K = F, so the total derivative of sigma w.r.t. F
            # is the sum of the partials at fixed K and at fixed F.
            d_sigma_d_F_atm = (
                this_res[SabrMetrics.D_LN_SIGMA_D_FORWARD]
                + this_res[SabrMetrics.D_LN_SIGMA_D_STRIKE]
            )

            res[SabrMetrics.D_ALPHA_D_LN_SIGMA_ATM] = 1.0 / dfdalpha
            res[SabrMetrics.D_ALPHA_D_FORWARD] = -d_sigma_d_F_atm / dfdalpha
            res[SabrMetrics.D_ALPHA_D_TTE] = -this_res[SabrMetrics.D_LN_SIGMA_D_TTE] / dfdalpha
            res[SabrMetrics.D_ALPHA_D_BETA] = -this_res[SabrMetrics.D_LN_SIGMA_D_BETA] / dfdalpha
            res[SabrMetrics.D_ALPHA_D_NU] = -this_res[SabrMetrics.D_LN_SIGMA_D_NU] / dfdalpha
            res[SabrMetrics.D_ALPHA_D_RHO] = -this_res[SabrMetrics.D_LN_SIGMA_D_RHO] / dfdalpha

        return res

    # conversion to alpha from normal atm vol
    @staticmethod
    def alpha_from_atm_normal_sigma(
        forward: float,
        time_to_expiry: float,
        sigma_atm_normal: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: bool = False,
        max_iter: int = 50,
        tol: float = 1e-8,
    ) -> Dict[SabrMetrics, float]:
        """
        At ATM, convert normal vol -> lognormal vol, then solve alpha from lognormal atm vol.
        Sensitivities via chain rule.
        """

        # g: (sigma_N, F, T) -> sigma_LN    (european_options.normal_vol_to_lognormal_vol at ATM)
        conv = EuropeanOptionAnalytics.normal_vol_to_lognormal_vol(
            forward,
            forward,
            time_to_expiry,
            sigma_atm_normal,
            calc_risk,
            shift,
            tol,
        )
        sigma_ln_atm = conv[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]

        # h: (sigma_LN, F, T, beta, rho, nu) -> alpha
        alpha_res = SABRAnalytics.alpha_from_atm_lognormal_sigma(
            forward,
            time_to_expiry,
            sigma_ln_atm,
            beta,
            rho,
            nu,
            shift,
            calc_risk,
            max_iter,
            max(tol, 1e-12),
        )

        final_res: Dict[SabrMetrics, float] = {
            SabrMetrics.ALPHA: alpha_res[SabrMetrics.ALPHA]
        }

        if calc_risk:
            dh_d_sigma_ln = alpha_res[SabrMetrics.D_ALPHA_D_LN_SIGMA_ATM]
            dg_d_sigma_n = conv[SimpleMetrics.D_LN_VOL_D_N_VOL]
            # atm total F derivative: partial at fixed K + partial at fixed F (since K = F)
            dg_dF_atm = (
                conv[SimpleMetrics.D_LN_VOL_D_FORWARD]
                + conv[SimpleMetrics.D_LN_VOL_D_STRIKE]
            )
            dg_dT = conv[SimpleMetrics.D_LN_VOL_D_TTE]

            final_res[SabrMetrics.D_ALPHA_D_NORMAL_SIGMA_ATM] = (
                dh_d_sigma_ln * dg_d_sigma_n
            )
            final_res[SabrMetrics.D_ALPHA_D_FORWARD] = (
                dh_d_sigma_ln * dg_dF_atm + alpha_res[SabrMetrics.D_ALPHA_D_FORWARD]
            )
            final_res[SabrMetrics.D_ALPHA_D_TTE] = (
                dh_d_sigma_ln * dg_dT + alpha_res[SabrMetrics.D_ALPHA_D_TTE]
            )
            final_res[SabrMetrics.D_ALPHA_D_BETA] = alpha_res[SabrMetrics.D_ALPHA_D_BETA]
            final_res[SabrMetrics.D_ALPHA_D_RHO] = alpha_res[SabrMetrics.D_ALPHA_D_RHO]
            final_res[SabrMetrics.D_ALPHA_D_NU] = alpha_res[SabrMetrics.D_ALPHA_D_NU]

        return final_res

    @staticmethod
    def atm_normal_sigma_from_alpha(
        forward: float,
        time_to_expiry: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
        tol: Optional[float] = 1e-8,
    ) -> Dict[SabrMetrics | SimpleMetrics, float]:
        """
        ATM SABR: alpha -> lognormal atm vol (Hagan) -> normal atm vol (BS-to-Bachelier).
        """
        ln_res = SABRAnalytics.lognormal_vol_from_alpha(
            forward,
            forward,
            time_to_expiry,
            alpha,
            beta,
            rho,
            nu,
            shift,
            calc_risk,
        )
        sigma_ln = ln_res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]

        conv = EuropeanOptionAnalytics.lognormal_vol_to_normal_vol(
            forward,
            forward,
            time_to_expiry,
            sigma_ln,
            calc_risk,
            shift,
            tol,
        )

        final_res: Dict[Any, float] = {
            SimpleMetrics.IMPLIED_NORMAL_VOL: conv[SimpleMetrics.IMPLIED_NORMAL_VOL]
        }

        if calc_risk:
            d_n_d_ln = conv[SimpleMetrics.D_N_VOL_D_LN_VOL]
            d_ln_dF_atm = (
                ln_res[SabrMetrics.D_LN_SIGMA_D_FORWARD]
                + ln_res[SabrMetrics.D_LN_SIGMA_D_STRIKE]
            )
            d_g_dF_atm = (
                conv[SimpleMetrics.D_N_VOL_D_FORWARD]
                + conv[SimpleMetrics.D_N_VOL_D_STRIKE]
            )
            d_g_dT = conv[SimpleMetrics.D_N_VOL_D_TTE]
            d_ln_dT = ln_res[SabrMetrics.D_LN_SIGMA_D_TTE]

            final_res[SabrMetrics.D_NORMAL_SIGMA_D_ALPHA] = (
                d_n_d_ln * ln_res[SabrMetrics.D_LN_SIGMA_D_ALPHA]
            )
            final_res[SabrMetrics.D_NORMAL_SIGMA_D_BETA] = (
                d_n_d_ln * ln_res[SabrMetrics.D_LN_SIGMA_D_BETA]
            )
            final_res[SabrMetrics.D_NORMAL_SIGMA_D_NU] = (
                d_n_d_ln * ln_res[SabrMetrics.D_LN_SIGMA_D_NU]
            )
            final_res[SabrMetrics.D_NORMAL_SIGMA_D_RHO] = (
                d_n_d_ln * ln_res[SabrMetrics.D_LN_SIGMA_D_RHO]
            )
            final_res[SabrMetrics.D_NORMAL_SIGMA_D_FORWARD] = (
                d_n_d_ln * d_ln_dF_atm + d_g_dF_atm
            )
            final_res[SabrMetrics.D_NORMAL_SIGMA_D_TTE] = d_n_d_ln * d_ln_dT + d_g_dT

        return final_res

    ### option pricing

    @staticmethod
    def european_option_alpha(
        forward: float,
        strike: float,
        time_to_expiry: float,
        opt_type: CallOrPut,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
    ):

        ### pv
        ln_sigma_and_sensitivities = SABRAnalytics.lognormal_vol_from_alpha(
            forward, strike, time_to_expiry, alpha, beta, rho, nu, shift, calc_risk
        )
        ln_iv = ln_sigma_and_sensitivities[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]
        value_and_sensitivities = EuropeanOptionAnalytics.european_option_log_normal(
            forward + shift, strike + shift, time_to_expiry, ln_iv, opt_type, calc_risk
        )

        ### risk(analytic)
        if calc_risk:
            ## first order risks
            dvdsigma = value_and_sensitivities[SimpleMetrics.VEGA]
            value_and_sensitivities.pop(SimpleMetrics.VEGA)
            # delta
            value_and_sensitivities[SimpleMetrics.DELTA] += (
                dvdsigma * ln_sigma_and_sensitivities[SabrMetrics.D_LN_SIGMA_D_FORWARD]
            )
            # theta
            value_and_sensitivities[SimpleMetrics.THETA] -= (
                dvdsigma * ln_sigma_and_sensitivities[SabrMetrics.D_LN_SIGMA_D_TTE]
            )
            # sabr alpha/beta/nu/rho
            for key, risk in [
                (SabrMetrics.DALPHA, SabrMetrics.D_LN_SIGMA_D_ALPHA),
                (SabrMetrics.DBETA, SabrMetrics.D_LN_SIGMA_D_BETA),
                (SabrMetrics.DRHO, SabrMetrics.D_LN_SIGMA_D_RHO),
                (SabrMetrics.DNU, SabrMetrics.D_LN_SIGMA_D_NU),
            ]:
                value_and_sensitivities[key] = dvdsigma * ln_sigma_and_sensitivities[risk]
            # strike
            value_and_sensitivities[SimpleMetrics.STRIKE_RISK] += (
                dvdsigma * ln_sigma_and_sensitivities[SabrMetrics.D_LN_SIGMA_D_STRIKE]
            )

            ## second order risk (bump reval)
            v_base = value_and_sensitivities[SimpleMetrics.PV]
            # strike
            res_up = SABRAnalytics.lognormal_vol_from_alpha(
                forward, strike + SABRAnalytics.EPSILON, time_to_expiry, alpha, beta, rho, nu, shift
            )
            vol_up = res_up[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]
            v_up = EuropeanOptionAnalytics.european_option_log_normal(
                forward + shift,
                strike + shift + SABRAnalytics.EPSILON,
                time_to_expiry,
                vol_up,
                opt_type,
            )[SimpleMetrics.PV]

            res_dn = SABRAnalytics.lognormal_vol_from_alpha(
                forward, strike - SABRAnalytics.EPSILON, time_to_expiry, alpha, beta, rho, nu, shift
            )
            vol_dn = res_dn[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]
            v_dn = EuropeanOptionAnalytics.european_option_log_normal(
                forward + shift,
                strike + shift - SABRAnalytics.EPSILON,
                time_to_expiry,
                vol_dn,
                opt_type,
            )[SimpleMetrics.PV]
            value_and_sensitivities[SimpleMetrics.STRIKE_RISK_2] = (v_up - 2 * v_base + v_dn) / (
                SABRAnalytics.EPSILON**2
            )

            # gamma
            res_up = SABRAnalytics.lognormal_vol_from_alpha(
                forward + SABRAnalytics.EPSILON, strike, time_to_expiry, alpha, beta, rho, nu, shift
            )
            vol_up = res_up[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]
            v_up = EuropeanOptionAnalytics.european_option_log_normal(
                forward + shift + SABRAnalytics.EPSILON,
                strike + shift,
                time_to_expiry,
                vol_up,
                opt_type,
            )[SimpleMetrics.PV]
            res_dn = SABRAnalytics.lognormal_vol_from_alpha(
                forward - SABRAnalytics.EPSILON, strike, time_to_expiry, alpha, beta, rho, nu, shift
            )
            vol_dn = res_dn[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]
            v_dn = EuropeanOptionAnalytics.european_option_log_normal(
                forward + shift - SABRAnalytics.EPSILON,
                strike + shift,
                time_to_expiry,
                vol_dn,
                opt_type,
            )[SimpleMetrics.PV]
            value_and_sensitivities[SimpleMetrics.GAMMA] = (v_up - 2 * v_base + v_dn) / (
                SABRAnalytics.EPSILON**2
            )

        return value_and_sensitivities

    # Given function
    @staticmethod
    def european_option_ln_sigma(
        forward: float,
        strike: float,
        time_to_expiry: float,
        opt_type: CallOrPut,
        ln_sigma_atm: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
    ):

        ### pv
        alpha_and_sensitivities = SABRAnalytics.alpha_from_atm_lognormal_sigma(
            forward, time_to_expiry, ln_sigma_atm, beta, rho, nu, shift, calc_risk
        )
        alpha = alpha_and_sensitivities[SabrMetrics.ALPHA]
        value_and_sensitivities = SABRAnalytics.european_option_alpha(
            forward, strike, time_to_expiry, opt_type, alpha, beta, rho, nu, shift, calc_risk
        )

        ### risk
        if calc_risk:
            ## first order risks
            dvdalpha = value_and_sensitivities[SabrMetrics.DALPHA]
            value_and_sensitivities.pop(SabrMetrics.DALPHA)

            # delta
            value_and_sensitivities[SimpleMetrics.DELTA] += (
                dvdalpha * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_FORWARD]
            )
            # theta
            value_and_sensitivities[SimpleMetrics.THETA] -= (
                dvdalpha * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_TTE]
            )
            # ln_sigma
            value_and_sensitivities[SabrMetrics.DLNSIGMA] = (
                dvdalpha * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_LN_SIGMA_ATM]
            )
            # sabr beta/rho/nu
            for key, risk in [
                (SabrMetrics.DBETA, SabrMetrics.D_ALPHA_D_BETA),
                (SabrMetrics.DRHO, SabrMetrics.D_ALPHA_D_RHO),
                (SabrMetrics.DNU, SabrMetrics.D_ALPHA_D_NU),
            ]:
                value_and_sensitivities[key] += dvdalpha * alpha_and_sensitivities[risk]

            ## second order risk (bump reval)
            v_base = value_and_sensitivities[SimpleMetrics.PV]

            # gamma
            res_up = SABRAnalytics.alpha_from_atm_lognormal_sigma(
                forward + SABRAnalytics.EPSILON, time_to_expiry, ln_sigma_atm, beta, rho, nu, shift
            )
            alpha_up = res_up[SabrMetrics.ALPHA]
            v_up = SABRAnalytics.european_option_alpha(
                forward + SABRAnalytics.EPSILON,
                strike,
                time_to_expiry,
                opt_type,
                alpha_up,
                beta,
                rho,
                nu,
                shift,
            )[SimpleMetrics.PV]
            res_dn = SABRAnalytics.alpha_from_atm_lognormal_sigma(
                forward - SABRAnalytics.EPSILON, time_to_expiry, ln_sigma_atm, beta, rho, nu, shift
            )
            alpha_dn = res_dn[SabrMetrics.ALPHA]
            v_dn = SABRAnalytics.european_option_alpha(
                forward - SABRAnalytics.EPSILON,
                strike,
                time_to_expiry,
                opt_type,
                alpha_dn,
                beta,
                rho,
                nu,
                shift,
            )[SimpleMetrics.PV]
            value_and_sensitivities[SimpleMetrics.GAMMA] = (v_up - 2 * v_base + v_dn) / (
                SABRAnalytics.EPSILON**2
            )

        return value_and_sensitivities

    # European call/put SABR risk with normal vol input
    @staticmethod
    def european_option_normal_sigma(
        forward: float,
        strike: float,
        time_to_expiry: float,
        opt_type: CallOrPut,
        normal_sigma_atm: float,
        beta: float,
        rho: float,
        nu: float,
        shift: Optional[float] = 0.0,
        calc_risk: Optional[bool] = False,
    ):
        """
        Price + risk under SABR parameterized by atm normal vol.
        Mirrors european_option_ln_sigma but routes through alpha_from_atm_normal_sigma.
        """
        # step 1: alpha from atm normal vol
        alpha_and_sensitivities = SABRAnalytics.alpha_from_atm_normal_sigma(
            forward, time_to_expiry, normal_sigma_atm, beta, rho, nu, shift, calc_risk
        )
        alpha = alpha_and_sensitivities[SabrMetrics.ALPHA]

        value_and_sensitivities = SABRAnalytics.european_option_alpha(
            forward, strike, time_to_expiry, opt_type, alpha, beta, rho, nu, shift, calc_risk
        )

        if calc_risk:
            dvdalpha = value_and_sensitivities[SabrMetrics.DALPHA]
            value_and_sensitivities.pop(SabrMetrics.DALPHA)

            # delta (chain in dalpha/dF)
            value_and_sensitivities[SimpleMetrics.DELTA] += (
                dvdalpha * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_FORWARD]
            )
            # theta (chain in dalpha/dT)
            value_and_sensitivities[SimpleMetrics.THETA] -= (
                dvdalpha * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_TTE]
            )
            # dnormalsigma
            value_and_sensitivities[SabrMetrics.DNORMALSIGMA] = (
                dvdalpha
                * alpha_and_sensitivities[SabrMetrics.D_ALPHA_D_NORMAL_SIGMA_ATM]
            )
            # sabr beta/rho/nu (already contain dv/dtheta_direct; add dv/dalpha * dalpha/dtheta)
            for key, risk in [
                (SabrMetrics.DBETA, SabrMetrics.D_ALPHA_D_BETA),
                (SabrMetrics.DRHO, SabrMetrics.D_ALPHA_D_RHO),
                (SabrMetrics.DNU, SabrMetrics.D_ALPHA_D_NU),
            ]:
                value_and_sensitivities[key] += (
                    dvdalpha * alpha_and_sensitivities[risk]
                )

            # gamma via bump-reval, re-solving alpha to keep atm normal vol constant
            v_base = value_and_sensitivities[SimpleMetrics.PV]

            res_up = SABRAnalytics.alpha_from_atm_normal_sigma(
                forward + SABRAnalytics.EPSILON,
                time_to_expiry,
                normal_sigma_atm,
                beta,
                rho,
                nu,
                shift,
            )
            alpha_up = res_up[SabrMetrics.ALPHA]
            v_up = SABRAnalytics.european_option_alpha(
                forward + SABRAnalytics.EPSILON,
                strike,
                time_to_expiry,
                opt_type,
                alpha_up,
                beta,
                rho,
                nu,
                shift,
            )[SimpleMetrics.PV]

            res_dn = SABRAnalytics.alpha_from_atm_normal_sigma(
                forward - SABRAnalytics.EPSILON,
                time_to_expiry,
                normal_sigma_atm,
                beta,
                rho,
                nu,
                shift,
            )
            alpha_dn = res_dn[SabrMetrics.ALPHA]
            v_dn = SABRAnalytics.european_option_alpha(
                forward - SABRAnalytics.EPSILON,
                strike,
                time_to_expiry,
                opt_type,
                alpha_dn,
                beta,
                rho,
                nu,
                shift,
            )[SimpleMetrics.PV]

            value_and_sensitivities[SimpleMetrics.GAMMA] = (
                v_up - 2.0 * v_base + v_dn
            ) / (SABRAnalytics.EPSILON**2)

        return value_and_sensitivities

   

    ### helpers

    @staticmethod
    def w2_risk(F, K, T, a, b, r, n) -> Dict:

        risk = {}

        risk[SabrMetrics.DALPHA] = (1 - b) ** 2 / 12 * a / (F * K) ** (1 - b) + b * r * n / (
            4 * (F * K) ** ((1 - b) / 2)
        )
        risk[SabrMetrics.DBETA] = (
            1 / 12 * (b - 1) * a**2 * (F * K) ** (b - 1)
            + 1 / 24 * (b - 1) ** 2 * a**2 * (F * K) ** (b - 1) * np.log(F * K)
            + 1 / 4 * a * r * n * (F * K) ** ((b - 1) / 2)
            + 1 / 8 * a * b * r * n * (F * K) ** ((b - 1) / 2) * np.log(F * K)
        )
        risk[SabrMetrics.DRHO] = 1 / 4 * a * b * n * (F * K) ** ((b - 1) / 2) - 1 / 4 * n**2 * r
        risk[SabrMetrics.DNU] = (
            1 / 4 * a * b * r * (F * K) ** ((b - 1) / 2) + 1 / 6 * n - 1 / 4 * r**2 * n
        )
        risk[SabrMetrics.DFORWARD] = (b - 1) ** 3 / 24 * a**2 * (F * K) ** (
            b - 2
        ) * K + a * r * n * b * (b - 1) / 8 * K ** ((b - 1) / 2) * F ** ((b - 3) / 2)

        risk[SabrMetrics.DSTRIKE] = (b - 1) ** 3 / 24 * a**2 * F ** (b - 1) * K ** (
            b - 2
        ) + a * b * r * n * (b - 1) / 8 * F ** ((b - 1) / 2) * K ** ((b - 3) / 2)

        risk[SabrMetrics.DSTRIKESTRIKE] = (b - 1) ** 3 / 24 * a**2 * (b - 2) * F ** (
            b - 1
        ) * K ** (b - 3) + a * b * r * n / 16 * (b - 1) * (b - 3) * F ** ((b - 1) / 2) * K ** (
            (b - 5) / 2
        )

        return risk

    @staticmethod
    def w1_risk(F, K, T, a, b, r, n) -> Dict:

        log_FK = np.log(F / K)

        risk = {}
        risk[SabrMetrics.DALPHA] = 0.0
        risk[SabrMetrics.DBETA] = (b - 1) / 12.0 * log_FK**2 + (b - 1) ** 3 / 480 * log_FK**4
        risk[SabrMetrics.DRHO] = 0.0
        risk[SabrMetrics.DNU] = 0.0
        risk[SabrMetrics.DFORWARD] = (b - 1) ** 2 / 12 * log_FK / F + (
            b - 1
        ) ** 4 / 480 / F * log_FK**3
        risk[SabrMetrics.DSTRIKE] = (
            -((b - 1) ** 2) / 12 * log_FK / K - (b - 1) ** 4 / 480 / K * log_FK**3
        )
        risk[SabrMetrics.DSTRIKESTRIKE] = (
            (b - 1) ** 2 / 12 / K**2
            + (b - 1) ** 2 / 12 * log_FK / K**2
            + (b - 1) ** 4 / 160 * log_FK**2 / K**2
            + (b - 1) ** 4 / 480 * log_FK**3 / K**2
        )

        return risk

    @staticmethod
    def z_risk(F, K, T, a, b, r, n) -> Dict:

        log_FK = np.log(F / K)
        fk = (F * K) ** ((1 - b) / 2)
        # z = n / a * log_FK * fk

        risk = {}
        risk[SabrMetrics.DALPHA] = -n / a * log_FK * fk / a
        risk[SabrMetrics.DBETA] = -1.0 / 2 * n / a * log_FK * fk * np.log(F * K)
        risk[SabrMetrics.DRHO] = 0.0
        risk[SabrMetrics.DNU] = 1.0 / a * log_FK * fk
        risk[SabrMetrics.DFORWARD] = (
            n * (1 - b) * K / 2 / a * (F * K) ** ((-b - 1) / 2) * log_FK + n / a * fk / F
        )
        risk[SabrMetrics.DSTRIKE] = (
            n * F * (1 - b) / 2 / a * log_FK * (F * K) ** ((-b - 1) / 2) - n / a * fk / K
        )
        risk[SabrMetrics.DSTRIKESTRIKE] = (
            n / a * F ** ((1 - b) / 2) * K ** ((-b - 3) / 2) * (log_FK * (b**2 - 1) / 4 + b)
        )

        return risk

    @staticmethod
    def x_risk(F, K, T, a, b, r, n) -> Dict:

        logFK = np.log(F / K)
        fk = (F * K) ** ((1 - b) / 2)
        z = n / a * fk * logFK
        dx_dz = 1 / np.sqrt(1 - 2 * r * z + z**2)

        risk = {}
        risk_z = SABRAnalytics.z_risk(F, K, T, a, b, r, n)

        risk[SabrMetrics.DALPHA] = dx_dz * risk_z[SabrMetrics.DALPHA]
        risk[SabrMetrics.DBETA] = dx_dz * risk_z[SabrMetrics.DBETA]
        risk[SabrMetrics.DRHO] = 1 / (1 - r) + (-z * dx_dz - 1) / (1 / dx_dz + z - r)
        risk[SabrMetrics.DNU] = dx_dz * risk_z[SabrMetrics.DNU]
        risk[SabrMetrics.DFORWARD] = dx_dz * risk_z[SabrMetrics.DFORWARD]
        risk[SabrMetrics.DSTRIKE] = dx_dz * risk_z[SabrMetrics.DSTRIKE]

        risk[SabrMetrics.DSTRIKESTRIKE] = (r - z) * dx_dz**3 * (
            risk_z[SabrMetrics.DSTRIKE] ** 2
        ) + dx_dz * risk_z[SabrMetrics.DSTRIKESTRIKE]

        return risk

    @staticmethod
    def C_risk(F, K, T, a, b, r, n) -> Dict:

        log_FK = np.log(F / K)
        fk = (F * K) ** ((1 - b) / 2)

        z = n / a * log_FK * fk
        risk = {}

        C0 = 1.0
        C1 = -r / 2.0
        C2 = -(r**2) / 4.0 + 1.0 / 6.0
        C3 = -(1.0 / 4.0 * r**2 - 5.0 / 24.0) * r
        C4 = -5.0 / 16.0 * r**4 + 1.0 / 3.0 * r**2 - 17.0 / 360.0
        C5 = -(7.0 / 16.0 * r**4 - 55.0 / 96.0 * r**2 + 37.0 / 240.0) * r

        dC_dz = C1 + 2 * C2 * z + 3 * C3 * z**2 + 4 * C4 * z**3 + 5 * C5 * z**4
        dC2_dz2 = 2 * C2 + 6 * C3 * z + 12 * C4 * z**2 + 20 * C5 * z**3

        risk[SabrMetrics.DRHO] = (
            -1.0 / 2 * z
            + 5.0 / 24 * z**3
            - 37.0 / 240 * z**5
            - 1.0 / 2 * z**2 * r
            + 2.0 / 3 * z**4 * r
            - 3.0 / 4 * z**3 * r**2
            + 55.0 / 32 * z**5 * r**2
            - 5.0 / 4 * z**4 * r**3
            - 35.0 / 16 * z**5 * r**4
        )
        risk_z = SABRAnalytics.z_risk(F, K, T, a, b, r, n)

        risk[SabrMetrics.DALPHA] = dC_dz * risk_z[SabrMetrics.DALPHA]
        risk[SabrMetrics.DBETA] = dC_dz * risk_z[SabrMetrics.DBETA]
        risk[SabrMetrics.DNU] = dC_dz * risk_z[SabrMetrics.DNU]
        risk[SabrMetrics.DFORWARD] = dC_dz * risk_z[SabrMetrics.DFORWARD]
        risk[SabrMetrics.DSTRIKE] = dC_dz * risk_z[SabrMetrics.DSTRIKE]
        risk[SabrMetrics.DSTRIKESTRIKE] = (
            dC_dz * risk_z[SabrMetrics.DSTRIKESTRIKE] + dC2_dz2 * risk_z[SabrMetrics.DSTRIKE] ** 2
        )
        return risk

    @staticmethod
    def _vol_and_risk(
        F, K, T, a, b, r, n, calc_risk=False, z_cut=1e-2
    ) -> Tuple[float, Dict[SabrMetrics, float]]:
        """
        Hagan-Lesniewski SABR lognormal vol and analytical greeks.

        sigma_LN = (a / (F*K)^((1-b)/2)) * (z / x(z)) / w1 * (1 + w2 * T)

        Around z ~ 0, z/x(z) is replaced by the 5-th order Taylor expansion C(z).
        """

        log_FK = np.log(F / K)
        fk = (F * K) ** ((1 - b) / 2)
        greeks: Dict[SabrMetrics, float] = {}

        z = n / a * log_FK * fk
        w1 = (
            1.0
            + (1.0 - b) ** 2 / 24.0 * log_FK**2
            + (1.0 - b) ** 4 / 1920.0 * log_FK**4
        )
        w2 = (
            (1.0 - b) ** 2 / 24.0 * a**2 / (F * K) ** (1.0 - b)
            + 0.25 * a * b * r * n / (F * K) ** ((1.0 - b) / 2.0)
            + (2.0 - 3.0 * r**2) / 24.0 * n**2
        )

        use_expansion = abs(z) < z_cut

        if use_expansion:
            C0 = 1.0
            C1 = -r / 2.0
            C2 = -(r**2) / 4.0 + 1.0 / 6.0
            C3 = -(0.25 * r**2 - 5.0 / 24.0) * r
            C4 = -5.0 / 16.0 * r**4 + 1.0 / 3.0 * r**2 - 17.0 / 360.0
            C5 = -(7.0 / 16.0 * r**4 - 55.0 / 96.0 * r**2 + 37.0 / 240.0) * r
            ratio = C0 + C1 * z + C2 * z**2 + C3 * z**3 + C4 * z**4 + C5 * z**5
            ratio_risk = SABRAnalytics.C_risk(F, K, T, a, b, r, n)
        else:
            # raw z/x(z)
            sqrt_term = np.sqrt(1.0 - 2.0 * r * z + z**2)
            x_val = np.log((sqrt_term + z - r) / (1.0 - r))
            # use dict aggregation: log(ratio) = log(z) - log(x)
            ratio = z / x_val
            # build ratio_risk in the same format as C_risk, so downstream code is uniform
            z_risk = SABRAnalytics.z_risk(F, K, T, a, b, r, n)
            x_risk = SABRAnalytics.x_risk(F, K, T, a, b, r, n)
            ratio_risk = {
                k: (z_risk[k] * x_val - z * x_risk[k]) / (x_val**2) for k in z_risk
            }

        sigma = (a / fk) * ratio * (1.0 + w2 * T) / w1

        if not calc_risk:
            return sigma, greeks

        w1r = SABRAnalytics.w1_risk(F, K, T, a, b, r, n)
        w2r = SABRAnalytics.w2_risk(F, K, T, a, b, r, n)

        inv_w1 = 1.0 / w1
        inv_ratio = 1.0 / ratio
        T_over = T / (1.0 + w2 * T)

        # d log(1/fk)/dtheta:
        #   log(1/fk) = -(1-b)/2 * log(F*K)
        #   d/db = +0.5 * log(F*K)
        #   d/dF = -(1-b)/(2F)
        #   d/dK = -(1-b)/(2K)
        # everything else: zero.
        d_log_inv_fk = {
            SabrMetrics.DALPHA: 0.0,
            SabrMetrics.DBETA: 0.5 * np.log(F * K),
            SabrMetrics.DNU: 0.0,
            SabrMetrics.DRHO: 0.0,
            SabrMetrics.DFORWARD: -(1.0 - b) / (2.0 * F),
            SabrMetrics.DSTRIKE: -(1.0 - b) / (2.0 * K),
        }
        d_log_a = {
            SabrMetrics.DALPHA: 1.0 / a,
            SabrMetrics.DBETA: 0.0,
            SabrMetrics.DNU: 0.0,
            SabrMetrics.DRHO: 0.0,
            SabrMetrics.DFORWARD: 0.0,
            SabrMetrics.DSTRIKE: 0.0,
        }

        # map helper-dict key -> output sabr-metrics key
        key_map = {
            SabrMetrics.DALPHA: SabrMetrics.D_LN_SIGMA_D_ALPHA,
            SabrMetrics.DBETA: SabrMetrics.D_LN_SIGMA_D_BETA,
            SabrMetrics.DNU: SabrMetrics.D_LN_SIGMA_D_NU,
            SabrMetrics.DRHO: SabrMetrics.D_LN_SIGMA_D_RHO,
            SabrMetrics.DFORWARD: SabrMetrics.D_LN_SIGMA_D_FORWARD,
            SabrMetrics.DSTRIKE: SabrMetrics.D_LN_SIGMA_D_STRIKE,
        }

        for k_in, k_out in key_map.items():
            d_log_sigma = (
                d_log_a[k_in]
                + d_log_inv_fk[k_in]
                + inv_ratio * ratio_risk.get(k_in, 0.0)
                + T_over * w2r.get(k_in, 0.0)
                - inv_w1 * w1r.get(k_in, 0.0)
            )
            greeks[k_out] = sigma * d_log_sigma

        # TTE: only enters via (1 + w2 * T)
        greeks[SabrMetrics.D_LN_SIGMA_D_TTE] = sigma * (w2 / (1.0 + w2 * T))

        # Strike-strike: bump re-val (good enough for downstream usage)
        bump = max(1e-6 * abs(K), 1e-8)
        sigma_up, _ = SABRAnalytics._vol_and_risk(
            F, K + bump, T, a, b, r, n, False, z_cut
        )
        sigma_dn, _ = SABRAnalytics._vol_and_risk(
            F, K - bump, T, a, b, r, n, False, z_cut
        )
        greeks[SabrMetrics.D_LN_SIGMA_D_STRIKESTRIKE] = (
            sigma_up - 2.0 * sigma + sigma_dn
        ) / (bump * bump)

        return sigma, greeks


    @staticmethod
    def pdf_and_cdf(
        forward: float,
        time_to_expiry: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
        grids: "List | np.ndarray",
        shift: Optional[float] = 0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute cdf / pdf of the (shifted) SABR forward at `time_to_expiry`
        on the strike grid `grids` using Breeden-Litzenberger:

            cdf(K) = 1 + dC/dK,   pdf(K) = d^2 C / dK^2
        """
        xs = np.asarray(grids, dtype=float)
        xs_shifted = xs + (shift or 0.0)
        cdf = np.zeros_like(xs, dtype=float)
        pdf = np.zeros_like(xs, dtype=float)

        for i, strike in enumerate(xs):
            res = SABRAnalytics.european_option_alpha(
                forward,
                float(strike),
                time_to_expiry,
                CallOrPut.CALL,
                alpha,
                beta,
                rho,
                nu,
                shift,
                True,
            )

            cdf[i] = 1.0 + res[SimpleMetrics.STRIKE_RISK]
            pdf[i] = res[SimpleMetrics.STRIKE_RISK_2]

        return xs, xs_shifted, cdf, pdf