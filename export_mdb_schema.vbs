Dim path, conn, rs, tables, t, fld, i
path = CreateObject("Scripting.FileSystemObject").GetAbsolutePathName("BaseInformes.mdb")
Set conn = CreateObject("ADODB.Connection")
conn.Open("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" & path)

Set rs = conn.OpenSchema(20)
tables = ""
Do While Not rs.EOF
    If rs.Fields("TABLE_TYPE").Value = "TABLE" Then
        WScript.Echo "TABLE: " & rs.Fields("TABLE_NAME").Value
    End If
    rs.MoveNext
Loop
rs.Close

Set rs = conn.OpenSchema(20)
Do While Not rs.EOF
    If rs.Fields("TABLE_TYPE").Value = "TABLE" Then
        t = rs.Fields("TABLE_NAME").Value
        WScript.Echo vbCrLf & "=== " & t & " ==="
        Set rs2 = conn.Execute("SELECT TOP 1 * FROM [" & t & "]")
        For i = 0 To rs2.Fields.Count - 1
            Set fld = rs2.Fields(i)
            WScript.Echo fld.Name & " | type=" & fld.Type
        Next
        rs2.Close
    End If
    rs.MoveNext
Loop
rs.Close
conn.Close
