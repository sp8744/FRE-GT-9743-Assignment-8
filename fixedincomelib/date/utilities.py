import pandas as pd
from typing import Optional
import QuantLib as ql
from QuantLib import Period
from fixedincomelib.date.basics import Date, Period
from fixedincomelib.market import HolidayConvention, BusinessDayConvention, AccrualBasis


def add_period(
    start_date: Date,
    term: Period,
    business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
    holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
    end_of_month: Optional[bool] = False,
):

    this_cal = holiday_convention.value
    return Date(this_cal.advance(start_date, term, business_day_convention.value, end_of_month))


def move_to_business_day(
    input_date: Date,
    business_day_convention: BusinessDayConvention,
    holiday_convention: HolidayConvention,
):
    return Date(holiday_convention.value.adjust(input_date, business_day_convention.value))


def accrued(
    start_date: Date,
    end_date: Date,
    accrual_basis: Optional[AccrualBasis] = AccrualBasis("ACT/ACT"),
    business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
    holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
):

    adjusted_end_dt = move_to_business_day(end_date, business_day_convention, holiday_convention)
    return accrual_basis.value.yearFraction(start_date, adjusted_end_dt)


def is_business_day(input_date: Date, holiday_convention: HolidayConvention):
    return holiday_convention.value.isBusinessDay(input_date)


def is_holiday(input_date: Date, holiday_convention: HolidayConvention):
    return holiday_convention.value.isHoliday(input_date)


def is_end_of_month(input_date: Date, holiday_convention: HolidayConvention):
    return holiday_convention.value.isEndOfMonth(input_date)


def end_of_month(input_date: Date, holiday_convention: HolidayConvention):
    return holiday_convention.value.endOfMonth(input_date)


def make_schedule(
    start_date: Date,
    end_date: Date,
    accrual_period: Period,
    holiday_convention: HolidayConvention,
    business_day_convention: BusinessDayConvention,
    accrual_basis: AccrualBasis,
    rule: Optional[str] = "BACKWARD",
    end_of_month: Optional[bool] = False,
    fix_in_arrear: Optional[bool] = False,
    fixing_offset: Optional[Period] = Period("0D"),
    payment_offset: Optional[Period] = Period("0D"),
    payment_business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
    payment_holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
) -> pd.DataFrame:

    this_rule = (
        ql.DateGeneration.Backward if rule.upper() == "BACKWARD" else ql.DateGeneration.Forward
    )
    # set up start date and end date of each period
    this_schedule = ql.Schedule(
        start_date,
        end_date,
        accrual_period,
        holiday_convention.value,
        business_day_convention.value,
        business_day_convention.value,
        this_rule,
        end_of_month,
    )

    # add fixing date and payment date
    start_dates = this_schedule.dates()[:-1]
    end_dates = this_schedule.dates()[1:]
    fixing_dates, payment_dates, accs = [], [], []
    for s, e in zip(start_dates, end_dates):
        f = s
        if fixing_offset != "":
            f = add_period(
                e if fix_in_arrear else s,
                fixing_offset,
                business_day_convention,
                holiday_convention,
            )
        fixing_dates.append(f)
        p = e
        if payment_offset != "":
            p = add_period(
                e, payment_offset, payment_business_day_convention, payment_holiday_convention
            )
        payment_dates.append(p)
        accs.append(accrued(s, e, accrual_basis, business_day_convention, holiday_convention))

    # set up container
    df = pd.DataFrame(columns=["StartDate", "EndDate", "FixingDate", "PaymentDate", "Accrued"])
    df["StartDate"] = start_dates
    df["EndDate"] = end_dates
    df["FixingDate"] = fixing_dates
    df["PaymentDate"] = payment_dates
    df["Accrued"] = accs

    return df


def frequency_from_period(p: str) -> float:
    freq = p.frequency()
    return float(freq)


### NOT SURE WE NEED BELOW FUNCTIONS YET

# def apply_off_set(value_date, offset: str, holiday_convention: str, business_day_convention: str = "F"):
#     s = str(offset).strip().upper()
#     cal = HolidayConvention(holiday_convention).value
#     if s.endswith("B"):
#         n = int(s[:-1]) if s[:-1] else 0
#         return Date(cal.advance(Date(value_date), n, ql.Days))
#     return addPeriod(value_date, s, business_day_convention, holiday_convention)

# def business_day_schedule(
#     start_date: Date,
#     end_date:   Date,
#     calendar) -> list[Date]:

#     ql_sched = ql.Schedule(
#         start_date,
#         end_date,
#         ql.Period(1, ql.Days),
#         calendar,
#         ql.Following, ql.Following,
#         ql.DateGeneration.Forward,
#         False
#     )

#     return [ Date(d) for d in ql_sched ]
