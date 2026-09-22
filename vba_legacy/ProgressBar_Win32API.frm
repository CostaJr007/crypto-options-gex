Attribute VB_Name = "Barra_Progresso"
Attribute VB_Base = "0{75EB18CF-EDA1-4C52-B3F3-B889F84D5C45}{9708F864-7594-447A-8FAD-D99D49A1CD6D}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False

Option Explicit

Private Type RECT
        Left As Long
        Top As Long
        Right As Long
        Bottom As Long
End Type

Const GWL_STYLE = (-16)
Const WS_CAPTION = &HC00000
Const SWP_FRAMECHANGED = &H20

#If Win64 Then
    Private Declare PtrSafe Function FindWindowA Lib "user32" (ByVal lpClassName As String, ByVal lpWindowName As String) As Long
    Private Declare PtrSafe Function GetWindowRect Lib "user32" (ByVal hwnd As Long, lpRect As RECT) As Long
    Private Declare PtrSafe Function GetWindowLong Lib "user32" Alias "GetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long) As Long
    Private Declare PtrSafe Function SetWindowLong Lib "user32" Alias "SetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long, ByVal dwNewLong As Long) As Long
    Private Declare PtrSafe Function SetWindowPos Lib "user32" _
       (ByVal hwnd As Long, _
        ByVal hWndInsertAfter As Long, _
        ByVal X As Long, _
        ByVal Y As Long, _
        ByVal cx As Long, _
        ByVal cy As Long, _
        ByVal wFlags As Long) _
     As LongPtr
#Else
    Private Declare Function FindWindowA Lib "user32" (ByVal lpClassName As String, ByVal lpWindowName As String) As Long
    Private Declare Function GetWindowRect Lib "user32" (ByVal hwnd As Long, lpRect As RECT) As Long
    Private Declare Function GetWindowLong Lib "user32" Alias "GetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long) As Long
    Private Declare Function SetWindowLong Lib "user32" Alias "SetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long, ByVal dwNewLong As Long) As Long
    Private Declare Function SetWindowPos Lib "user32" _
       (ByVal hwnd As Long, _
        ByVal hWndInsertAfter As Long, _
        ByVal X As Long, _
        ByVal Y As Long, _
        ByVal cx As Long, _
        ByVal cy As Long, _
        ByVal wFlags As Long) _
     As Long
#End If

Private Sub UserForm_Activate()
    Me.Aviso.Caption = Sheets("GBM").Range("R1").Value
    Me.lblProcesso.Caption = Sheets("GBM").Range("R2").Value
    Me.FrameProcesso.Caption = "Aviso"
    'Barra_Progresso.lblProcesso.Width = 0
End Sub

Private Sub UserForm_Initialize()
    Retirar_Titulo Me.Caption, False
End Sub

Sub Retirar_Titulo(stCaption As String, sbxVisible As Boolean)
    Dim vrWin As RECT
    Dim style As Long
    Dim lHwnd As Long
    lHwnd = FindWindowA(vbNullString, stCaption)
    GetWindowRect lHwnd, vrWin
    style = GetWindowLong(lHwnd, GWL_STYLE)
    If sbxVisible Then
        SetWindowLong lHwnd, GWL_STYLE, style Or WS_CAPTION
    Else
        SetWindowLong lHwnd, GWL_STYLE, style And Not WS_CAPTION
    End If
    SetWindowPos lHwnd, 0, vrWin.Left, vrWin.Top, vrWin.Right - vrWin.Left, vrWin.Bottom - vrWin.Top, SWP_FRAMECHANGED
End Sub
