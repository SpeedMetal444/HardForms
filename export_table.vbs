Dim conn, rs, fso, out, i, val, table, csvPath, mdbPath
table = WScript.Arguments(0)
csvPath = WScript.Arguments(1)
mdbPath = WScript.Arguments(2)

Set conn = CreateObject("ADODB.Connection")
conn.Open("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" & mdbPath)
Set rs = conn.Execute("SELECT * FROM [" & table & "]")

Set fso = CreateObject("Scripting.FileSystemObject")
Set out = fso.CreateTextFile(csvPath, True, False)

' Header
Dim header
For i = 0 To rs.Fields.Count - 1
    If i > 0 Then out.Write ","
    out.Write """" & rs.Fields(i).Name & """"
Next
out.WriteLine

' Rows
Do While Not rs.EOF
    For i = 0 To rs.Fields.Count - 1
        If i > 0 Then out.Write ","
        val = rs.Fields(i).Value
        If IsNull(val) Then
            out.Write ""
        Else
            val = Replace(CStr(val), """", """""")
            out.Write """" & val & """"
        End If
    Next
    out.WriteLine
    rs.MoveNext
Loop
rs.Close
conn.Close
out.Close
