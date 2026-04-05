import math
from enum import Enum
from typing import Optional, Dict
from scipy.stats import norm


class CallOrPut(Enum):

    CALL = "call"
    PUT = "put"
    INVALID = "invalid"

    @classmethod
    def from_string(cls, value: str) -> "CallOrPut":
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value


class SimpleMetrics(Enum):

    ## valuations
    PV = "pv"
    ## vol
    IMPLIED_NORMAL_VOL = "implied_normal_vol"
    IMPLIED_LOG_NORMAL_VOL = "implied_log_normal_vol"
    ## pv sensitivities
    DELTA = "delta"
    GAMMA = "gamma"
    VEGA = "vega"
    TTE_RISK = "tte_risk"
    STRIKE_RISK = "strike_risk"
    STRIKE_RISK_2 = "strike_risk_2"
    THETA = "theta"

    ## vol sensitivities
    # nv = f(ln_vol, f, k, tte)
    D_N_VOL_D_LN_VOL = "d_n_vol_d_ln_vol"
    D_N_VOL_D_FORWARD = "d_n_vol_d_forward"
    D_N_VOL_D_TTE = "d_n_vol_d_tte"
    D_N_VOL_D_STRIKE = "d_n_vol_d_strike"
    # ln_vol = f^-1(nv, f, k, tte)
    D_LN_VOL_D_N_VOL = "d_ln_vol_d_n_vol"
    D_LN_VOL_D_FORWARD = "d_ln_vol_d_forward"
    D_LN_VOL_D_TTE = "d_ln_vol_d_tte"
    D_LN_VOL_D_STRIKE = "d_ln_vol_d_strike"

    @classmethod
    def from_string(cls, value: str) -> "SimpleMetrics":
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value


class EuropeanOptionAnalytics:

    @staticmethod
    def european_option_log_normal(
        forward: float,
        strike: float,
        time_to_expiry: float,
        log_normal_sigma: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        calc_risk: Optional[bool] = False,
    ) -> Dict[SimpleMetrics, float]:
        """
        BS'76 pv and risk
        """

        if time_to_expiry <= 0 or log_normal_sigma <= 0:
            raise ValueError("Time to expiry and implied log-normal sigma must be positive")

        res: Dict[SimpleMetrics, float] = {}

        sqrt_t = math.sqrt(time_to_expiry)
        d1 = (math.log(forward / strike) + 0.5 * log_normal_sigma**2 * time_to_expiry) / (
            log_normal_sigma * sqrt_t
        )
        d2 = d1 - log_normal_sigma * sqrt_t

        # pricing
        if option_type == CallOrPut.CALL:
            res[SimpleMetrics.PV] = forward * norm.cdf(d1) - strike * norm.cdf(d2)
        elif option_type == CallOrPut.PUT:
            res[SimpleMetrics.PV] = strike * norm.cdf(-d2) - forward * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")

        # risk
        if calc_risk:
            res[SimpleMetrics.DELTA] = (
                norm.cdf(d1) if option_type == CallOrPut.CALL else norm.cdf(d1) - 1
            )
            res[SimpleMetrics.GAMMA] = norm.pdf(d1) / (forward * log_normal_sigma * sqrt_t)
            res[SimpleMetrics.VEGA] = forward * norm.pdf(d1) * sqrt_t
            res[SimpleMetrics.THETA] = -(forward * norm.pdf(d1) * log_normal_sigma) / (2 * sqrt_t)
            res[SimpleMetrics.TTE_RISK] = -res[SimpleMetrics.THETA]
            res[SimpleMetrics.STRIKE_RISK] = (
                -norm.cdf(d2) if option_type == CallOrPut.CALL else norm.cdf(-d2)
            )

        return res

    @staticmethod
    def european_option_normal(
        forward: float,
        strike: float,
        time_to_expiry: float,
        normal_sigma: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        calc_risk: Optional[bool] = False,
    ) -> Dict[SimpleMetrics, float]:
        """
        Bachelier formula
        """

        if time_to_expiry <= 0 or normal_sigma <= 0:
            raise ValueError("Time to expiry and implied normal sigma must be positive")

        res: Dict[SimpleMetrics, float] = {}

        sqrt_t = math.sqrt(time_to_expiry)
        d = (forward - strike) / (normal_sigma * sqrt_t)

        # pricing
        if option_type == CallOrPut.CALL:
            res[SimpleMetrics.PV] = (forward - strike) * norm.cdf(
                d
            ) + normal_sigma * sqrt_t * norm.pdf(d)
        elif option_type == CallOrPut.PUT:
            res[SimpleMetrics.PV] = (strike - forward) * norm.cdf(
                -d
            ) + normal_sigma * sqrt_t * norm.pdf(d)
        else:
            raise ValueError("option_type must be 'call' or 'put'")

        # risk
        if calc_risk:
            res[SimpleMetrics.DELTA] = (
                norm.cdf(d) if option_type == CallOrPut.CALL else norm.cdf(d) - 1
            )
            res[SimpleMetrics.GAMMA] = norm.pdf(d) / (normal_sigma * sqrt_t)
            res[SimpleMetrics.VEGA] = sqrt_t * norm.pdf(d)
            res[SimpleMetrics.THETA] = -0.5 * normal_sigma * norm.pdf(d) / sqrt_t
            res[SimpleMetrics.TTE_RISK] = -res[SimpleMetrics.THETA]
            res[SimpleMetrics.STRIKE_RISK] = (
                -norm.cdf(d) if option_type == CallOrPut.CALL else norm.cdf(-d)
            )

        return res

    @staticmethod
    def implied_lognormal_vol_sensitivities(
        pv: float,
        forward: float,
        strike: float,
        time_to_expiry: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        calc_risk: Optional[bool] = False,
        tol: Optional[float] = 1e-8,
    ) -> Dict[SimpleMetrics, float]:

        res: Dict[SimpleMetrics, float] = {}

        # 1) compute implied vol
        sigma_imp = EuropeanOptionAnalytics._implied_lognormal_vol_black(
            pv, forward, strike, time_to_expiry, option_type, tol=tol
        )
        res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL] = sigma_imp

        # 2) compute greeks at implied vol
        greeks = EuropeanOptionAnalytics.european_option_log_normal(
            forward, strike, time_to_expiry, sigma_imp, option_type, calc_risk
        )

        # 3) compute sensitivities of implied vol using implicit function theorem
        # G(\sigma_imp(f, k, tte, pv), f, k, tte) = pv, where G is the pricing function
        # For instance, for f risk, we have
        # dG/dsigma * dsigma / df = - dG/df => - dG/df / dG/dsigma
        if calc_risk:
            res.update(
                {
                    SimpleMetrics.D_LN_VOL_D_FORWARD: -greeks[SimpleMetrics.DELTA]
                    / greeks[SimpleMetrics.VEGA],
                    SimpleMetrics.D_LN_VOL_D_TTE: -greeks[SimpleMetrics.TTE_RISK]
                    / greeks[SimpleMetrics.VEGA],
                    SimpleMetrics.D_LN_VOL_D_STRIKE: -greeks[SimpleMetrics.STRIKE_RISK]
                    / greeks[SimpleMetrics.VEGA],
                }
            )

        return res

    @staticmethod
    def implied_normal_vol_sensitivities(
        pv: float,
        forward: float,
        strike: float,
        time_to_expiry: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        calc_risk: Optional[bool] = False,
        tol: Optional[float] = 1e-8,
    ) -> Dict[SimpleMetrics, float]:

        res = {}

        # 1) Compute implied normal vol
        sigma_imp = EuropeanOptionAnalytics._implied_normal_vol_bachelier(
            pv, forward, strike, time_to_expiry, option_type, tol=tol
        )
        res[SimpleMetrics.IMPLIED_NORMAL_VOL] = sigma_imp

        # 2) Compute Greeks at implied vol
        greeks = EuropeanOptionAnalytics.european_option_normal(
            forward, strike, time_to_expiry, sigma_imp, option_type, calc_risk
        )

        # 3) Compute sensitivities of implied vol
        # G(\sigma_imp(f, k, tte), f, k, tte) = pv, where G is the pricing function
        # For instance, for f risk, we have
        # dG/dsigma * dsigma / df = - dG/df => - dG/df / dG/dsigma
        if calc_risk:
            res.update(
                {
                    SimpleMetrics.D_N_VOL_D_FORWARD: -greeks[SimpleMetrics.DELTA]
                    / greeks[SimpleMetrics.VEGA],
                    SimpleMetrics.D_N_VOL_D_TTE: -greeks[SimpleMetrics.TTE_RISK]
                    / greeks[SimpleMetrics.VEGA],
                    SimpleMetrics.D_N_VOL_D_STRIKE: -greeks[SimpleMetrics.STRIKE_RISK]
                    / greeks[SimpleMetrics.VEGA],
                }
            )

        return res

    @staticmethod
    def lognormal_vol_to_normal_vol(
        forward: float,
        strike: float,
        time_to_expiry: float,
        log_normal_sigma: float,
        calc_risk: Optional[bool] = False,
        shift: Optional[float] = 0.0,
        tol: Optional[float] = 1e-8,
    ) -> Dict[SimpleMetrics, float]:

        res: Dict[SimpleMetrics, float] = {}

        option_type = CallOrPut.PUT if forward > strike else CallOrPut.CALL

        # 1) black price (BS'76)
        # V = BS(f, k, tte, log_normal_sigma)
        black_res = EuropeanOptionAnalytics.european_option_log_normal(
            forward + shift,
            strike + shift,
            time_to_expiry,
            log_normal_sigma,
            option_type,
            calc_risk,
        )
        pv = black_res[SimpleMetrics.PV]

        # 2) implied normal vol (Bachelier)
        # nv = Imp(f, k, tte, V)
        # notice dnv/dV = 1 / vega
        bachelier_res = EuropeanOptionAnalytics.implied_normal_vol_sensitivities(
            pv, forward + shift, strike + shift, time_to_expiry, option_type, calc_risk, tol
        )
        res[SimpleMetrics.IMPLIED_NORMAL_VOL] = bachelier_res[SimpleMetrics.IMPLIED_NORMAL_VOL]

        if calc_risk:
            # compute bacherlie vega
            vega_res = EuropeanOptionAnalytics.european_option_normal(
                forward + shift,
                strike + shift,
                time_to_expiry,
                bachelier_res[SimpleMetrics.IMPLIED_NORMAL_VOL],
                option_type,
                calc_risk,
            )
            # vol risk
            res[SimpleMetrics.D_N_VOL_D_LN_VOL] = (
                black_res[SimpleMetrics.VEGA] / vega_res[SimpleMetrics.VEGA]
            )
            # forward risk
            res[SimpleMetrics.D_N_VOL_D_FORWARD] = (
                bachelier_res[SimpleMetrics.D_N_VOL_D_FORWARD]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * black_res[SimpleMetrics.DELTA]
            )
            # strike risk
            res[SimpleMetrics.D_N_VOL_D_STRIKE] = (
                bachelier_res[SimpleMetrics.D_N_VOL_D_STRIKE]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * black_res[SimpleMetrics.STRIKE_RISK]
            )
            # tte risk
            res[SimpleMetrics.D_N_VOL_D_TTE] = (
                bachelier_res[SimpleMetrics.D_N_VOL_D_TTE]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * black_res[SimpleMetrics.TTE_RISK]
            )

        return res

    @staticmethod
    def normal_vol_to_lognormal_vol(
        forward: float,
        strike: float,
        time_to_expiry: float,
        normal_sigma: float,
        calc_risk: Optional[bool] = False,
        shift: Optional[float] = 0.0,
        tol: Optional[float] = 1e-8,
    ) -> Dict[SimpleMetrics, float]:

        res: Dict[SimpleMetrics, float] = {}

        option_type = CallOrPut.PUT if forward > strike else CallOrPut.CALL

        # 1) bachelier
        # V = Bachelier(f, k, tte, normal_sigma)
        bachelier_res = EuropeanOptionAnalytics.european_option_normal(
            forward + shift, strike + shift, time_to_expiry, normal_sigma, option_type, calc_risk
        )
        pv = bachelier_res[SimpleMetrics.PV]

        # 2) implied log normal vol (BS'76)
        # ln_nv = Imp(f, k, tte, V)
        # notice dln_nv/dV = 1 / vega
        black_res = EuropeanOptionAnalytics.implied_lognormal_vol_sensitivities(
            pv, forward + shift, strike + shift, time_to_expiry, option_type, calc_risk, tol
        )
        res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL] = black_res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL]

        # risk
        if calc_risk:
            # compute bs vega
            vega_res = EuropeanOptionAnalytics.european_option_log_normal(
                forward + shift,
                strike + shift,
                time_to_expiry,
                black_res[SimpleMetrics.IMPLIED_LOG_NORMAL_VOL],
                option_type,
                calc_risk,
            )
            # vol risk
            res[SimpleMetrics.D_LN_VOL_D_N_VOL] = (
                bachelier_res[SimpleMetrics.VEGA] / vega_res[SimpleMetrics.VEGA]
            )
            # forward risk
            res[SimpleMetrics.D_LN_VOL_D_FORWARD] = (
                black_res[SimpleMetrics.D_LN_VOL_D_FORWARD]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * bachelier_res[SimpleMetrics.DELTA]
            )
            # strike risk
            res[SimpleMetrics.D_LN_VOL_D_STRIKE] = (
                black_res[SimpleMetrics.D_LN_VOL_D_STRIKE]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * bachelier_res[SimpleMetrics.STRIKE_RISK]
            )
            # tte risk
            res[SimpleMetrics.D_LN_VOL_D_TTE] = (
                black_res[SimpleMetrics.D_LN_VOL_D_TTE]
                + 1.0 / vega_res[SimpleMetrics.VEGA] * bachelier_res[SimpleMetrics.TTE_RISK]
            )

        return res

    ### utilities below

    @staticmethod
    def _implied_lognormal_vol_black(
        pv: float,
        forward: float,
        strike: float,
        time_to_expiry: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        tol: Optional[float] = 1e-8,
        vol_min: Optional[float] = 0.0,
        vol_max: Optional[float] = 10.0,
        max_iter: Optional[int] = 1000,
    ) -> float:

        # arbitrage bounds
        intrinsic = (
            max(0.0, forward - strike)
            if option_type == CallOrPut.CALL
            else max(0.0, strike - forward)
        )
        if pv < intrinsic:
            raise ValueError("Price below intrinsic value")

        # initial guess
        sigma = EuropeanOptionAnalytics._initial_log_normal_implied_vol_guess(
            forward, time_to_expiry, pv
        )

        # bisection + newton
        for _ in range(max_iter):

            res = EuropeanOptionAnalytics.european_option_log_normal(
                forward, strike, time_to_expiry, sigma, option_type, True
            )
            pv_est = res[SimpleMetrics.PV]
            vega = res[SimpleMetrics.VEGA]

            diff = pv_est - pv

            if abs(diff) < tol:
                return sigma
            if pv_est > pv:
                vol_max = sigma
            else:
                vol_min = sigma

            # newton step only if stable
            if vega > 1e-8:
                sigma_new = sigma - diff / vega
                if vol_min < sigma_new < vol_max:
                    sigma = sigma_new
                else:
                    sigma = 0.5 * (vol_min + vol_max)
            else:
                sigma = 0.5 * (vol_min + vol_max)

        raise RuntimeError("Implied volatility did not converge")

    @staticmethod
    def _implied_normal_vol_bachelier(
        pv: float,
        forward: float,
        strike: float,
        time_to_expiry: float,
        option_type: Optional[CallOrPut] = CallOrPut.CALL,
        tol: Optional[float] = 1e-8,
        vol_min: Optional[float] = 1e-8,
        vol_max: Optional[float] = 0.1,
        max_iter: Optional[int] = 100,
    ) -> float:

        # arbitrage bounds
        intrinsic = (
            max(0.0, forward - strike)
            if option_type == CallOrPut.CALL
            else max(0.0, strike - forward)
        )
        if pv < intrinsic:
            raise ValueError("Price below intrinsic value")

        # initial guess
        sigma = EuropeanOptionAnalytics._initial_normal_implied_vol_guess(time_to_expiry, pv)

        # bisection + newton
        for _ in range(max_iter):

            res = EuropeanOptionAnalytics.european_option_normal(
                forward, strike, time_to_expiry, sigma, option_type, True
            )
            pv_est = res[SimpleMetrics.PV]
            vega = res[SimpleMetrics.VEGA]
            diff = pv_est - pv

            if abs(diff) < tol:
                return sigma
            # newton step only if stable
            if vega > 1e-8 and 0 < sigma - diff / vega < vol_max:
                sigma -= diff / vega
            else:
                # bisection fallback
                sigma = 0.5 * (vol_min + vol_max)

            if pv_est > pv:
                vol_max = sigma
            else:
                vol_min = sigma

        raise RuntimeError("Implied normal volatility did not converge")

    @staticmethod
    def _initial_log_normal_implied_vol_guess(forward: float, time_to_expiry: float, pv: float):
        return math.sqrt(2 * math.pi / time_to_expiry) * pv / forward

    @staticmethod
    def _initial_normal_implied_vol_guess(time_to_expiry: float, pv: float):
        return pv * math.sqrt(2 * math.pi / time_to_expiry)
