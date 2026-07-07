' VBScript para exportar Access 97 (.mdb) a JSON
' Se ejecuta con cscript.exe de 32 bits desde SysWOW64

Dim path, conn, rs, tables, t, fld, i, json, first, f
path = CreateObject("Scripting.FileSystemObject").GetAbsolutePathName("BaseInformes.mdb")

Set conn = CreateObject("ADODB.Connection")
conn.Open("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" & path)

Set rs = conn.OpenSchema(20) ' adSchemaTables
tables = ""
Do While Not rs.EOF
    If rs.Fields("TABLE_TYPE").Value = "TABLE" Then
        tables = tables & rs.Fields("TABLE_NAME").Value & "|"
    End If
    rs.MoveNext
Loop
rs.Close

WScript.Echo "{""tables"":["" & Left(tables, Len(tables)-1) & ""]"

Dim tArr
tArr = Split(Left(tables, Len(tables)-1), "|")

For Each t In tArr
    WScript.Echo ",""" & t & """:{""columns"":["
    Set rs = conn.Execute("SELECT TOP 1 * FROM [" & t & "]")
    first = True
    For i = 0 To rs.Fields.Count - 1
        Set f = rs.Fields(i)
        If Not first Then WScript.Echo "," End If
        WScript.Echo "{""name"":""" & f.Name & """,""type"":" & f.Type & "}"
        first = False
    Next
    WScript.Echo "],""rows"":["
    rs.Close
    
    Set rs = conn.Execute("SELECT * FROM [" & t & "]")
    first = True
    Do While Not rs.EOF
        If Not first Then WScript.Echo "," End If
        WScript.Echo "["
        For i = 0 To rs.Fields.Count - 1
            Set f = rs.Fields(i)
            If i > 0 Then WScript.Echo "," End If
            Dim val
            If IsNull(f.Value) Then
                val = "null"
            Else
                val = Replace(f.Value, "\", "\\")
                val = Replace(val, """", "\""")
                val = """" & val & """"
            End If
            WScript.Echo val
        Next
        WScript.Echo "]"
        first = False
        rs.MoveNext
    Loop
    WScript.Echo "]}}"
    rs.Close
Next

conn.Close
