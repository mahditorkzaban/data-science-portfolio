"""
Professional Valuation Calculator
A production-quality financial modeling engine supporting DCF, multiples,
asset-based, and special valuation models.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import json
import math
from enum import Enum


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ValuationModel(Enum):
    """Supported valuation models"""
    FCFF_DCF = "fcff_dcf"
    FCFE_DCF = "fcfe_dcf"
    DDM_GORDON = "ddm_gordon"
    DDM_MULTISTAGE = "ddm_multistage"
    PE_MULTIPLE = "pe_multiple"
    EV_EBITDA = "ev_ebitda"
    EV_SALES = "ev_sales"
    PB_MULTIPLE = "pb_multiple"
    PEG_MULTIPLE = "peg_multiple"
    BOOK_VALUE = "book_value"
    ADJUSTED_BOOK = "adjusted_book"
    LIQUIDATION = "liquidation"
    REAL_OPTIONS = "real_options"
    SOTP = "sotp"
    LBO = "lbo"


# ============================================================================
# DATA CLASSES FOR INPUTS
# ============================================================================

@dataclass
class FCFFInputs:
    """Inputs for FCFF DCF model"""
    ebit_projections: List[float]  # in millions
    tax_rate: float  # as decimal (e.g., 0.25 for 25%)
    da_projections: List[float]  # Depreciation & Amortization
    capex_projections: List[float]
    nwc_change_projections: List[float]
    wacc: float  # as decimal
    terminal_growth: float  # as decimal
    net_debt: float  # Total Debt - Cash
    minority_interest: float
    investments: float  # Non-operating investments
    diluted_shares: float  # in millions

    def validate(self) -> List[str]:
        warnings = []
        if self.wacc <= self.terminal_growth:
            warnings.append("WACC must be > terminal growth rate")
        if self.tax_rate < 0 or self.tax_rate > 1:
            warnings.append("Tax rate should be between 0 and 1")
        if self.diluted_shares <= 0:
            warnings.append("Diluted shares must be positive")
        if len(self.ebit_projections) != len(self.da_projections):
            warnings.append("All projection lists must have same length")
        return warnings


@dataclass
class FCFEInputs:
    """Inputs for FCFE DCF model"""
    net_income_projections: List[float]
    da_projections: List[float]
    capex_projections: List[float]
    nwc_change_projections: List[float]
    net_borrowing_projections: List[float]
    cost_of_equity: float
    terminal_growth: float
    diluted_shares: float

    def validate(self) -> List[str]:
        warnings = []
        if self.cost_of_equity <= self.terminal_growth:
            warnings.append("Cost of equity must be > terminal growth rate")
        if self.diluted_shares <= 0:
            warnings.append("Diluted shares must be positive")
        return warnings


@dataclass
class DDMInputs:
    """Inputs for Dividend Discount Model"""
    dividends: List[float]  # Dividend projections
    cost_of_equity: float
    terminal_growth: float  # For perpetuity
    diluted_shares: float
    is_multistage: bool = True

    def validate(self) -> List[str]:
        warnings = []
        if self.cost_of_equity <= self.terminal_growth:
            warnings.append("Cost of equity must be > terminal growth rate")
        if any(d < 0 for d in self.dividends):
            warnings.append("Dividends should be non-negative")
        return warnings


@dataclass
class MultiplesInputs:
    """Inputs for relative valuation multiples"""
    # Company metrics
    market_cap: Optional[float] = None
    price: Optional[float] = None
    eps: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    revenue: Optional[float] = None
    book_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash: Optional[float] = None
    earnings_growth: Optional[float] = None  # For PEG
    diluted_shares: Optional[float] = None

    # Comparable multiples
    comparable_pe: Optional[float] = None
    comparable_ev_ebitda: Optional[float] = None
    comparable_ev_sales: Optional[float] = None
    comparable_pb: Optional[float] = None

    def validate(self) -> List[str]:
        warnings = []
        if self.market_cap and self.market_cap < 0:
            warnings.append("Market cap cannot be negative")
        if self.diluted_shares and self.diluted_shares <= 0:
            warnings.append("Shares must be positive")
        return warnings


@dataclass
class AssetBasedInputs:
    """Inputs for asset-based valuation"""
    total_assets: float
    total_liabilities: float
    # For adjusted book value
    asset_fair_values: Optional[Dict[str, float]] = None
    liability_fair_values: Optional[Dict[str, float]] = None
    # For liquidation
    asset_haircuts: Optional[Dict[str, float]] = None  # Recovery rates
    liquidation_costs: Optional[float] = None

    def validate(self) -> List[str]:
        warnings = []
        if self.total_assets < 0 or self.total_liabilities < 0:
            warnings.append("Assets and liabilities should be non-negative")
        return warnings


@dataclass
class RealOptionsInputs:
    """Inputs for Black-Scholes real options model"""
    underlying_value: float  # S0 (e.g., PV of project)
    strike_price: float  # X (e.g., investment required)
    time_to_expiration: float  # T in years
    risk_free_rate: float  # r as decimal
    volatility: float  # σ as decimal

    def validate(self) -> List[str]:
        warnings = []
        if self.underlying_value <= 0 or self.strike_price <= 0:
            warnings.append("Underlying and strike must be positive")
        if self.time_to_expiration <= 0:
            warnings.append("Time to expiration must be positive")
        if self.volatility < 0:
            warnings.append("Volatility cannot be negative")
        return warnings


@dataclass
class SOTPInputs:
    """Inputs for Sum of the Parts valuation"""
    segment_values: Dict[str, float]  # {segment_name: value}
    net_debt: float
    holding_discount: float = 0.0  # as decimal

    def validate(self) -> List[str]:
        warnings = []
        if not self.segment_values:
            warnings.append("Must have at least one segment")
        if self.holding_discount < 0 or self.holding_discount > 1:
            warnings.append("Holding discount should be between 0 and 1")
        return warnings


@dataclass
class LBOInputs:
    """Inputs for LBO IRR analysis"""
    purchase_ev: float
    initial_debt: float
    initial_equity: float
    exit_ev: float
    exit_debt: float
    holding_period: float  # years

    def validate(self) -> List[str]:
        warnings = []
        if self.holding_period <= 0:
            warnings.append("Holding period must be positive")
        if self.initial_equity <= 0:
            warnings.append("Initial equity must be positive")
        return warnings


# ============================================================================
# DATA CLASSES FOR OUTPUTS
# ============================================================================

@dataclass
class DCFOutput:
    """Output from DCF models"""
    pv_cash_flows: List[float]
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    equity_value: float
    price_per_share: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class MultipleOutput:
    """Output from multiples valuation"""
    current_multiple: Optional[float]
    implied_value: Optional[float]
    implied_price: Optional[float]
    warnings: List[str] = field(default_factory=list)


@dataclass
class AssetBasedOutput:
    """Output from asset-based valuation"""
    equity_value: float
    price_per_share: Optional[float] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class OptionsOutput:
    """Output from real options valuation"""
    option_value: float
    d1: float
    d2: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class SOTPOutput:
    """Output from SOTP valuation"""
    total_enterprise_value: float
    equity_value: float
    segment_breakdown: Dict[str, float]
    warnings: List[str] = field(default_factory=list)


@dataclass
class LBOOutput:
    """Output from LBO analysis"""
    exit_equity: float
    irr: float
    money_multiple: float
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# VALUATION MODELS
# ============================================================================

class DCFModels:
    """DCF valuation models"""

    @staticmethod
    def fcff_dcf(inputs: FCFFInputs) -> DCFOutput:
        """
        FCFF DCF Model
        Formula: FCFF_t = EBIT_t*(1-T) + D&A_t - Capex_t - ΔNWC_t
                 EV = Σ FCFF_t/(1+WACC)^t + TV/(1+WACC)^N
        """
        warnings = inputs.validate()
        n = len(inputs.ebit_projections)

        # Calculate FCFF for each period
        fcff = []
        for i in range(n):
            fcff_t = (inputs.ebit_projections[i] * (1 - inputs.tax_rate) +
                      inputs.da_projections[i] -
                      inputs.capex_projections[i] -
                      inputs.nwc_change_projections[i])
            fcff.append(fcff_t)

        # Present value of FCFF
        pv_fcff = [fcff[i] / (1 + inputs.wacc) ** (i + 1) for i in range(n)]

        # Terminal value
        fcff_terminal = fcff[-1] * (1 + inputs.terminal_growth)
        tv = fcff_terminal / (inputs.wacc - inputs.terminal_growth)
        pv_tv = tv / (1 + inputs.wacc) ** n

        # Enterprise and equity value
        ev = sum(pv_fcff) + pv_tv
        equity = ev - inputs.net_debt - inputs.minority_interest + inputs.investments
        price = equity / inputs.diluted_shares

        return DCFOutput(
            pv_cash_flows=pv_fcff,
            terminal_value=tv,
            pv_terminal_value=pv_tv,
            enterprise_value=ev,
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )

    @staticmethod
    def fcfe_dcf(inputs: FCFEInputs) -> DCFOutput:
        """
        FCFE DCF Model
        Formula: FCFE_t = NI_t + D&A_t - Capex_t - ΔNWC_t + NetBorrowing_t
                 Equity = Σ FCFE_t/(1+Re)^t + TV/(1+Re)^N
        """
        warnings = inputs.validate()
        n = len(inputs.net_income_projections)

        # Calculate FCFE for each period
        fcfe = []
        for i in range(n):
            fcfe_t = (inputs.net_income_projections[i] +
                      inputs.da_projections[i] -
                      inputs.capex_projections[i] -
                      inputs.nwc_change_projections[i] +
                      inputs.net_borrowing_projections[i])
            fcfe.append(fcfe_t)

        # Present value of FCFE
        pv_fcfe = [fcfe[i] / (1 + inputs.cost_of_equity) ** (i + 1)
                   for i in range(n)]

        # Terminal value
        fcfe_terminal = fcfe[-1] * (1 + inputs.terminal_growth)
        tv = fcfe_terminal / (inputs.cost_of_equity - inputs.terminal_growth)
        pv_tv = tv / (1 + inputs.cost_of_equity) ** n

        # Equity value (FCFE goes directly to equity)
        equity = sum(pv_fcfe) + pv_tv
        price = equity / inputs.diluted_shares

        return DCFOutput(
            pv_cash_flows=pv_fcfe,
            terminal_value=tv,
            pv_terminal_value=pv_tv,
            enterprise_value=equity,  # Not meaningful for FCFE
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )

    @staticmethod
    def ddm(inputs: DDMInputs) -> DCFOutput:
        """
        Dividend Discount Model
        Gordon Growth: P0 = D1/(Re - g)
        Multi-stage: P0 = Σ Dt/(1+Re)^t + [D_{N+1}/(Re-g)]/(1+Re)^N
        """
        warnings = inputs.validate()
        n = len(inputs.dividends)

        if inputs.is_multistage and n > 1:
            # Multi-stage DDM
            pv_divs = [inputs.dividends[i] / (1 + inputs.cost_of_equity) ** (i + 1)
                       for i in range(n)]

            # Terminal value
            div_terminal = inputs.dividends[-1] * (1 + inputs.terminal_growth)
            tv = div_terminal / (inputs.cost_of_equity - inputs.terminal_growth)
            pv_tv = tv / (1 + inputs.cost_of_equity) ** n

            equity = sum(pv_divs) + pv_tv
        else:
            # Gordon Growth Model (single stage)
            d1 = inputs.dividends[0] if inputs.dividends else 0
            equity = d1 / (inputs.cost_of_equity - inputs.terminal_growth)
            pv_divs = [equity]
            tv = 0
            pv_tv = 0

        price = equity / inputs.diluted_shares

        return DCFOutput(
            pv_cash_flows=pv_divs,
            terminal_value=tv if inputs.is_multistage else 0,
            pv_terminal_value=pv_tv if inputs.is_multistage else 0,
            enterprise_value=equity,
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )


class MultiplesModels:
    """Relative valuation using multiples"""

    @staticmethod
    def pe_multiple(inputs: MultiplesInputs) -> MultipleOutput:
        """P/E Multiple: P/E = Price/EPS or MarketCap/NetIncome"""
        warnings = inputs.validate()

        current_pe = None
        implied_value = None
        implied_price = None

        # Calculate current P/E
        if inputs.price and inputs.eps and inputs.eps != 0:
            current_pe = inputs.price / inputs.eps
        elif inputs.market_cap and inputs.net_income and inputs.net_income != 0:
            current_pe = inputs.market_cap / inputs.net_income

        # Calculate implied value from comparable
        if inputs.comparable_pe and inputs.net_income:
            implied_value = inputs.comparable_pe * inputs.net_income
            if inputs.diluted_shares:
                implied_price = implied_value / inputs.diluted_shares

        if current_pe is None and implied_value is None:
            warnings.append("Insufficient data for P/E calculation")

        return MultipleOutput(
            current_multiple=current_pe,
            implied_value=implied_value,
            implied_price=implied_price,
            warnings=warnings
        )

    @staticmethod
    def ev_ebitda(inputs: MultiplesInputs) -> MultipleOutput:
        """EV/EBITDA Multiple"""
        warnings = inputs.validate()

        current_multiple = None
        implied_value = None
        implied_price = None

        # Calculate current EV
        if inputs.market_cap is not None and inputs.total_debt is not None:
            cash = inputs.cash if inputs.cash else 0
            ev = inputs.market_cap + inputs.total_debt - cash

            if inputs.ebitda and inputs.ebitda != 0:
                current_multiple = ev / inputs.ebitda

        # Calculate implied EV from comparable
        if inputs.comparable_ev_ebitda and inputs.ebitda:
            implied_ev = inputs.comparable_ev_ebitda * inputs.ebitda
            # Convert EV to equity value
            if inputs.total_debt is not None:
                cash = inputs.cash if inputs.cash else 0
                implied_value = implied_ev - inputs.total_debt + cash
                if inputs.diluted_shares:
                    implied_price = implied_value / inputs.diluted_shares

        return MultipleOutput(
            current_multiple=current_multiple,
            implied_value=implied_value,
            implied_price=implied_price,
            warnings=warnings
        )

    @staticmethod
    def ev_sales(inputs: MultiplesInputs) -> MultipleOutput:
        """EV/Sales Multiple"""
        warnings = inputs.validate()

        current_multiple = None
        implied_value = None
        implied_price = None

        # Calculate current EV/Sales
        if inputs.market_cap is not None and inputs.total_debt is not None:
            cash = inputs.cash if inputs.cash else 0
            ev = inputs.market_cap + inputs.total_debt - cash

            if inputs.revenue and inputs.revenue != 0:
                current_multiple = ev / inputs.revenue

        # Calculate implied EV from comparable
        if inputs.comparable_ev_sales and inputs.revenue:
            implied_ev = inputs.comparable_ev_sales * inputs.revenue
            if inputs.total_debt is not None:
                cash = inputs.cash if inputs.cash else 0
                implied_value = implied_ev - inputs.total_debt + cash
                if inputs.diluted_shares:
                    implied_price = implied_value / inputs.diluted_shares

        return MultipleOutput(
            current_multiple=current_multiple,
            implied_value=implied_value,
            implied_price=implied_price,
            warnings=warnings
        )

    @staticmethod
    def pb_multiple(inputs: MultiplesInputs) -> MultipleOutput:
        """P/B Multiple: Price-to-Book"""
        warnings = inputs.validate()

        current_multiple = None
        implied_value = None
        implied_price = None

        # Calculate current P/B
        if inputs.market_cap and inputs.book_equity and inputs.book_equity != 0:
            current_multiple = inputs.market_cap / inputs.book_equity

        # Calculate implied value from comparable
        if inputs.comparable_pb and inputs.book_equity:
            implied_value = inputs.comparable_pb * inputs.book_equity
            if inputs.diluted_shares:
                implied_price = implied_value / inputs.diluted_shares

        return MultipleOutput(
            current_multiple=current_multiple,
            implied_value=implied_value,
            implied_price=implied_price,
            warnings=warnings
        )

    @staticmethod
    def peg_ratio(inputs: MultiplesInputs) -> MultipleOutput:
        """PEG Ratio: (P/E) / EarningsGrowth"""
        warnings = inputs.validate()

        current_multiple = None

        # Calculate P/E first
        pe = None
        if inputs.price and inputs.eps and inputs.eps != 0:
            pe = inputs.price / inputs.eps
        elif inputs.market_cap and inputs.net_income and inputs.net_income != 0:
            pe = inputs.market_cap / inputs.net_income

        # Calculate PEG
        if pe and inputs.earnings_growth and inputs.earnings_growth != 0:
            # Convert growth to percentage if in decimal
            growth = inputs.earnings_growth * 100 if inputs.earnings_growth < 1 else inputs.earnings_growth
            current_multiple = pe / growth
        else:
            warnings.append("Need P/E and earnings growth rate for PEG")

        return MultipleOutput(
            current_multiple=current_multiple,
            implied_value=None,  # PEG is typically not used for valuation
            implied_price=None,
            warnings=warnings
        )


class AssetBasedModels:
    """Asset-based valuation models"""

    @staticmethod
    def book_value(inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Book Value: Total Assets - Total Liabilities"""
        warnings = inputs.validate()

        equity = inputs.total_assets - inputs.total_liabilities
        price = equity / shares if shares and shares > 0 else None

        return AssetBasedOutput(
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )

    @staticmethod
    def adjusted_book_value(inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Adjusted Book Value: Fair Value Assets - Fair Value Liabilities"""
        warnings = inputs.validate()

        if not inputs.asset_fair_values or not inputs.liability_fair_values:
            warnings.append("Using book values; fair values not provided")
            return AssetBasedModels.book_value(inputs, shares)

        fv_assets = sum(inputs.asset_fair_values.values())
        fv_liabilities = sum(inputs.liability_fair_values.values())
        equity = fv_assets - fv_liabilities
        price = equity / shares if shares and shares > 0 else None

        return AssetBasedOutput(
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )

    @staticmethod
    def liquidation_value(inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Liquidation Value: Σ(Asset * Haircut) - LiquidationCosts - Liabilities"""
        warnings = inputs.validate()

        if not inputs.asset_haircuts:
            warnings.append("No haircuts provided; cannot calculate liquidation value")
            return AssetBasedOutput(equity_value=0, warnings=warnings)

        recoverable_assets = sum(inputs.asset_haircuts.values())
        liquidation_costs = inputs.liquidation_costs if inputs.liquidation_costs else 0

        equity = recoverable_assets - liquidation_costs - inputs.total_liabilities
        price = equity / shares if shares and shares > 0 else None

        if equity < 0:
            warnings.append("Liquidation value is negative; liabilities exceed recoverable assets")

        return AssetBasedOutput(
            equity_value=equity,
            price_per_share=price,
            warnings=warnings
        )


class SpecialModels:
    """Special valuation models"""

    @staticmethod
    def black_scholes_call(inputs: RealOptionsInputs) -> OptionsOutput:
        """
        Black-Scholes Call Option (Real Options)
        C = S0*N(d1) - X*exp(-rT)*N(d2)
        d1 = [ln(S0/X) + (r + 0.5σ²)T] / [σ√T]
        d2 = d1 - σ√T
        """
        warnings = inputs.validate()

        S = inputs.underlying_value
        X = inputs.strike_price
        T = inputs.time_to_expiration
        r = inputs.risk_free_rate
        sigma = inputs.volatility

        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Standard normal CDF
        N_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
        N_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))

        # Call option value
        call_value = S * N_d1 - X * math.exp(-r * T) * N_d2

        return OptionsOutput(
            option_value=call_value,
            d1=d1,
            d2=d2,
            warnings=warnings
        )

    @staticmethod
    def sotp(inputs: SOTPInputs) -> SOTPOutput:
        """Sum of the Parts: Σ SegmentValue - NetDebt - HoldingDiscount"""
        warnings = inputs.validate()

        total_ev = sum(inputs.segment_values.values())
        discount_amount = total_ev * inputs.holding_discount
        equity = total_ev - inputs.net_debt - discount_amount

        return SOTPOutput(
            total_enterprise_value=total_ev,
            equity_value=equity,
            segment_breakdown=inputs.segment_values.copy(),
            warnings=warnings
        )

    @staticmethod
    def lbo_irr(inputs: LBOInputs) -> LBOOutput:
        """LBO IRR: (ExitEquity/InitialEquity)^(1/n) - 1"""
        warnings = inputs.validate()

        exit_equity = inputs.exit_ev - inputs.exit_debt

        if inputs.initial_equity <= 0:
            warnings.append("Initial equity must be positive for IRR calculation")
            return LBOOutput(exit_equity=exit_equity, irr=0, money_multiple=0, warnings=warnings)

        money_multiple = exit_equity / inputs.initial_equity

        if money_multiple <= 0:
            warnings.append("Exit equity is non-positive; IRR undefined")
            irr = float('-inf')
        else:
            irr = money_multiple ** (1 / inputs.holding_period) - 1

        return LBOOutput(
            exit_equity=exit_equity,
            irr=irr,
            money_multiple=money_multiple,
            warnings=warnings
        )


# ============================================================================
# VALUATION CALCULATOR ENGINE
# ============================================================================

class ValuationCalculator:
    """Main valuation calculator orchestrator"""

    def __init__(self):
        self.dcf = DCFModels()
        self.multiples = MultiplesModels()
        self.assets = AssetBasedModels()
        self.special = SpecialModels()

    def run_fcff_dcf(self, inputs: FCFFInputs) -> DCFOutput:
        """Run FCFF DCF model"""
        return self.dcf.fcff_dcf(inputs)

    def run_fcfe_dcf(self, inputs: FCFEInputs) -> DCFOutput:
        """Run FCFE DCF model"""
        return self.dcf.fcfe_dcf(inputs)

    def run_ddm(self, inputs: DDMInputs) -> DCFOutput:
        """Run Dividend Discount Model"""
        return self.dcf.ddm(inputs)

    def run_pe_multiple(self, inputs: MultiplesInputs) -> MultipleOutput:
        """Run P/E multiple valuation"""
        return self.multiples.pe_multiple(inputs)

    def run_ev_ebitda(self, inputs: MultiplesInputs) -> MultipleOutput:
        """Run EV/EBITDA multiple valuation"""
        return self.multiples.ev_ebitda(inputs)

    def run_ev_sales(self, inputs: MultiplesInputs) -> MultipleOutput:
        """Run EV/Sales multiple valuation"""
        return self.multiples.ev_sales(inputs)

    def run_pb_multiple(self, inputs: MultiplesInputs) -> MultipleOutput:
        """Run P/B multiple valuation"""
        return self.multiples.pb_multiple(inputs)

    def run_peg(self, inputs: MultiplesInputs) -> MultipleOutput:
        """Run PEG ratio calculation"""
        return self.multiples.peg_ratio(inputs)

    def run_book_value(self, inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Run book value calculation"""
        return self.assets.book_value(inputs, shares)

    def run_adjusted_book(self, inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Run adjusted book value calculation"""
        return self.assets.adjusted_book_value(inputs, shares)

    def run_liquidation(self, inputs: AssetBasedInputs, shares: Optional[float] = None) -> AssetBasedOutput:
        """Run liquidation value calculation"""
        return self.assets.liquidation_value(inputs, shares)

    def run_real_options(self, inputs: RealOptionsInputs) -> OptionsOutput:
        """Run Black-Scholes real options model"""
        return self.special.black_scholes_call(inputs)

    def run_sotp(self, inputs: SOTPInputs) -> SOTPOutput:
        """Run Sum of the Parts valuation"""
        return self.special.sotp(inputs)

    def run_lbo(self, inputs: LBOInputs) -> LBOOutput:
        """Run LBO IRR analysis"""
        return self.special.lbo_irr(inputs)


# ============================================================================
# REPORTING
# ============================================================================

class ValuationReporter:
    """Formats valuation outputs for the console."""

    @staticmethod
    def _header(title: str) -> None:
        print(f"\n{'=' * 70}\n{title.upper()}\n{'=' * 70}")

    @staticmethod
    def print_dcf_output(output: DCFOutput, model_name: str) -> None:
        ValuationReporter._header(f"{model_name} valuation")
        for t, pv in enumerate(output.pv_cash_flows, start=1):
            print(f"  PV of cash flow, year {t:<2}: {pv:>14,.2f}")
        print(f"  Terminal value            : {output.terminal_value:>14,.2f}")
        print(f"  PV of terminal value      : {output.pv_terminal_value:>14,.2f}")
        print(f"  Enterprise value          : {output.enterprise_value:>14,.2f}")
        print(f"  Equity value              : {output.equity_value:>14,.2f}")
        print(f"  Value per share           : {output.price_per_share:>14,.2f}")
        ValuationReporter._warnings(output.warnings)

    @staticmethod
    def print_lbo_output(output: LBOOutput) -> None:
        ValuationReporter._header("LBO returns")
        print(f"  Exit equity    : {output.exit_equity:>12,.2f}")
        print(f"  Money multiple : {output.money_multiple:>11.2f}x")
        print(f"  IRR            : {output.irr:>11.1%}")
        ValuationReporter._warnings(output.warnings)

    @staticmethod
    def _warnings(warnings: List[str]) -> None:
        for w in warnings:
            print(f"  ! {w}")


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    calc = ValuationCalculator()

    fcff = FCFFInputs(
        ebit_projections=[120, 135, 150, 165, 180],
        tax_rate=0.25,
        da_projections=[30, 32, 34, 36, 38],
        capex_projections=[40, 42, 44, 46, 48],
        nwc_change_projections=[5, 5, 6, 6, 7],
        wacc=0.09,
        terminal_growth=0.025,
        net_debt=250,
        minority_interest=0,
        investments=20,
        diluted_shares=100,
    )
    ValuationReporter.print_dcf_output(calc.run_fcff_dcf(fcff), "FCFF DCF")

    lbo = LBOInputs(purchase_ev=1000, initial_debt=600, initial_equity=400,
                    exit_ev=1500, exit_debt=350, holding_period=5)
    ValuationReporter.print_lbo_output(calc.run_lbo(lbo))

    option = calc.run_real_options(RealOptionsInputs(
        underlying_value=120, strike_price=100, time_to_expiration=2,
        risk_free_rate=0.03, volatility=0.30))
    ValuationReporter._header("Real option (Black-Scholes)")
    print(f"  Option value: {option.option_value:,.2f}  (d1={option.d1:.3f}, d2={option.d2:.3f})")
