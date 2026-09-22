Attribute VB_Name = "greeks"
'by Peter McPhee - www.OptionTradingTips.com
'27/04/06 - Fixed a bug that failed to calculate the theoretical change in P&L for stocks in the strategies tab.
'28/08/06 - Fixed a small calculation bug for the Option Theta, which now has a near perfect accuracy.
'1/10/06 - Added support for Dividend Yield, which can be used as a workaround to price options on futures
' by making the Dividend Yield the same as the Interest Rate.
'1/05/14 - Excel 2013 introduced their own Gamma function, which conflicted with my own Gamma function, so I changed
' Gamma to OptionGamma

Function dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
dOne = (Log(UnderlyingPrice / ExercisePrice) + (Interest - Dividend + 0.5 * Volatility ^ 2) * Time) / (Volatility * (Sqr(Time)))
End Function
Function NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
NdOne = Exp(-(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) ^ 2) / 2) / (Sqr(2 * 3.14159265358979))
End Function
Function dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
dTwo = dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) - Volatility * Sqr(Time)
End Function
Function NdTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
NdTwo = Application.NormSDist(dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
End Function
Function CallOption(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
CallOption = Exp(-Dividend * Time) * UnderlyingPrice * Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - ExercisePrice * Exp(-Interest * Time) * Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) - Volatility * Sqr(Time))
End Function
Function PutOption(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
PutOption = ExercisePrice * Exp(-Interest * Time) * Application.NormSDist(-dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - Exp(-Dividend * Time) * UnderlyingPrice * Application.NormSDist(-dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
End Function
Function CallDelta(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
CallDelta = Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
'CallDelta = Application.NormSDist((Log(UnderlyingPrice / ExercisePrice) + (Interest - Dividend) * Time) / (Volatility * Sqr(Time)) + 0.5 * Volatility * Sqr(Time))
End Function
Function PutDelta(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
PutDelta = Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - 1
'PutDelta = Application.NormSDist((Log(UnderlyingPrice / ExercisePrice) + (Interest - Dividend) * Time) / (Volatility * Sqr(Time)) + 0.5 * Volatility * Sqr(Time)) - 1
End Function
Function CallTheta(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
CT = -(UnderlyingPrice * Volatility * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) / (2 * Sqr(Time)) - Interest * ExercisePrice * Exp(-Interest * (Time)) * NdTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
CallTheta = CT / 252
End Function
Function OptionGamma(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
OptionGamma = NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) / (UnderlyingPrice * (Volatility * Sqr(Time)))
End Function
Function Vega(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
Vega = 0.01 * UnderlyingPrice * Sqr(Time) * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
End Function
Function PutTheta(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
PT = -(UnderlyingPrice * Volatility * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) / (2 * Sqr(Time)) + Interest * ExercisePrice * Exp(-Interest * (Time)) * (1 - NdTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
PutTheta = PT / 252
End Function
Function CallRho(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
CallRho = 0.01 * ExercisePrice * Time * Exp(-Interest * Time) * Application.NormSDist(dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
End Function
Function PutRho(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
PutRho = -0.01 * ExercisePrice * Time * Exp(-Interest * Time) * (1 - Application.NormSDist(dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)))
End Function
Function ImpliedCallVolatility(UnderlyingPrice, ExercisePrice, Time, Interest, Target, Dividend)
High = 5
Low = 0
Do While (High - Low) > 0.0001
If CallOption(UnderlyingPrice, ExercisePrice, Time, Interest, (High + Low) / 2, Dividend) > Target Then
High = (High + Low) / 2
Else: Low = (High + Low) / 2
End If
Loop
ImpliedCallVolatility = (High + Low) / 2
End Function
Function ImpliedPutVolatility(UnderlyingPrice, ExercisePrice, Time, Interest, Target, Dividend)
High = 5
Low = 0
Do While (High - Low) > 0.0001
If PutOption(UnderlyingPrice, ExercisePrice, Time, Interest, (High + Low) / 2, Dividend) > Target Then
High = (High + Low) / 2
Else: Low = (High + Low) / 2
End If
Loop
ImpliedPutVolatility = (High + Low) / 2
End Function

Function OTW_BlackScholes(callputstock, Output, UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)


' Stock Calculations
Select Case LCase(Left(callputstock, 1))
Case Is = "s"
' Stock Output
Select Case LCase(Left(Output, 1))
Case Is = "x"
OTW_BlackScholes = "Stock Payoff"
Case Is = "p"
OTW_BlackScholes = UnderlyingPrice
Case Is = "d"
OTW_BlackScholes = 1
Case Is = "g"
OTW_BlackScholes = 0
Case Is = "t"
OTW_BlackScholes = 0
Case Is = "v"
OTW_BlackScholes = 0
Case Is = "r"
OTW_BlackScholes = 0
End Select
'End Stock Output
End Select
'End Stock Calculations

' Call Option Calculations
Select Case LCase(Left(callputstock, 1))
Case Is = "c"
' Call Option Output
Select Case LCase(Left(Output, 1))
Case Is = "x"
OTW_BlackScholes = "Call Option Payoff"
Case Is = "p"
OTW_BlackScholes = Exp(-Dividend * Time) * UnderlyingPrice * Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - ExercisePrice * Exp(-Interest * Time) * Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) - Volatility * Sqr(Time))
Case Is = "d"
OTW_BlackScholes = Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
Case Is = "g"
OTW_BlackScholes = NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) / (UnderlyingPrice * (Volatility * Sqr(Time)))
Case Is = "t"
CT = -(UnderlyingPrice * Volatility * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) / (2 * Sqr(Time)) - Interest * ExercisePrice * Exp(-Interest * (Time)) * NdTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
OTW_BlackScholes = CT / 252
Case Is = "v"
OTW_BlackScholes = 0.01 * UnderlyingPrice * Sqr(Time) * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
Case Is = "r"
OTW_BlackScholes = 0.01 * ExercisePrice * Time * Exp(-Interest * Time) * Application.NormSDist(dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
End Select
'End Call Output
End Select
'End Call Option Calculations

' Put Option Calculations
Select Case LCase(Left(callputstock, 1))
Case Is = "p"
' Put Option Output
Select Case LCase(Left(Output, 1))
Case Is = "x"
OTW_BlackScholes = "Put Option Payoff"
Case Is = "p"
OTW_BlackScholes = ExercisePrice * Exp(-Interest * Time) * Application.NormSDist(-dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - Exp(-Dividend * Time) * UnderlyingPrice * Application.NormSDist(-dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
Case Is = "d"
OTW_BlackScholes = Application.NormSDist(dOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) - 1
Case Is = "g"
OTW_BlackScholes = NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend) / (UnderlyingPrice * (Volatility * Sqr(Time)))
Case Is = "t"
PT = -(UnderlyingPrice * Volatility * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)) / (2 * Sqr(Time)) + Interest * ExercisePrice * Exp(-Interest * (Time)) * (1 - NdTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend))
OTW_BlackScholes = PT / 252
Case Is = "v"
OTW_BlackScholes = 0.01 * UnderlyingPrice * Sqr(Time) * NdOne(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)
Case Is = "r"
OTW_BlackScholes = -0.01 * ExercisePrice * Time * Exp(-Interest * Time) * (1 - Application.NormSDist(dTwo(UnderlyingPrice, ExercisePrice, Time, Interest, Volatility, Dividend)))
End Select
'End Put Output
End Select
'End Put Option Calculations

End Function

Function OTW_IV(CallPut, UnderlyingPrice, ExercisePrice, Time, Interest, Target, Dividend)

Select Case LCase(Left(CallPut, 1))
Case Is = "c"
High = 5
Low = 0
Do While (High - Low) > 0.0001
If OTW_BlackScholes("c", "p", UnderlyingPrice, ExercisePrice, Time, Interest, (High + Low) / 2, Dividend) > Target Then
High = (High + Low) / 2
Else: Low = (High + Low) / 2
End If
Loop
OTW_IV = (High + Low) / 2

Case Is = "p"
High = 5
Low = 0
Do While (High - Low) > 0.0001
If OTW_BlackScholes("p", "p", UnderlyingPrice, ExercisePrice, Time, Interest, (High + Low) / 2, Dividend) > Target Then
High = (High + Low) / 2
Else: Low = (High + Low) / 2
End If
Loop
OTW_IV = (High + Low) / 2
End Select

End Function
