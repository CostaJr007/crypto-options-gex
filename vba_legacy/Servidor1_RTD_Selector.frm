Attribute VB_Name = "Servidor1"
Attribute VB_Base = "0{56A0017E-D141-4CF2-A843-EB4C6D76D0BA}{AC3A2910-FE34-494A-90D2-5F2D1E51124D}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False

Const Ser As String = "Forward N&S"
Dim Prov As String

Private Sub UserForm_Activate()
    Select Case Sheets(Ser).Range("A1").Value
        
        Case "LINK RTD-PROFITCHART"
            Me.OptionButton2.Value = True
            Me.OptionButton2.SetFocus
            
        Case "LINK RTD-FAST"
            Me.OptionButton4.Value = True
            Me.OptionButton4.SetFocus
        
        Case "***"
            Me.OptionButton3.Value = True
            Me.OptionButton3.SetFocus
            
        Case "RTD-TRYD"
            Me.OptionButton1.Value = True
            Me.OptionButton1.SetFocus
        
    End Select
End Sub

Private Sub CommandButton1_Click()
    If Sheets(Ser).Range("A1").Value <> Prov Then
        Application.Calculation = xlCalculationManual
        Application.EnableEvents = False
        Application.ScreenUpdating = False
        ActiveWorkbook.Unprotect Password:=Sheets("GBM").Range("R3").Value
        Sheets("GBM").Visible = True
        Sheets(Ser).Select
        Sheets(Ser).Unprotect Password:=Sheets("GBM").Range("R3").Value
        Sheets("Forward N&S").Unprotect Password:=Sheets("GBM").Range("R3").Value
        If Sheets("GBM").Range("R4").Value > 0 Then
        Sheets(Ser).Range("A1").Value = Prov
        Unload Me
        End If
        Select Case Sheets(Ser).Range("A1").Value
            
            Case "RTD-TRYD"
                Configurar_RTD_TRYD
            
            Case "LINK RTD-PROFITCHART"
                Configurar_PROFITCHART
                
            Case "LINK RTD-FAST"
                Configurar_RTD_FAST
            
            Case "***"
                Configurar_Limpar
        End Select
        If Sheets(Ser).Range("A1").Value = "***" Then
           Sheets(Ser).Range("B3:F" & ULinha(1, Ser)).ClearContents
            
        Else
            Linha1 = 3
            Do While Linha1 <= ULinha(1, Ser)
                     Linha1 = Linha1 + 1
            Loop
            Bordas
            Sheets(Ser).Range("A1").Select
        End If
        
        Application.ScreenUpdating = True
        Application.EnableEvents = True
        Application.Calculation = xlCalculationAutomatic
    End If
End Sub
Private Sub OptionButton2_Click()
    Prov = "LINK RTD-PROFITCHART"
    If Sheets(Ser).Range("A1").Value <> Prov Then
        MsgBox "O LINK RTD do PROFTCHART só mostrará dados dos ativos que estiverem carregados no painel de RTD/Cotações" & Chr(10) & Chr(10) & "Para configurar o LINK RTD carregue o arquivo .prt atual da planilha", vbInformation, "OBT"
    End If
End Sub

Private Sub OptionButton3_Click()
    Prov = "***"
End Sub

Private Sub OptionButton1_Click()
    Prov = "RTD-TRYD"
End Sub

Private Sub OptionButton4_Click()
    Prov = "LINK RTD-FAST"
End Sub

Sub Bordas()
    Dim Ultima_Linha As Integer
    Ultima_Linha = ULinha(1, Ser)
    If Ultima_Linha < 6 Then
        Ultima_Linha = 6
    End If
    Sheets(Ser).Range("A1:AF" & Ultima_Linha).Select
    Selection.Borders(xlDiagonalDown).LineStyle = xlNone
    Selection.Borders(xlDiagonalUp).LineStyle = xlNone
    With Selection.Borders(xlEdgeLeft)
        .LineStyle = xlDouble
        .ColorIndex = 0
        .TintAndShade = 0
        .Weight = xlThick
    End With
    With Selection.Borders(xlEdgeTop)
        .LineStyle = xlDouble
        .ColorIndex = 0
        .TintAndShade = 0
        .Weight = xlThick
    End With
    With Selection.Borders(xlEdgeBottom)
        .LineStyle = xlDouble
        .ColorIndex = 0
        .TintAndShade = 0
        .Weight = xlThick
    End With
    With Selection.Borders(xlEdgeRight)
        .LineStyle = xlDouble
        .ColorIndex = 0
        .TintAndShade = 0
        .Weight = xlThick
    End With
End Sub


