import QuantLib as ql
import numpy as np
from typing import Optional, List
from fixedincomelib.date import (Date, Period, TermOrTerminationDate)
from fixedincomelib.date.utilities import accrued
from fixedincomelib.market.data_conventions import CompoundingMethod
from fixedincomelib.market.registries import (IndexFixingsManager, IndexRegistry)
from fixedincomelib.valuation import *
from fixedincomelib.valuation.valuation_parameters import ValuationParametersCollection
from fixedincomelib.yield_curve.yield_curve_model import YieldCurve


class ValuationEngineAnalyticsOvernightIndex(ValuationEngineAnalytics):

    def __init__(self, 
                 model: YieldCurve, 
                 valuation_parameters_collection: ValuationParametersCollection,
                 overnight_index : ql.OvernightIndex,
                 effective_date : Date,
                 term_or_termination_date : TermOrTerminationDate,
                 compounding_method : Optional[CompoundingMethod.COMPOUND]) -> None:
    
        super().__init__(model, valuation_parameters_collection)
        self.overnight_index_ = overnight_index
        self.compounding_method_ = compounding_method
        self.effctive_date_ = effective_date
        self.term_or_termination_date_ = term_or_termination_date
        self.initialise()
        # calculation variables
        self.index_value_ = None
        self.historical_portion_ = 1.
        self.floating_portion_ = 1.
        self.dr_dfloat_ = 0.
        self.floating_portion_df_s_risk_ = 0.
        self.floating_portion_df_e_risk_ = 0.

    def initialise(self):
        
        # basic vars
        calendar : ql.Calendar = self.overnight_index_.fixingCalendar()
        day_counter : ql.DayCounter = self.overnight_index_.dayCounter()
        business_day_convention = self.overnight_index_.businessDayConvention()

        # calculate termination date
        self.termination_date_ = None
        if self.term_or_termination_date_.is_term():
            self.termination_date_ = calendar.advance(self.effctive_date_, 
                        self.term_or_termination_date_.get_term(),
                        business_day_convention)
        else:
            self.termination_date_ = self.term_or_termination_date_.get_date()
        self.accrued_ = day_counter.yearFraction(self.effctive_date_, self.termination_date_)

        # is partial fixexd ?
        self.partial_fix_start_, self.partial_fix_end_ = None, None
        self.effective_start_, self.effctive_end_ = self.effctive_date_, self.termination_date_
        # 1) value_date <= effective date : nothing has fixed (default)
        # 2) value_date in (effective date, termination date] : fixed up to value_date
        #    i) value_date is termination date : fully fixed
        #   ii) value_date < termination date : partially fixed
        # 3) value_date > termination_date : fully fixed
        if self.value_date_ > self.effctive_date_ and self.value_date_ <= self.termination_date_:
            self.partial_fix_start_ = self.effctive_date_
            self.partial_fix_end_ = self.value_date_
            next_date = calendar.advance(self.partial_fix_end_, Period('1D'), business_day_convention)
            if next_date > self.termination_date_:
                self.effective_start_, self.effctive_end_ = None, None # everything is fixed
            else:
                self.effective_start_ = self.value_date_
                self.effctive_end_ = self.termination_date_
        elif self.value_date_ > self.termination_date_:
            # fully fixed
            self.partial_fix_start_ = self.effctive_date_
            self.partial_fix_end_ = self.termination_date_
            self.effective_start_, self.effctive_end_ = None, None # everything is fixed

        # get fixings
        index_name = IndexRegistry().look_up_index_name(self.overnight_index_)
        self.daily_fixings_, self.daily_acc_ = [], []
        if self.partial_fix_start_:
            cur_date = self.partial_fix_start_
            while cur_date < self.partial_fix_end_:
                fixing = IndexFixingsManager().get_fixing(index_name, cur_date)
                self.daily_fixings_.append(fixing)
                next_date = calendar.advance(cur_date, Period('1D'), business_day_convention)
                self.daily_acc_.append(day_counter.yearFraction(cur_date, next_date))
                cur_date = next_date


    def calculate_value(self):
        
        # 1 + \tau R = (1 + \tau_h R_h) * (1 + \tau_f R_f)

        # calculate historical portion (1 + \tau_h R_h)
        if len(self.daily_fixings_) != 0:
            if self.compounding_method_ == CompoundingMethod.COMPOUND:
                this_multi = 1.
                for fixing, acc in zip(self.daily_fixings_, self.daily_acc_):
                    this_multi *= (1. + acc * fixing)
                self.historical_portion_ = this_multi
            elif self.compounding_method_ == CompoundingMethod.ARITHMETIC:
                self.historical_portion_ += np.inner(self.daily_fixings_, self.daily_acc_)
        
        # calculate floating part
        # if self.value_date >= termination_date_, then its fully fixed
        if self.value_date_ < self.termination_date_:
            # not fully fixed yet
            df_s = self.model_.discount_factor(self.overnight_index_, self.effective_start_)
            df_e = self.model_.discount_factor(self.overnight_index_, self.effctive_end_)
            self.floating_portion_ = df_s / df_e
            self.floating_portion_df_s_risk_ = 1. / df_e
            self.floating_portion_df_e_risk_ = - self.floating_portion_ / df_e
        
        # calculate R
        self.index_value_ = 1./ self.accrued_ * (self.historical_portion_ * self.floating_portion_ - 1)
        self.dr_dfloat_ = self.historical_portion_ / self.accrued_

    def calculate_risk(self, gradient : List[np.ndarray], scaler : Optional[float]=1., accumulate : Optional[bool]=False) -> None:
        
        local_grad = []
        self.model_.resize_gradient(local_grad)
        
        if self.value_date_ < self.termination_date_:
            self.model_.discount_factor_gradient_wrt_state(
                self.overnight_index_, 
                self.effective_start_, 
                local_grad,  
                scaler * self.dr_dfloat_ * self.floating_portion_df_s_risk_,
                True)
            self.model_.discount_factor_gradient_wrt_state(
                self.overnight_index_, 
                self.effctive_end_, 
                local_grad,
                scaler * self.dr_dfloat_ * self.floating_portion_df_e_risk_,
                True)
    
        self.model_.resize_gradient(gradient)
        if accumulate:
            for i in range(len(gradient)):
                gradient[i] += local_grad[i]
        else:
            gradient[:] = local_grad


    def value(self) -> float:
        return self.index_value_

### Registry
ValuationEngineAnalyticIndexRegistry().register((YieldCurve._model_type.to_string(), ql.OvernightIndex.__name__), ValuationEngineAnalyticsOvernightIndex)


